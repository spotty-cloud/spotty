from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.config import get_instance_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.instance_factory import InstanceFactory


class StopCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'stop'

    @staticmethod
    def get_description():
        return 'Terminate running instance and delete its stack'

    def run(self, output: AbstractOutputWriter):
        project_name = self._config['project']['name']
        instance_config = get_instance_config(self._config['instances'], self._args.instance_name)

        instance = InstanceFactory.get_instance(project_name, instance_config)

        # check that the stack with the instance is created
        if not instance.is_created():
            raise ValueError('Instance "%s" is not started.' % self._args.instance_name)

        instance.stop(project_name, output)

        output.write('\n'
                     '--------------------\n'
                     'Instance was successfully deleted.\n'
                     '--------------------')
