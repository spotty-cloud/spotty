import argparse
from typing import List, Type
import pkg_resources
from spotty.commands.abstract_command import AbstractCommand
from spotty.commands.aws import AwsCommand
from spotty.commands.download import DownloadCommand
from spotty.commands.exec import ExecCommand
from spotty.commands.run import RunCommand
from spotty.commands.sh import ShCommand
from spotty.commands.start import StartCommand
from spotty.commands.status import StatusCommand
from spotty.commands.stop import StopCommand
from spotty.commands.sync import SyncCommand


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('-V', '--version', action='store_true', help='Display the version of the Spotty')

    command_classes = [
       StartCommand,
       StopCommand,
       StatusCommand,
       ShCommand,
       RunCommand,
       ExecCommand,
       SyncCommand,
       DownloadCommand,
       AwsCommand,
    ] + _get_custom_commands()

    # add commands to the parser
    add_subparsers(parser, command_classes)

    return parser


def add_subparsers(parser: argparse.ArgumentParser, command_classes: List[Type[AbstractCommand]]):
    """Adds commands to the parser."""
    subparsers = parser.add_subparsers()
    for command_class in command_classes:
        command = command_class()
        subparser = subparsers.add_parser(command.name, help=command.description, description=command.description)
        subparser.set_defaults(command=command, parser=subparser)
        command.configure(subparser)


def _get_custom_commands() -> List[Type[AbstractCommand]]:
    """Returns custom commands that integrated through entry points."""
    return [entry_point.load() for entry_point in pkg_resources.iter_entry_points('spotty.commands')]
