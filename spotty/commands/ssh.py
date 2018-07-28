import boto3
import subprocess
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.commands.project_resources.key_pair import KeyPairResource
from spotty.commands.project_resources.stack import StackResource
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class SshCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'ssh'

    def run(self, output: AbstractOutputWriter):
        project_config = self._config['project']
        instance_config = self._config['instance']

        project_name = project_config['name']
        region = instance_config['region']

        cf = boto3.client('cloudformation', region_name=region)

        stack = StackResource(cf, project_name, region)

        # check that the stack exists
        if not stack.stack_exists():
            raise ValueError('Stack "%s" doesn\'t exists.' % stack.name)

        # get instance IP address
        info = stack.get_stack_info()
        ip_address = [row['OutputValue'] for row in info['Outputs'] if row['OutputKey'] == 'InstanceIpAddress'][0]

        # connect to the instance
        host = 'ubuntu@%s' % ip_address
        key_path = KeyPairResource(None, project_name, region).key_path
        subprocess.call(['ssh', '-i', key_path, host])
