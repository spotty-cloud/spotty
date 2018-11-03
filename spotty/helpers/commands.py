from argparse import ArgumentParser


def add_subparsers(parser: ArgumentParser, command_classes: list):
    """Adds commands to the parser."""
    subparsers = parser.add_subparsers()
    for command_class in command_classes:
        command = command_class()
        subparser = subparsers.add_parser(command.name, help=command.description)
        subparser.set_defaults(command=command, parser=subparser)
        command.configure(subparser)
