from argparse import ArgumentParser, Namespace
import subprocess
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.helpers.ssh import get_ssh_command
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class SshCommand(AbstractConfigCommand):

    name = 'ssh'
    description = 'Connect to the running Docker container or to the instance itself'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-H', '--host-os', action='store_true', help='Connect to the host OS instead of the Docker '
                                                                         'container')
        parser.add_argument('-s', '--session-name', type=str, default=None, help='tmux session name')

    def _run(self, project_dir: str, config: dict, instance_manager: AbstractInstanceManager,
             args: Namespace, output: AbstractOutputWriter):
        if args.host_os:
            # connect to the host OS
            session_name = args.session_name if args.session_name else 'spotty-ssh-host-os'
            remote_cmd = ['tmux', 'new', '-s', session_name, '-A']
        else:
            # connect to the container
            session_name = args.session_name if args.session_name else 'spotty-ssh-container'
            remote_cmd = ['tmux', 'new', '-s', session_name, '-A', 'sudo', '/scripts/container_bash.sh']

        remote_cmd = subprocess.list2cmdline(remote_cmd)

        # connect to the instance
        ssh_command = get_ssh_command(instance_manager.ip_address, instance_manager.ssh_user,
                                      instance_manager.ssh_key_path, remote_cmd,
                                      instance_manager.local_ssh_port)
        subprocess.call(ssh_command)
