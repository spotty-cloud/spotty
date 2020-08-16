from argparse import ArgumentParser, Namespace
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.utils.commands import get_script_command, get_log_command, get_tmux_session_command, get_bash_command
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.errors.nothing_to_do import NothingToDoError
from spotty.deployment.utils.user_scripts import parse_script_parameters, render_script
from spotty.deployment.abstract_instance_manager import AbstractInstanceManager


class RunCommand(AbstractConfigCommand):

    name = 'run'
    description = 'Run a custom script from the configuration file inside the container'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('script_name', metavar='SCRIPT_NAME', type=str, help='Script name')
        parser.add_argument('-u', '--user', type=str, default=None,
                            help='Container username or UID (format: <name|uid>[:<group|gid>])')
        parser.add_argument('-s', '--session-name', type=str, default=None, help='tmux session name')
        parser.add_argument('-l', '--logging', action='store_true', help='Log the script outputs to a file')
        parser.add_argument('-p', '--parameter', metavar='PARAMETER=VALUE', action='append', type=str, default=[],
                            help='Set a value for the script parameter (format: PARAMETER=VALUE). This '
                                 'argument can be used multiple times to set several parameters. Parameters can be '
                                 'used in the script as Mustache variables (for example: {{PARAMETER}}).')
        parser.add_argument('--no-sync', action='store_true', help='Don\'t sync the project before running the script')

        # add the "double-dash" argument to the usage message
        parser.prog = 'spotty run'
        parser.usage = parser.format_usage()[7:-1] + ' [-- args...]\n'
        parser.epilog = 'The double dash (--) separates custom arguments that you can pass to the script ' \
                        'from the Spotty arguments.'

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        # check that the script exists
        script_name = args.script_name
        scripts = instance_manager.project_config.scripts
        if script_name not in scripts:
            raise ValueError('Script "%s" is not defined in the configuration file.' % script_name)

        # replace script parameters
        params = parse_script_parameters(args.parameter)
        script_content = render_script(scripts[script_name], params)

        # check that the instance is started
        if not instance_manager.is_running():
            raise InstanceNotRunningError(instance_manager.instance_config.name)

        # sync the project with the instance
        if not args.no_sync:
            try:
                instance_manager.sync(output)
            except NothingToDoError:
                pass

        # get a command to run the script with "docker exec"
        script_command = get_script_command(script_name, script_content, script_args=args.custom_args,
                                            logging=args.logging)
        command = instance_manager.container_commands.exec(script_command, interactive=True, tty=True,
                                                           user=args.user)

        # wrap the command with the tmux session
        if instance_manager.use_tmux:
            session_name = args.session_name if args.session_name else 'spotty-script-%s' % script_name
            default_command = instance_manager.container_commands.exec(get_bash_command(), interactive=True, tty=True,
                                                                       user=args.user)
            command = get_tmux_session_command(command, session_name, script_name, default_command=default_command,
                                               keep_pane=True)

        # execute command on the host OS
        instance_manager.exec(command)
