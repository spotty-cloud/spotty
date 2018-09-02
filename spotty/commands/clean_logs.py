from argparse import ArgumentParser
from time import time
import boto3
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.validation import validate_logs_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class CleanLogsCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'clean-logs'

    @staticmethod
    def get_description():
        return 'Delete expired CloudFormation log groups with Spotty prefixes'

    @staticmethod
    def _validate_config(config):
        return validate_logs_config(config)

    @staticmethod
    def configure(parser: ArgumentParser):
        AbstractConfigCommand.configure(parser)
        parser.add_argument('--delete-all', '-a', action='store_true', help='Delete all Spotty log groups, '
                                                                            'not just expired ones')

    def run(self, output: AbstractOutputWriter):
        region = self._config['instance']['region']
        logs = boto3.client('logs', region_name=region)

        prefixes = ['spotty-', '/aws/lambda/spotty-']
        only_empty = not self._args.delete_all

        output.write('Deleting %s Spotty log groups...' % ('empty' if only_empty else 'all'))

        res = logs.describe_log_groups()
        self._delete_log_groups(logs, res['logGroups'], prefixes, only_empty, output)

        while 'nextToken' in res:
            res = logs.describe_log_groups(nextToken=res['nextToken'])
            self._delete_log_groups(logs, res['logGroups'], prefixes, only_empty, output)

        output.write('Done')

    @staticmethod
    def _delete_log_groups(logs, log_groups: list, prefixes: list, only_empty: bool, output: AbstractOutputWriter):
        for log_group in log_groups:
            for prefix in prefixes:
                if log_group['logGroupName'].startswith(prefix):
                    delete = True
                    if only_empty:
                        delete = False
                        days_passed = (int(time()) - log_group['creationTime'] // 1000) // 86400
                        if ('retentionInDays' in log_group) and (days_passed >= log_group['retentionInDays']):
                            delete = True

                    if delete:
                        output.write('[x] %s' % log_group['logGroupName'])
                        logs.delete_log_group(logGroupName=log_group['logGroupName'])
                    break
