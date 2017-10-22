import json
import os
from abc import ABC, abstractmethod
from argparse import Namespace


class AbstractCommand(ABC):
    def __init__(self, args: Namespace):
        self._region = args.region
        self._project_dir = os.path.abspath(os.path.join(os.getcwd(), args.project_dir))
        self._args = args

        # read a project config
        config = {}
        config_file = os.path.join(self._project_dir, 'cloud_training.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)

        self._config = config

    @abstractmethod
    def run(self):
        return

    def check(self) -> bool:
        return True