from argparse import ArgumentParser
import pkg_resources


def add_subparsers(parser: ArgumentParser, command_classes: list):
    """Adds commands to the parser."""
    subparsers = parser.add_subparsers()
    for command_class in command_classes:
        command = command_class()
        subparser = subparsers.add_parser(command.name, help=command.description)
        subparser.set_defaults(command=command, parser=subparser)
        command.configure(subparser)


def get_custom_commands():
    """Returns custom commands that integrated through entry points."""
    return [entry_point.load() for entry_point in pkg_resources.iter_entry_points('spotty.commands')]
