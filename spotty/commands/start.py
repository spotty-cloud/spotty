import boto3
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.resources import wait_stack_status_changed, get_instance_ip_address, check_az_and_subnet
from spotty.helpers.spot_prices import get_current_spot_price
from spotty.helpers.sync import sync_project_with_s3
from spotty.helpers.validation import validate_instance_config
from spotty.project_resources.instance_profile_stack import create_or_update_instance_profile
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
        availability_zone = instance_config['availabilityZone']
        subnet_id = instance_config['subnetId']

        cf = boto3.client('cloudformation', region_name=region)
        ec2 = boto3.client('ec2', region_name=region)

        project_name = project_config['name']
        stack = StackResource(cf, project_name, region)

        # check if the stack already exists
        if stack.stack_exists():
            raise ValueError('Stack "%s" already exists.\n'
                             'Use "spotty stop" command to delete the stack.' % stack.name)

        # check availability zone and subnet
        check_az_and_subnet(ec2, availability_zone, subnet_id, region)

        # sync the project with S3
        output.write('Syncing the project with S3...')
        sync_filters = project_config['syncFilters']
        bucket_name = sync_project_with_s3(self._project_dir, project_name, region, sync_filters, output)

        # create or update instance profile
        instance_profile_arn = create_or_update_instance_profile(cf, output)

        # prepare CloudFormation template
        output.write('Preparing CloudFormation template...')

        instance_type = instance_config['instanceType']
        volumes = instance_config['volumes']
        ports = instance_config['ports']
        max_price = instance_config['maxPrice']
        on_demand = instance_config['onDemandInstance']
        docker_commands = instance_config['docker']['commands']

        template = stack.prepare_template(ec2, availability_zone, subnet_id, instance_type, volumes, ports, max_price,
                                          on_demand, docker_commands)

        # create stack
        ami_name = instance_config['amiName']
        root_volume_size = instance_config['rootVolumeSize']
        mount_dirs = [volume['directory'] for volume in volumes]
        docker_config = instance_config['docker']
        remote_project_dir = project_config['remoteDir']

        res = stack.create_stack(ec2, template, instance_profile_arn, instance_type, ami_name, root_volume_size,
                                 mount_dirs, bucket_name, remote_project_dir, project_name, self._project_dir,
                                 docker_config)

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
            output.write('\n'
                         '--------------------\n'
                         'Instance is running.\n'
                         '\n'
                         'IP address: %s' % ip_address)

            if not on_demand:
                # get the current spot price
                availability_zone = [row['OutputValue'] for row in info['Outputs']
                                     if row['OutputKey'] == 'AvailabilityZone'][0]
                current_price = get_current_spot_price(ec2, instance_type, availability_zone)
                output.write('Current Spot price: $%.04f' % current_price)

            output.write('\n'
                         'Use "spotty ssh" command to connect to the Docker container.\n'
                         '--------------------')
        else:
            raise ValueError('Stack "%s" was not created.\n'
                             'Please, see CloudFormation and CloudWatch logs for the details.' % stack.name)
