from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.helpers.config import get_instance_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.instance_factory import InstanceFactory


class SyncCommand(AbstractConfigCommand):

    name = 'sync'
    description = 'Synchronize the project with the running instance'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('--dry-run', action='store_true', help='Show files to be synced')

    def _run(self, project_dir: str, config: dict, args: Namespace, output: AbstractOutputWriter):
        project_name = config['project']['name']
        sync_filters = config['project']['syncFilters']
        instance_config = get_instance_config(config['instances'], args.instance_name)

        instance = InstanceFactory.get_instance(project_name, instance_config)

        dry_run = args.dry_run
        with output.prefix('[dry-run] ' if dry_run else ''):
            output.write('Syncing the project with the instance...')
            instance.sync(project_dir, sync_filters, output, dry_run)

        output.write('Done')
