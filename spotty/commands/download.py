from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class DownloadCommand(AbstractConfigCommand):

    name = 'download'
    description = 'Download files from the running instance'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-i', '--include', metavar='PATTERN', action='append', type=str, required=True,
                            help='Download all files that matches the specified pattern (see Include Filters '
                                 'for the "aws s3 sync" command). Paths must be relative to your project directory, '
                                 'they cannot be absolute.')
        parser.add_argument('--dry-run', action='store_true', help='Show files to be downloaded')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        filters = [
            {'exclude': ['*']},
            {'include': args.include}
        ]

        dry_run = args.dry_run
        with output.prefix('[dry-run] ' if dry_run else ''):
            instance_manager.download(filters, output, dry_run)

        output.write('Done')
