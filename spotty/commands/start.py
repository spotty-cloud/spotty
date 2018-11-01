from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.config import get_instance_config
from spotty.helpers.validation import validate_instance_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.instance_factory import InstanceFactory


class StartCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'start'

    @staticmethod
    def get_description():
        return 'Run spot instance, sync the project and start the Docker container'

    @staticmethod
    def _validate_config(config):
        return validate_instance_config(config)

    def run(self, output: AbstractOutputWriter):
        project_name = self._config['project']['name']
        sync_filters = self._config['project']['syncFilters']
        container_config = self._config['container']
        instance_config = get_instance_config(self._config['instances'], self._args.instance_name)

        instance = InstanceFactory.get_instance(project_name, instance_config)

        # check if the stack with the instance is already created
        if instance.is_created():
            raise ValueError('Instance "%s" is already started.\n'
                             'Use "spotty stop" command to stop the instance.' % self._args.instance_name)

        # start the instance
        instance.start(self._project_dir, sync_filters, container_config, output)

        output.write('\n'
                     '--------------------\n'
                     '%s\n\n'
                     'Use "spotty ssh" command to connect to the Docker container.\n'
                     '--------------------' % instance.status_text)
