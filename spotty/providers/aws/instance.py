from collections import OrderedDict
import boto3
import os
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.errors.stack_not_created import StackNotCreatedError
from spotty.providers.aws.helpers.resources import wait_stack_status_changed, get_instance_info
from spotty.providers.aws.helpers.spot_prices import get_current_spot_price
from spotty.providers.aws.helpers.sync import sync_project_with_s3, sync_instance_with_s3
from spotty.providers.aws.project_resources.bucket import BucketResource
from spotty.providers.aws.project_resources.instance_profile_stack import create_or_update_instance_profile
from spotty.providers.aws.project_resources.instance_stack import InstanceStackResource
from spotty.providers.abstract_instance import AbstractInstance
from spotty.providers.aws.project_resources.key_pair import KeyPairResource
from spotty.providers.aws.validation import validate_aws_instance_parameters


class AwsInstance(AbstractInstance):

    def __init__(self, project_name: str, instance_config: dict):
        super().__init__(project_name, instance_config)

        self._instance_params = validate_aws_instance_parameters(self._instance_params)

        self._region = self._instance_params['region']
        self._instance_stack = InstanceStackResource(self._project_name, self._region)

    def is_created(self):
        return self._instance_stack.stack_exists()

    def start(self, project_dir: str, sync_filters: list, container_config: dict, output: AbstractOutputWriter):
        cf = boto3.client('cloudformation', region_name=self._region)
        ec2 = boto3.client('ec2', region_name=self._region)

        availability_zone = self._instance_params['availabilityZone']
        instance_type = self._instance_params['instanceType']
        ami_name = self._instance_params['amiName']
        root_volume_size = self._instance_params['rootVolumeSize']
        docker_data_root = self._instance_params['dockerDataRoot']
        max_price = self._instance_params['maxPrice']
        volumes = self._instance_params['volumes']

        # sync the project with the bucket
        sync_project_with_s3(project_dir, self._project_name, self._region, sync_filters, output)

        # create or update instance profile
        instance_profile_arn = create_or_update_instance_profile(cf, output)

        # prepare CloudFormation template
        output.write('Preparing CloudFormation template...')

        # check availability zone
        if availability_zone:
            zones = ec2.describe_availability_zones()
            zone_names = [zone['ZoneName'] for zone in zones['AvailabilityZones']]
            if availability_zone not in zone_names:
                raise ValueError('Availability zone "%s" doesn\'t exist in the "%s" region.'
                                 % (availability_zone, self._region))

        # prepare CF template
        ports = container_config['ports']
        docker_commands = container_config['commands']

        template = self._instance_stack.prepare_template(ec2, self._project_name, self._instance_name,
                                                         availability_zone, instance_type, volumes, ports,
                                                         max_price, docker_commands)

        # mount directories for the volumes
        mount_dirs = OrderedDict()
        for volume in volumes:
            if volume['parameters']['directory']:
                mount_dir = volume['parameters']['directory']
            else:
                mount_dir = '/mnt/%s-%s-%s' % (self._project_name, volume['name'], self._instance_name)

            mount_dirs[volume['name']] = mount_dir

        output.write('Container volumes:')

        # container volumes mapping
        container_volumes = {}
        for container_mount in container_config['volumeMounts']:
            if container_mount['name'] in mount_dirs:
                container_volumes[mount_dirs[container_mount['name']]] = container_mount['mountPath']
                output.write('  %s -> EBS volume (%s-%s-%s)' % (container_mount['mountPath'], self._project_name,
                                                              container_mount['name'], self._instance_name))
            else:
                tmp_host_dir = '/tmp/spotty/volumes/%s-%s-%s' \
                               % (self._project_name, container_mount['name'], self._instance_name)
                container_volumes[tmp_host_dir] = container_mount['mountPath']
                output.write('  %s -> temporary directory' % container_mount['mountPath'])

        # get project directory
        container_project_dir = container_config['projectDir']
        project_dir = None
        for host_dir, container_dir in container_volumes.items():
            if (container_project_dir + '/').startswith(container_dir + '/'):
                project_subdir = os.path.relpath(container_project_dir, container_dir)
                project_dir = host_dir + '/' + project_subdir
                break

        if not project_dir:
            # use temporary directory for the project
            project_dir = '/tmp/spotty/projects/%s' % self._project_name

            # update container volume mappings
            container_volumes[project_dir] = container_project_dir
            output.write('  %s -> temporary directory' % project_dir)

        # project bucket name
        s3 = boto3.client('s3', region_name=self._region)
        project_bucket = BucketResource(s3, self._project_name, self._region)
        bucket_name = project_bucket.create_bucket(output)

        # create stack
        res = self._instance_stack.create_stack(ec2, template, instance_profile_arn, instance_type, ami_name,
                                                root_volume_size, project_dir, list(mount_dirs.values()),
                                                container_volumes, bucket_name, container_config, docker_data_root)

        output.write('Waiting for the stack to be created...')

        resource_messages = [
            ('SpotInstance', 'launching the instance'),
            ('DockerReadyWaitCondition', 'waiting for the Docker container to be ready'),
        ]

        # wait for the stack to be created
        status, stack_info = wait_stack_status_changed(cf, stack_id=res['StackId'], waiting_status='CREATE_IN_PROGRESS',
                                                       resource_messages=resource_messages,
                                                       resource_success_status='CREATE_COMPLETE', output=output)

        if status != 'CREATE_COMPLETE':
            raise ValueError('Stack "%s" was not created.\n'
                             'Please, see CloudFormation and CloudWatch logs for the details.'
                             % self._instance_stack.name)

    def stop(self, project_name: str, output: AbstractOutputWriter):
        cf = boto3.client('cloudformation', region_name=self._region)

        # get stack ID
        stack_info = self._instance_stack.get_stack_info()
        stack_id = stack_info['StackId']

        # delete the stack
        self._instance_stack.delete_stack()

        output.write('Waiting for the stack to be deleted...')

        resource_messages = [
            ('TerminateInstance', 'terminating the instance'),
            ('_', 'creating snapshots and deleting the volumes'),
        ]

        # wait for the deletion to be completed
        status, stack_info = wait_stack_status_changed(cf, stack_id=stack_id, waiting_status='DELETE_IN_PROGRESS',
                                                       resource_messages=resource_messages,
                                                       resource_success_status='DELETE_COMPLETE', output=output)

        if status != 'DELETE_COMPLETE':
            raise ValueError('Stack "%s" was not deleted.\n'
                             'See CloudFormation and CloudWatch logs for details.' % self._instance_stack.name)

    def sync(self, project_dir: str, sync_filters: list, output: AbstractOutputWriter):
        # sync the project with S3 bucket
        output.write('Syncing the project with S3 bucket...')
        sync_project_with_s3(project_dir, self._project_name, self._region, sync_filters, output)

        # sync S3 with the instance
        output.write('Syncing S3 bucket with the instance...')
        sync_instance_with_s3(self.ip_address, self._project_name, self._region)

    @property
    def status_text(self):
        ec2 = boto3.client('ec2', region_name=self._region)
        instance_info = get_instance_info(ec2, self._instance_stack.name)
        if not instance_info:
            raise StackNotCreatedError()

        state_name = instance_info['State']['Name']
        instance_type = instance_info['InstanceType']
        ip_address = instance_info['PublicIpAddress']
        availability_zone = instance_info['Placement']['AvailabilityZone']
        launch_time_str = instance_info['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S')

        spot_price = get_current_spot_price(ec2, instance_type, availability_zone)

        text = 'Instance State: %s.\n' \
               'Instance Type: %s.\n' \
               'IP Address: %s\n' \
               'Availability Zone: %s\n' \
               'Launch Time: %s\n' \
               'Current Spot Price: $%.04f' % (state_name, instance_type, ip_address, availability_zone,
                                               launch_time_str, spot_price)

        return text

    @property
    def ip_address(self):
        ec2 = boto3.client('ec2', region_name=self._region)
        instance_info = get_instance_info(ec2, self._instance_stack.name)
        if not instance_info:
            raise InstanceNotRunningError()

        return instance_info['PublicIpAddress']

    @property
    def ssh_user(self):
        return 'ubuntu'

    @property
    def ssh_key_path(self):
        return KeyPairResource(self._project_name, self._region).key_path
