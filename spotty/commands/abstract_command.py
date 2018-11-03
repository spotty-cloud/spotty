from abc import ABC, abstractmethod
from argparse import Namespace, ArgumentParser
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class AbstractCommand(ABC):
    """Abstract class for implementing a command"""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    def description(self) -> str:
        return ''

    def configure(self, parser: ArgumentParser):
        parser.add_argument('-d', '--debug', action='store_true', help='Show debug messages')

    @abstractmethod
    def run(self, args: Namespace, output: AbstractOutputWriter):
        """Performs a command.

        Args:
            args: arguments provided by argparse.
        Raises:
            ValueError: If command's arguments can't be processed.
        """
        raise NotImplementedError
