from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.errors.nothing_to_do import NothingToDoError
from spotty.deployment.abstract_instance_manager import AbstractInstanceManager


class SyncCommand(AbstractConfigCommand):

    name = 'sync'
    description = 'Synchronize the project with the running instance'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('--dry-run', action='store_true', help='Show files to be synced')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        # check that the instance is started
        if not instance_manager.is_running():
            raise InstanceNotRunningError(instance_manager.instance_config.name)

        dry_run = args.dry_run
        with output.prefix('[dry-run] ' if dry_run else ''):
            try:
                instance_manager.sync(output, dry_run)
            except NothingToDoError as e:
                output.write(str(e))
                return

        output.write('Done')
