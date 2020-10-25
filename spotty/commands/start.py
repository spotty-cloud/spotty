from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.deployment.abstract_instance_manager import AbstractInstanceManager


class StartCommand(AbstractConfigCommand):

    name = 'start'
    description = 'Start an instance with a container'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-C', '--container', action='store_true', help='Starts or restarts container on the '
                                                                           'running instance')
        parser.add_argument('--dry-run', action='store_true', help='Displays the steps that would be performed '
                                                                   'using the specified command without actually '
                                                                   'running them')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        dry_run = args.dry_run

        if args.container:
            # check that the instance is started
            if not instance_manager.is_running():
                raise InstanceNotRunningError(instance_manager.instance_config.name)

            # start a container on the running instance
            instance_manager.start_container(output, dry_run=dry_run)

            if not dry_run:
                instance_name = ''
                if len(instance_manager.project_config.instances) > 1:
                    instance_name = ' ' + instance_manager.instance_config.name

                output.write('\nContainer was successfully started.\n'
                             'Use the "spotty sh%s" command to connect to the container.\n'
                             % instance_name)
        else:
            # start the instance
            with output.prefix('[dry-run] ' if dry_run else ''):
                instance_manager.start(output, dry_run)

            if not dry_run:
                instance_name = ''
                if len(instance_manager.project_config.instances) > 1:
                    instance_name = ' ' + instance_manager.instance_config.name

                output.write('\n%s\n'
                             '\nUse the "spotty sh%s" command to connect to the container.\n'
                             % (instance_manager.get_status_text(), instance_name))
