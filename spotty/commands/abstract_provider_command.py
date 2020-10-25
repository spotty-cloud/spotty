from abc import abstractmethod
from argparse import Namespace, ArgumentParser
import sys
from spotty.commands.abstract_command import AbstractCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class AbstractProviderCommand(AbstractCommand):
    """Abstract class for a provider sub-command."""

    @property
    @abstractmethod
    def commands(self) -> list:
        """Returns a list of the provider sub-commands."""
        raise NotImplementedError

    def configure(self, parser: ArgumentParser):
        from spotty.cli import add_subparsers
        add_subparsers(parser, self.commands)

    def run(self, args: Namespace, output: AbstractOutputWriter):
        """If the command is called, it just displays a list of available sub-commands."""
        args.parser.print_help()
        sys.exit(1)
