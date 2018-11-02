from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.config import get_instance_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.instance_factory import InstanceFactory


class SyncCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'sync'

    @staticmethod
    def get_description():
        return 'Synchronize the project with the running instance'

    def run(self, output: AbstractOutputWriter):
        project_name = self._config['project']['name']
        sync_filters = self._config['project']['syncFilters']
        instance_config = get_instance_config(self._config['instances'], self._args.instance_name)

        instance = InstanceFactory.get_instance(project_name, instance_config)

        output.write('Syncing the project with the instance...')

        instance.sync(self._project_dir, sync_filters, output)

        output.write('Done')
