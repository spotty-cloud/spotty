import boto3
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.resources import get_instance_ip_address
from spotty.helpers.sync import sync_instance_with_s3, sync_project_with_s3
from spotty.helpers.validation import validate_instance_config
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

        output.write('Syncing the project with S3 bucket...')

        # sync the project with S3 bucket
        sync_filters = project_config['syncFilters']
        sync_project_with_s3(self._project_dir, project_name, region, sync_filters, output)

        output.write('Syncing S3 bucket with the instance...')

        # get instance IP address
        stack = StackResource(None, project_name, region)
        ec2 = boto3.client('ec2', region_name=region)
        ip_address = get_instance_ip_address(ec2, stack.name)

        # sync S3 with the instance
        sync_instance_with_s3(ip_address, project_name, region)

        output.write('Done')
