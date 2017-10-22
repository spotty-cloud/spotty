import datetime
import json
import logging
import subprocess


class Aws(object):
    def __init__(self, region):
        self._region = region

    def run(self, args: list, decode_json=True):
        command_args = ['aws', '--region', self._region] + args

        logging.debug('AWS command: ' + subprocess.list2cmdline(command_args))

        res = subprocess.run(command_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        if res.returncode:
            logging.error('AWS command error: ' + res.stdout.decode('utf-8'))
            return None

        return json.loads(res.stdout) if decode_json else res.stdout.decode('utf-8')

    def s3_sync(self, from_path: str, to_path: str, exclusions=None, inclusions=None) -> str:
        args = ['s3', 'sync', from_path, to_path]

        if exclusions:
            for path in exclusions:
                args += ['--exclude', path]

        if inclusions:
            for path in inclusions:
                args += ['--include', path]

        return self.run(args, False)

    def spot_price(self, instance_type: str) -> dict:
        tomorrow_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        args = ['ec2', 'describe-spot-price-history', '--instance-types', instance_type, '--start-time', tomorrow_date,
                '--filters', 'Name=product-description,Values="Linux/UNIX"']

        return self.run(args)
