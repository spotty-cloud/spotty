from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class StartCommand(AbstractConfigCommand):

    name = 'start'
    description = 'Run spot instance, sync the project and start the Docker container'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('--dry-run', action='store_true', help='Displays the steps that would be performed '
                                                                   'using the specified command without actually '
                                                                   'running them')

    def _run(self, project_dir: str, config: dict, instance_manager: AbstractInstanceManager,
             args: Namespace, output: AbstractOutputWriter):
        sync_filters = config['project']['syncFilters']

        # start the instance
        dry_run = args.dry_run
        with output.prefix('[dry-run] ' if dry_run else ''):
            instance_manager.start(project_dir, sync_filters, output, dry_run)

        if not dry_run:
            output.write('\n' + instance_manager.status_text)
            output.write('\nUse "spotty ssh" command to connect to the Docker container.\n')
