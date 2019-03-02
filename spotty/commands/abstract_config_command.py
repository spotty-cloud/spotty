from abc import abstractmethod
import yaml
import os
from argparse import Namespace, ArgumentParser
from spotty.config.project_config import ProjectConfig
from spotty.providers.abstract_instance_manager import AbstractInstanceManager
from spotty.providers.instance_manager_factory import InstanceManagerFactory
from spotty.utils import filter_list
from yaml.scanner import ScannerError
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
        # get project directory
        config_path = args.config
        if not config_path:
            config_path = 'spotty.yaml'

        if os.path.isabs(config_path):
            config_abs_path = config_path
        else:
            config_abs_path = os.path.abspath(os.path.join(os.getcwd(), config_path))

        if not os.path.exists(config_abs_path):
            raise ValueError('Configuration file "%s" not found.' % config_path)

        # get project configuration
        project_dir = os.path.dirname(config_abs_path)
        project_config = ProjectConfig(self._load_config(config_abs_path), project_dir)

        # get instance configuration
        instance_config = self._get_instance_config(project_config, args.instance_name, output)

        # create an instance manger
        instance_manager = InstanceManagerFactory.get_instance(project_config, instance_config)

        # run the command
        self._run(instance_manager, args, output)

    @staticmethod
    def _load_config(config_path: str):
        """Returns project configuration."""
        config = None
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                try:
                    config = yaml.safe_load(f)
                except ScannerError as e:
                    raise ValueError(str(e))

        return config

    @staticmethod
    def _get_instance_config(project_config: ProjectConfig, instance_name: str, output: AbstractOutputWriter):
        if not instance_name:
            if len(project_config.instances) > 1:
                # ask user to choose the instance
                output.write('Select the instance:\n')
                with output.prefix('  '):
                    for i, instance_config in enumerate(project_config.instances):
                        output.write('[%d] %s' % (i + 1, instance_config['name']))
                output.write()

                try:
                    num = int(input('Enter number: '))
                    output.write()
                except ValueError:
                    num = 0

                if num < 1 or num > len(project_config.instances):
                    raise ValueError('The value from 1 to %d was expected.' % len(project_config.instances))
            else:
                num = 1

            instance_config = project_config.instances[num - 1]
        else:
            # get the instance by name
            instance_configs = filter_list(project_config.instances, 'name', instance_name)
            if not instance_configs:
                raise ValueError('Instance "%s" not found in the configuration file' % instance_name)

            instance_config = instance_configs[0]

        return instance_config
