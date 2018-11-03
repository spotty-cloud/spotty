from abc import abstractmethod
from argparse import Namespace, ArgumentParser
import sys
from spotty.commands.abstract_command import AbstractCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.helpers.commands import add_subparsers


class AbstractProviderCommand(AbstractCommand):
    """Abstract class for implementing a provider command."""

    @property
    @abstractmethod
    def commands(self):
        raise NotImplementedError

    def configure(self, parser: ArgumentParser):
        add_subparsers(parser, self.commands)

    def run(self, args: Namespace, output: AbstractOutputWriter):
        args.parser.print_help()
        sys.exit(1)
