from abc import ABC, abstractmethod
from argparse import Namespace, ArgumentParser
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class AbstractCommand(ABC):
    """Abstract class for a Spotty sub-command."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The sub-command name."""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """The sub-command description. It will be displayed in the help text."""
        return ''

    def configure(self, parser: ArgumentParser):
        """Adds arguments for the sub-command."""
        parser.add_argument('-d', '--debug', action='store_true', help='Show debug messages')

    @abstractmethod
    def run(self, args: Namespace, output: AbstractOutputWriter):
        """Runs the sub-command.

        Args:
            args: Arguments provided by argparse.
            output: Output writer.
        Raises:
            ValueError: If command's arguments can't be processed.
        """
        raise NotImplementedError
