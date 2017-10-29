from abc import ABC, abstractmethod
from argparse import Namespace
from cloud_training import configure


class AbstractCommand(ABC):
    def __init__(self, args: Namespace):
        self._args = args
        self._settings = configure.get_all_settings(self._args.profile)

    @abstractmethod
    def run(self) -> bool:
        return True
