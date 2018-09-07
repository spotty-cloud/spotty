import yaml
import os
from argparse import Namespace, ArgumentParser
from yaml.scanner import ScannerError
from spotty.commands.abstract import AbstractCommand


class AbstractConfigCommand(AbstractCommand):

    def __init__(self, args: Namespace):
        super().__init__(args)

        # get project directory
        config_path = self._args.config
        if not config_path:
            config_path = 'spotty.yaml'

        if os.path.isabs(config_path):
            config_abs_path = config_path
        else:
            config_abs_path = os.path.abspath(os.path.join(os.getcwd(), config_path))

        if not os.path.exists(config_abs_path):
            raise ValueError('Configuration file "%s" not found.' % config_path)

        self._project_dir = os.path.dirname(config_abs_path)

        # load project config file
        self._config = self._validate_config(self._load_config(config_abs_path))

    @staticmethod
    def configure(parser: ArgumentParser):
        parser.add_argument('-c', '--config', type=str, default=None, help='Path to the configuration file')

    @staticmethod
    def _validate_config(config):
        return config

    @staticmethod
    def _load_config(config_path: str):
        """Returns project configuration."""
        config = None
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                try:
                    config = yaml.load(f)
                except ScannerError as e:
                    raise ValueError(str(e))

        return config
