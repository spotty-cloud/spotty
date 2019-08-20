from spotty.commands.abstract_provider_command import AbstractProviderCommand
from spotty.providers.gcp.commands.create_image import CreateImageCommand
from spotty.providers.gcp.commands.delete_image import DeleteImageCommand


class GcpCommand(AbstractProviderCommand):

    name = 'gcp'
    description = 'GCP commands'
    commands = [
        CreateImageCommand,
        DeleteImageCommand,
    ]
