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
        parser.add_argument('-l', '--list-sessions', action='store_true', help='List all tmux sessions managed by the '
                                                                               'instance')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        if args.list_sessions:
            remote_cmd = ['tmux', 'ls', ';', 'echo', '']
        else:
            # tmux session name
            session_name = args.session_name
            if not session_name:
                session_name = 'spotty-ssh-host-os' if args.host_os else 'spotty-ssh-container'

            # a command to connect to the host OS or to the container
            remote_cmd = ['tmux', 'new', '-s', session_name, '-A']
            if not args.host_os:
                # connect to the container or keep the tmux window in case of a failure
                container_cmd = subprocess.list2cmdline(['sudo', '/tmp/spotty/instance/scripts/container_bash.sh'])
                tmux_cmd = '%s || tmux set remain-on-exit on' % container_cmd
                remote_cmd += [tmux_cmd]

        remote_cmd = subprocess.list2cmdline(remote_cmd)

        # connect to the instance
        ssh_command = get_ssh_command(instance_manager.ip_address, instance_manager.ssh_port,
                                      instance_manager.ssh_user, instance_manager.ssh_key_path, remote_cmd)
        subprocess.call(ssh_command)
