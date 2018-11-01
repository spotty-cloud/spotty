from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.config import get_instance_config
from spotty.helpers.validation import validate_instance_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.instance_factory import InstanceFactory


class StatusCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'status'

    @staticmethod
    def get_description():
        return 'Print information about the instance'

    @staticmethod
    def _validate_config(config):
        return validate_instance_config(config)

    def run(self, output: AbstractOutputWriter):
        project_name = self._config['project']['name']
        instance_config = get_instance_config(self._config['instances'], self._args.instance_name)

        instance = InstanceFactory.get_instance(project_name, instance_config)

        output.write(instance.status_text)
