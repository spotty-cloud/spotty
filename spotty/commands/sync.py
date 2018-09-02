import subprocess
import boto3
from spotty.aws_cli import AwsCli
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.resources import get_instance_ip_address
from spotty.helpers.validation import validate_instance_config
from spotty.project_resources.bucket import BucketResource
from spotty.project_resources.key_pair import KeyPairResource
from spotty.project_resources.stack import StackResource
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class SyncCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'sync'

    @staticmethod
    def get_description():
        return 'Synchronize the project with the running instance'

    @staticmethod
    def _validate_config(config):
        return validate_instance_config(config)

    def run(self, output: AbstractOutputWriter):
        project_config = self._config['project']
        instance_config = self._config['instance']

        region = instance_config['region']
        project_name = project_config['name']

        # create bucket for the project
        s3 = boto3.client('s3', region_name=region)
        project_bucket = BucketResource(s3, project_name, region)
        bucket_name = project_bucket.create_bucket(output)

        output.write('Syncing the project with S3 bucket...')

        # sync the project with S3
        project_filters = project_config['syncFilters']
        AwsCli(region=region).s3_sync(self._project_dir, 's3://%s/project' % bucket_name, delete=True,
                                      filters=project_filters, capture_output=False)

        # get instance IP address
        stack = StackResource(None, project_name, region)
        ec2 = boto3.client('ec2', region_name=region)
        ip_address = get_instance_ip_address(ec2, stack.name)

        output.write('Syncing S3 bucket with the instance...')

        # sync S3 with the instance
        remote_cmd = subprocess.list2cmdline(['sudo', '-i', '/bin/bash', '-e', '/tmp/scripts/sync_project.sh',
                                              '>', '/dev/null'])

        # connect to the instance and run remote command
        host = 'ubuntu@%s' % ip_address
        key_path = KeyPairResource(None, project_name, region).key_path
        ssh_command = ['ssh', '-i', key_path, '-o', 'StrictHostKeyChecking no', '-tq', host, remote_cmd]

        subprocess.call(ssh_command)

        output.write('Done')
