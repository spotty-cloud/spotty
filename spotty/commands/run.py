from argparse import ArgumentParser, Namespace
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.helpers.run import parse_parameters, render_script
from spotty.helpers.ssh import run_script
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class RunCommand(AbstractConfigCommand):

    name = 'run'
    description = 'Run a script from the configuration file inside the Docker container'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-s', '--session-name', type=str, default=None, help='tmux session name')
        parser.add_argument('-S', '--sync', action='store_true', help='Sync the project before running the script')
        parser.add_argument('-l', '--logging', action='store_true', help='Log the script outputs to the file')
        parser.add_argument('-r', '--restart', action='store_true',
                            help='Restart the script (kills previous session if it exists)')
        parser.add_argument('script_name', metavar='SCRIPT_NAME', type=str, help='Script name')
        parser.add_argument('-p', '--parameters', metavar='PARAMETER=VALUE', nargs='*', type=str, default=[],
                            help='Script parameters')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        # check that the script exists
        script_name = args.script_name
        scripts = instance_manager.project_config.scripts
        if script_name not in scripts:
            raise ValueError('Script "%s" is not defined in the configuration file.' % script_name)

        # replace script parameters
        params = parse_parameters(args.parameters)
        script_content = render_script(scripts[script_name], params)

        # check that the instance is started
        if not instance_manager.is_running():
            raise InstanceNotRunningError(instance_manager.instance_config.name)

        # sync the project with the instance
        if args.sync:
            instance_manager.sync(output)

        # tmux session name
        session_name = args.session_name if args.session_name else 'spotty-script-%s' % script_name

        # run the script on the instance
        run_script(host=instance_manager.ip_address,
                   port=instance_manager.ssh_port,
                   user=instance_manager.ssh_user,
                   key_path=instance_manager.ssh_key_path,
                   script_name=script_name,
                   script_content=script_content,
                   tmux_session_name=session_name,
                   restart=args.restart,
                   logging=args.logging)
