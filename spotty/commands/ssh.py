from argparse import ArgumentParser
import subprocess
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.config import get_instance_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.instance_factory import InstanceFactory


class SshCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'ssh'

    @staticmethod
    def get_description():
        return 'Connect to the running Docker container or to the instance itself'

    @staticmethod
    def configure(parser: ArgumentParser):
        AbstractConfigCommand.configure(parser)
        parser.add_argument('--host-os', '-o', action='store_true', help='Connect to the host OS instead of the Docker '
                                                                         'container')
        parser.add_argument('--session-name', '-s', type=str, default=None, help='tmux session name')

    def run(self, output: AbstractOutputWriter):
        project_name = self._config['project']['name']
        instance_config = get_instance_config(self._config['instances'], self._args.instance_name)

        instance = InstanceFactory.get_instance(project_name, instance_config)

        # connect to the instance
        host = '%s@%s' % (instance.ssh_user, instance.ip_address)
        ssh_command = ['ssh', '-i', instance.ssh_key_path, '-o', 'StrictHostKeyChecking no', '-t', host]

        if self._args.host_os:
            session_name = self._args.session_name if self._args.session_name else 'spotty-ssh-host-os'
            ssh_command += ['tmux', 'new', '-s', session_name, '-A']
        else:
            session_name = self._args.session_name if self._args.session_name else 'spotty-ssh-container'
            ssh_command += ['tmux', 'new', '-s', session_name, '-A', 'sudo', '/scripts/container_bash.sh']

        subprocess.call(ssh_command)
