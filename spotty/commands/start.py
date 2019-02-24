from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class StartCommand(AbstractConfigCommand):

    name = 'start'
    description = 'Run a spot instance, sync the project and start the Docker container'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('--dry-run', action='store_true', help='Displays the steps that would be performed '
                                                                   'using the specified command without actually '
                                                                   'running them')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        # start the instance
        dry_run = args.dry_run
        with output.prefix('[dry-run] ' if dry_run else ''):
            instance_manager.start(output, dry_run)

        if not dry_run:
            instance_name = ''
            if len(instance_manager.project_config.instances) > 1:
                instance_name = ' ' + instance_manager.instance_config.name

            output.write('\nThe instance was successfully started.\n'
                         '\n%s\n'
                         '\nUse the "spotty ssh%s" command to connect to the Docker container.\n'
                         % (instance_manager.status_text, instance_name))
