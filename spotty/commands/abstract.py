from abc import ABC, abstractmethod
from argparse import Namespace, ArgumentParser

from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class AbstractCommand(ABC):
    """Abstract class for implementing a command"""

    def __init__(self, args: Namespace):
        """Command constructor.

        Args:
            args: arguments provided by argparse.
        Raises:
            ValueError: If command's arguments can't be processed.
        """
        self._args = args

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        raise NotImplementedError

    @staticmethod
    def get_description() -> str:
        return ''

    @staticmethod
    def configure(parser: ArgumentParser):
        pass

    @abstractmethod
    def run(self, output: AbstractOutputWriter):
        """Performs a command.

        Raises:
            ValueError: If command's arguments can't be processed.
        """
        raise NotImplementedError
