from argparse import Namespace
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.helpers.config import get_instance_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.instance_factory import InstanceFactory


class StopCommand(AbstractConfigCommand):

    name = 'stop'
    description = 'Terminate running instance and delete its stack'

    def _run(self, project_dir: str, config: dict, args: Namespace, output: AbstractOutputWriter):
        project_name = config['project']['name']
        instance_config = get_instance_config(config['instances'], args.instance_name)

        instance = InstanceFactory.get_instance(project_name, instance_config)

        # check that the stack with the instance is created
        if not instance.is_created():
            raise ValueError('Instance "%s" is not started.' % args.instance_name)

        instance.stop(project_name, output)

        output.write('\n'
                     '--------------------\n'
                     'Instance was successfully deleted.\n'
                     '--------------------')
