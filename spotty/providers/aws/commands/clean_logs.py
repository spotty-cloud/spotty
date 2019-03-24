from argparse import ArgumentParser, Namespace
from time import time
import boto3
from spotty.commands.abstract_command import AbstractCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class CleanLogsCommand(AbstractCommand):

    name = 'clean-logs'
    description = 'Delete expired CloudFormation log groups with Spotty prefixes'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-r', '--region', type=str, required=True, help='AWS region')
        parser.add_argument('-a', '--delete-all', action='store_true', help='Delete all Spotty log groups, '
                                                                            'not just expired ones')

    def run(self, args: Namespace, output: AbstractOutputWriter):
        region = args.region
        logs = boto3.client('logs', region_name=region)

        prefixes = ['spotty-', '/aws/lambda/spotty-']
        only_empty = not args.delete_all

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
