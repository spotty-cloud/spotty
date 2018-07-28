from argparse import ArgumentParser
import boto3
from spotty.aws_cli import AwsCli
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.commands.helpers.resources import wait_for_status_changed
from spotty.commands.helpers.validation import validate_instance_config
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

        # create bucket for the project
        project_bucket = BucketResource(s3, project_name, region)
        bucket_name = project_bucket.create_bucket(output)

        output.write('Syncing the project with S3...')

        # sync the project with S3
        project_filters = project_config['syncFilters']
        AwsCli(region=region).s3_sync(self._project_dir, 's3://%s' % bucket_name, delete=True,
                                      filters=project_filters)

        output.write('Preparing CloudFormation template...')

        # prepare CloudFormation template
        ami_name = instance_config['amiName']
        volume = instance_config['volumes'][0]
        snapshot_name = volume['snapshotName']
        volume_size = volume['size']
        delete_volume = volume['deleteOnTermination']
        ports = instance_config['ports']
        template = stack.prepare_template(ec2, snapshot_name, volume_size, delete_volume, ports, output)

        # create stack
        instance_type = instance_config['instanceType']
        mount_dir = volume['directory']
        docker_config = instance_config['docker']
        remote_project_dir = project_config['remoteDir']
        res = stack.create_stack(ec2, template, instance_type, ami_name, mount_dir, bucket_name, remote_project_dir,
                                 docker_config)

        output.write('Waiting for the stack to be created...')

        # wait for the stack to be created
        status, info = wait_for_status_changed(cf, stack_id=res['StackId'], waiting_status='CREATE_IN_PROGRESS',
                                               output=output)

        if status == 'CREATE_COMPLETE':
            log_group = [row['OutputValue'] for row in info['Outputs'] if row['OutputKey'] == 'InstanceLogGroup'][0]

            output.write('\n'
                         '--------------------\n'
                         'Instance is running.\n'
                         'CloudWatch Log Group: %s.\n'
                         '\n'
                         'Use "spotty ssh" command to connect to the instance.\n'
                         '--------------------' % log_group)
        else:
            raise ValueError('Stack "%s" was not created.\n'
                             'Please, see CloudFormation and CloudWatch logs for the details.' % stack.name)