from spotty.commands.abstract_provider_command import AbstractProviderCommand
from spotty.providers.aws.commands.clean_logs import CleanLogsCommand
from spotty.providers.aws.commands.create_ami import CreateAmiCommand
from spotty.providers.aws.commands.delete_ami import DeleteAmiCommand
from spotty.providers.aws.commands.spot_prices import SpotPricesCommand
from spotty.providers.aws.commands.start_container import StartContainerCommand


class AwsCommand(AbstractProviderCommand):

    name = 'aws'
    description = 'AWS commands'
    commands = [
        StartContainerCommand,
        CreateAmiCommand,
        DeleteAmiCommand,
        SpotPricesCommand,
        CleanLogsCommand,
    ]
