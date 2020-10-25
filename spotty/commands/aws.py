from spotty.commands.abstract_provider_command import AbstractProviderCommand
from spotty.providers.aws.commands.clean_logs import CleanLogsCommand
from spotty.providers.aws.commands.spot_prices import SpotPricesCommand


class AwsCommand(AbstractProviderCommand):

    name = 'aws'
    description = 'AWS commands'
    commands = [
        SpotPricesCommand,
        CleanLogsCommand,
    ]
