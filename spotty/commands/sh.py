from argparse import ArgumentParser, Namespace
import subprocess
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.docker_commands import get_bash_cmd
from spotty.deployment.tmux_commands import get_session_cmd
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class ShCommand(AbstractConfigCommand):

    name = 'sh'
    description = 'Get a shell to the Docker container or to the instance itself'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-H', '--host-os', action='store_true', help='Connect to the host OS instead of the Docker '
                                                                         'container')
        parser.add_argument('-s', '--session-name', type=str, default=None, help='tmux session name')
        parser.add_argument('-l', '--list-sessions', action='store_true', help='List all tmux sessions managed by the '
                                                                               'instance')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        if args.list_sessions:
            if not instance_manager.use_tmux:
                raise ValueError('The "%s" provider doesn\'t support tmux.'
                                 % instance_manager.instance_config.provider_name)

            # a command to list existing tmux session on the host OS
            command = ['tmux', 'ls', ';', 'echo', '']
        else:
            if args.host_os:
                # get a command to open a login shell on the host OS
                session_name = args.session_name if args.session_name else 'spotty-sh-host'
                command = get_session_cmd([], session_name, keep_pane=False) if instance_manager.use_tmux else []
            else:
                # get a command to run bash inside the docker container
                command = get_bash_cmd(
                    container_name=instance_manager.instance_config.full_container_name,
                    working_dir=instance_manager.instance_config.container_config.working_dir,
                )

                # wrap the command with the tmux session
                if instance_manager.use_tmux:
                    session_name = args.session_name if args.session_name else 'spotty-sh-container'
                    command = get_session_cmd(command, session_name, default_command=subprocess.list2cmdline(command),
                                              keep_pane=False)

        # execute command on the host OS
        instance_manager.exec(command)
