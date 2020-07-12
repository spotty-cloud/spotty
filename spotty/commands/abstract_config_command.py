from abc import abstractmethod
from typing import List
from argparse import Namespace, ArgumentParser
from spotty.config.config_utils import load_config
from spotty.deployment.abstract_instance_manager import AbstractInstanceManager
from spotty.providers.instance_manager_factory import InstanceManagerFactory
from spotty.commands.abstract_command import AbstractCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class AbstractConfigCommand(AbstractCommand):
    """Abstract class for a Spotty sub-command that needs to use a project's configuration."""

    @abstractmethod
    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        raise NotImplementedError

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-c', '--config', type=str, default=None, help='Path to the configuration file')
        parser.add_argument('instance_name', metavar='INSTANCE_NAME', nargs='?', type=str, help='Instance name')

    def run(self, args: Namespace, output: AbstractOutputWriter):
        # get project configuration
        project_config = load_config(args.config)

        # get instance configuration
        instance_id = self._get_instance_id(project_config.instances, args.instance_name, output)
        instance_config = project_config.instances[instance_id]

        # create an instance manger
        instance_manager = InstanceManagerFactory.get_instance(project_config, instance_config)

        # run the command
        self._run(instance_manager, args, output)

    @staticmethod
    def _get_instance_id(instances: List[dict], instance_name: str, output: AbstractOutputWriter):
        if not instance_name:
            if len(instances) > 1:
                # ask user to choose the instance
                output.write('Select the instance:\n')
                with output.prefix('  '):
                    for i, instance_config in enumerate(instances):
                        output.write('[%d] %s' % (i + 1, instance_config['name']))
                output.write()

                try:
                    num = int(input('Enter number: '))
                    output.write()
                except ValueError:
                    num = 0

                if num < 1 or num > len(instances):
                    raise ValueError('The value from 1 to %d was expected.' % len(instances))

                instance_id = num - 1
            else:
                instance_id = 0
        else:
            # get instance ID by name
            instance_ids = [i for i, instance in enumerate(instances) if instance['name'] == instance_name]
            if not instance_ids:
                raise ValueError('Instance "%s" not found in the configuration file' % instance_name)

            instance_id = instance_ids[0]

        return instance_id
