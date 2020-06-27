import time
from argparse import ArgumentParser, Namespace
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.commands import get_script_command, get_log_command, get_tmux_session_command, get_bash_command
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.errors.nothing_to_do import NothingToDoError
from spotty.helpers.run import parse_parameters, render_script
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class RunCommand(AbstractConfigCommand):

    name = 'run'
    description = 'Run a script from the configuration file inside the Docker container'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('script_name', metavar='SCRIPT_NAME', type=str, help='Script name')
        parser.add_argument('-s', '--session-name', type=str, default=None, help='tmux session name')
        parser.add_argument('-l', '--logging', action='store_true', help='Log the script outputs to the file')
        parser.add_argument('-p', '--parameter', metavar='PARAMETER=VALUE', action='append', type=str, default=[],
                            help='Set the value for a script parameter (you can use this argument multiple times '
                                 'to set several parameters)')
        parser.add_argument('--no-sync', action='store_true', help='Don\'t sync the project before running the script')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        # check that the script exists
        script_name = args.script_name
        scripts = instance_manager.project_config.scripts
        if script_name not in scripts:
            raise ValueError('Script "%s" is not defined in the configuration file.' % script_name)

        # replace script parameters
        params = parse_parameters(args.parameter)
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
        script_command = get_script_command(script_name, script_content, script_args=args.custom_args)
        command = instance_manager.container_commands.exec(script_command)

        # wrap the command with logging
        if args.logging:
            log_file_path = instance_manager.instance_config.host_logs_dir + '/run/%s-%d.log' \
                            % (script_name, time.time())
            command = get_log_command(command, log_file_path)

        # wrap the command with the tmux session
        if instance_manager.use_tmux:
            session_name = args.session_name if args.session_name else 'spotty-script-%s' % script_name
            default_command = instance_manager.container_commands.exec(get_bash_command())
            command = get_tmux_session_command(command, session_name, script_name, default_command=default_command,
                                               keep_pane=True)

        # execute command on the host OS
        instance_manager.exec(command)
