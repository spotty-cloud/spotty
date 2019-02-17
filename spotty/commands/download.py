from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class DownloadCommand(AbstractConfigCommand):

    name = 'download'
    description = 'Download files from the running instance'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-f', '--filters', metavar='FILTER', nargs='+', type=str, required=True,
                            help='AWS S3 Sync "include" filters')
        parser.add_argument('--dry-run', action='store_true', help='Show files to be downloaded')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        filters = [
            {'exclude': ['*']},
            {'include': args.filters}
        ]

        dry_run = args.dry_run
        with output.prefix('[dry-run] ' if dry_run else ''):
            instance_manager.download(filters, output, dry_run)

        output.write('Done')
