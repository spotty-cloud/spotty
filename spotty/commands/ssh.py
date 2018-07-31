from argparse import ArgumentParser
import boto3
import subprocess
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.commands.helpers.validation import validate_instance_config
from spotty.commands.project_resources.key_pair import KeyPairResource
from spotty.commands.project_resources.stack import StackResource
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class SshCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'ssh'

    @staticmethod
    def get_description():
        return 'Connect to the running Docker container or to the instance itself'

    @staticmethod
    def _validate_config(config):
        return validate_instance_config(config)

    @staticmethod
    def configure(parser: ArgumentParser):
        AbstractConfigCommand.configure(parser)
        parser.add_argument('--host-os', '-o', action='store_true', help='Connect to the host OS instead of the Docker '
                                                                         'container')
        parser.add_argument('--session-name', '-s', type=str, default=None, help='tmux session name')

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
        ssh_command = ['ssh', '-i', key_path, '-o', 'StrictHostKeyChecking no', '-t', host]

        if self._args.host_os:
            session_name = self._args.session_name if self._args.session_name else 'spotty-ssh-host-os'
            ssh_command += ['tmux', 'new', '-s', session_name, '-A']
        else:
            working_dir = instance_config['docker']['workingDir']
            session_name = self._args.session_name if self._args.session_name else 'spotty-ssh-container'
            ssh_command += ['tmux', 'new', '-s', session_name, '-A',
                            'sudo', 'docker', 'exec', '-it', '-w', working_dir, 'spotty', '/bin/bash']

        subprocess.call(ssh_command)
