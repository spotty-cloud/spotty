import boto3
from spotty.aws_cli import AwsCli
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.resources import wait_stack_status_changed, get_default_subnet_ids, get_subnet, \
    get_instance_ip_address
from spotty.helpers.spot_prices import get_current_spot_price
from spotty.helpers.validation import validate_instance_config
from spotty.project_resources.bucket import BucketResource
from spotty.project_resources.instance_profile import create_or_update_instance_profile
from spotty.project_resources.stack import StackResource
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class StartCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'start'

    @staticmethod
    def get_description():
        return 'Run spot instance, sync the project and start the Docker container'

    @staticmethod
    def _validate_config(config):
        return validate_instance_config(config)

    def run(self, output: AbstractOutputWriter):
        project_config = self._config['project']
        instance_config = self._config['instance']

        region = instance_config['region']
        cf = boto3.client('cloudformation', region_name=region)
        ec2 = boto3.client('ec2', region_name=region)
        s3 = boto3.client('s3', region_name=region)

        project_name = project_config['name']
        stack = StackResource(cf, project_name, region)

        # check if the stack already exists
        if stack.stack_exists():
            raise ValueError('Stack "%s" already exists.\n'
                             'Use "spotty stop" command to delete the stack.' % stack.name)

        # get all availability zones for the region
        zones = ec2.describe_availability_zones()
        zone_names = [zone['ZoneName'] for zone in zones['AvailabilityZones']]

        # check availability zone
        availability_zone = instance_config['availabilityZone']
        if availability_zone and availability_zone not in zone_names:
            raise ValueError('Availability zone "%s" doesn\'t exist in the "%s" region.'
                             % (availability_zone, region))

        subnet_id = instance_config['subnetId']
        if availability_zone:
            if subnet_id:
                subnet = get_subnet(ec2, subnet_id)
                if not subnet:
                    raise ValueError('Subnet "%s" not found.' % subnet_id)

                if subnet['AvailabilityZone'] != availability_zone:
                    raise ValueError('Availability zone of the subnet doesn\'t match the specified availability zone')
            else:
                default_subnets = get_default_subnet_ids(ec2)
                if availability_zone not in default_subnets:
                    raise ValueError('Default subnet for the "%s" availability zone not found.\n'
                                     'Use the "subnetId" parameter to specify a subnet for this availability zone.'
                                     % availability_zone)
        else:
            if subnet_id:
                raise ValueError('Availability zone should be specified if a custom subnet is specified.')
            else:
                default_subnets = get_default_subnet_ids(ec2)
                zones_wo_subnet = [zone_name for zone_name in zone_names if zone_name not in default_subnets]
                if zones_wo_subnet:
                    raise ValueError('Default subnets for the following availability zones were not found: %s.\n'
                                     'Consider to use the "subnetId" parameter or create missing default subnets.'
                                     % ', '.join(zones_wo_subnet))

        # create bucket for the project
        project_bucket = BucketResource(s3, project_name, region)
        bucket_name = project_bucket.create_bucket(output)

        # sync the project with S3
        output.write('Syncing the project with S3...')

        project_filters = project_config['syncFilters']
        AwsCli(region=region).s3_sync(self._project_dir, 's3://%s/project' % bucket_name, delete=True,
                                      filters=project_filters, capture_output=False)

        # create or update instance profile
        instance_profile_arn = create_or_update_instance_profile(cf, output)

        # prepare CloudFormation template
        output.write('Preparing CloudFormation template...')

        instance_type = instance_config['instanceType']
        volumes = instance_config['volumes']
        ports = instance_config['ports']
        max_price = instance_config['maxPrice']
        docker_commands = instance_config['docker']['commands']

        template = stack.prepare_template(ec2, availability_zone, subnet_id, instance_type, volumes, ports, max_price,
                                          docker_commands)

        # create stack
        ami_name = instance_config['amiName']
        root_volume_size = instance_config['rootVolumeSize']
        mount_dirs = [volume['directory'] for volume in volumes]
        docker_config = instance_config['docker']
        remote_project_dir = project_config['remoteDir']

        res = stack.create_stack(ec2, template, instance_profile_arn, instance_type, ami_name, root_volume_size,
                                 mount_dirs, bucket_name, remote_project_dir, self._project_dir, docker_config)

        output.write('Waiting for the stack to be created...')

        resource_messages = [
            ('SpotInstance', 'launching the instance'),
            ('DockerReadyWaitCondition', 'waiting for the Docker container to be ready'),
        ]

        # wait for the stack to be created
        status, info = wait_stack_status_changed(cf, stack_id=res['StackId'], waiting_status='CREATE_IN_PROGRESS',
                                                 resource_messages=resource_messages,
                                                 resource_success_status='CREATE_COMPLETE', output=output)

        if status == 'CREATE_COMPLETE':
            ip_address = get_instance_ip_address(ec2, stack.name)
            availability_zone = [row['OutputValue'] for row in info['Outputs']
                                 if row['OutputKey'] == 'AvailabilityZone'][0]

            # get the current spot price
            current_price = get_current_spot_price(ec2, instance_type, availability_zone)

            output.write('\n'
                         '--------------------\n'
                         'Instance is running.\n'
                         '\n'
                         'IP address: %s\n'
                         'Current Spot price: $%.04f\n'
                         '\n'
                         'Use "spotty ssh" command to connect to the Docker container.\n'
                         '--------------------' % (ip_address, current_price))
        else:
            raise ValueError('Stack "%s" was not created.\n'
                             'Please, see CloudFormation and CloudWatch logs for the details.' % stack.name)
