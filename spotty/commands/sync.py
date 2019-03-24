from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class SyncCommand(AbstractConfigCommand):

    name = 'sync'
    description = 'Synchronize the project with the running instance'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('--dry-run', action='store_true', help='Show files to be synced')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        dry_run = args.dry_run
        with output.prefix('[dry-run] ' if dry_run else ''):
            instance_manager.sync(output, dry_run)

        output.write('Done')
