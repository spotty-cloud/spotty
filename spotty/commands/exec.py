import sys
from argparse import ArgumentParser, Namespace
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.utils.cli import shlex_join
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.errors.nothing_to_do import NothingToDoError
from spotty.deployment.abstract_instance_manager import AbstractInstanceManager


class ExecCommand(AbstractConfigCommand):

    name = 'exec'
    description = 'Execute a command in the container'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-i', '--interactive', action='store_true', help='Pass STDIN to the container')
        parser.add_argument('-t', '--tty', action='store_true', help='Allocate a pseudo-TTY')
        parser.add_argument('-u', '--user', type=str, default=None,
                            help='Container username or UID (format: <name|uid>[:<group|gid>])')
        parser.add_argument('--no-sync', action='store_true', help='Don\'t sync the project before running the script')

        # add the "double-dash" argument to the usage message
        parser.prog = 'spotty exec'
        parser.usage = parser.format_usage()[7:-1] + ' -- COMMAND [args...]\n'
        parser.epilog = 'The double dash (--) separates the command that you want to execute inside the container ' \
                        'from the Spotty arguments.'

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        # check that the command is provided
        if not args.custom_args:
            raise ValueError('Use the double-dash ("--") to split Spotty arguments from the command that should be '
                             'executed inside the container.')

        # check that the instance is started
        if not instance_manager.is_running():
            raise InstanceNotRunningError(instance_manager.instance_config.name)

        # sync the project with the instance
        if not args.no_sync:
            try:
                instance_manager.sync(output)
            except NothingToDoError:
                pass

        # generate a "docker exec" command
        command = shlex_join(args.custom_args)
        command = instance_manager.container_commands.exec(command, interactive=args.interactive, tty=args.tty,
                                                           user=args.user)

        # execute the command on the host OS
        exit_code = instance_manager.exec(command, tty=args.tty)
        sys.exit(exit_code)
