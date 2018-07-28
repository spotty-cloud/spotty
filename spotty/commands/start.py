from argparse import ArgumentParser
import boto3
from spotty.aws_cli import AwsCli
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.commands.helpers.resources import wait_for_status_changed
from spotty.commands.project_resources.bucket import BucketResource
from spotty.commands.project_resources.stack import StackResource
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class StartCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'start'

    @staticmethod
    def configure(parser: ArgumentParser):
        AbstractConfigCommand.configure(parser)
        parser.add_argument('script-name', metavar='SCRIPT_NAME', type=str, default='', nargs='?', help='Script name')

    def run(self, output: AbstractOutputWriter):
        if 'project' not in self._config:
            raise ValueError('Project configuration is not provided')

        if 'instance' not in self._config:
            raise ValueError('Instance configuration is not provided')

        project_config = self._config['project']
        instance_config = self._config['instance']

        project_name = project_config['name']
        project_filters = project_config.get('syncFilters', [])
        remote_project_dir = project_config['remoteDir']
        region = instance_config['region']
        instance_type = instance_config['instanceType']
        ami_name = instance_config['amiName']
        volume = instance_config['volumes'][0]

        cf = boto3.client('cloudformation', region_name=region)
        ec2 = boto3.client('ec2', region_name=region)
        s3 = boto3.client('s3', region_name=region)

        stack = StackResource(cf, project_name, region)

        # check if the stack already exists
        if stack.stack_exists():
            raise ValueError('Stack "%s" already exists.\n'
                             'Use "spotty stop" command to delete the stack.' % stack.name)

        # create bucket for the project
        project_bucket = BucketResource(s3, project_name, region)
        bucket_name = project_bucket.create_bucket(output)

        output.write('Syncing the project with S3...')

        # sync the project with S3
        AwsCli(region=region).s3_sync(self._project_dir, 's3://%s' % bucket_name, delete=True,
                                      filters=project_filters)

        output.write('Preparing CloudFormation template...')

        # prepare CloudFormation template
        snapshot_name = volume['snapshotName']
        volume_size = int(volume.get('size', 0))
        delete_volume = volume.get('deleteOnTermination', False)
        ports = instance_config.get('ports', [])
        template = stack.prepare_template(ec2, snapshot_name, volume_size, delete_volume, ports, output)

        # create stack
        mount_dir = volume.get('directory', '')
        docker_config = instance_config.get('docker', {})
        res = stack.create_stack(ec2, template, instance_type, ami_name, mount_dir, bucket_name, remote_project_dir,
                                 docker_config)

        output.write('Waiting for the stack to be created...')

        # wait for the stack to be created
        status, info = wait_for_status_changed(cf, stack_id=res['StackId'], waiting_status='CREATE_IN_PROGRESS',
                                               output=output)

        if status == 'CREATE_COMPLETE':
            #ip_address = [row['OutputValue'] for row in info['Outputs'] if row['OutputKey'] == 'InstanceIpAddress'][0]
            output.write('Instance is running.' % stack.name)
            output.write('Use "spotty ssh" command to connect to the instance.')
            #output.write('IP address of the instance: %s' % ip_address)
        else:
            raise ValueError('Stack "%s" was not created.\n'
                             'Please, see CloudFormation and CloudWatch logs for the details.' % stack.name)
