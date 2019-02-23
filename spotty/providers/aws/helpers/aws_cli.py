import json
import logging
import shlex
import subprocess
from shutil import which


class AwsCommandError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class AwsCli(object):
    def __init__(self, profile: str = None, region: str = None):
        self._profile = profile
        self._region = region

    def s3_sync(self, from_path: str, to_path: str, filters: list = None, exact_timestamp: bool = False,
                delete: bool = False, capture_output: bool = True, dry_run: bool = False) -> str:
        args = ['s3', 'sync', from_path, to_path]
        args += self.get_s3_sync_arguments(filters, exact_timestamp=exact_timestamp, delete=delete, dry_run=dry_run)

        return self._run(args, False, capture_output=capture_output)

    @staticmethod
    def get_s3_sync_arguments(filters: list = None, exact_timestamp: bool = False, delete: bool = False,
                              quote=False, dry_run: bool = False):
        args = []

        if filters:
            for sync_filter in filters:
                if ('exclude' in sync_filter and 'include' in sync_filter) \
                        or ('exclude' not in sync_filter and 'include' not in sync_filter):
                    raise ValueError('S3 sync filter has wrong format.')

                if 'exclude' in sync_filter:
                    for path in sync_filter['exclude']:
                        args += ['--exclude', shlex.quote(path) if quote else path]

                if 'include' in sync_filter:
                    for path in sync_filter['include']:
                        args += ['--include', shlex.quote(path) if quote else path]

        if exact_timestamp:
            args.append('--exact-timestamp')

        if delete:
            args.append('--delete')

        if dry_run:
            args.append('--dryrun')

        return args

    def _run(self, args: list, json_format=True, capture_output=True):
        aws_cmd = 'aws'
        if which(aws_cmd) is None:
            raise ValueError('AWS CLI is not installed.')

        command_args = [aws_cmd]
        if self._profile:
            command_args += ['--profile', self._profile]

        if self._region:
            command_args += ['--region', self._region]

        if json_format:
            command_args += ['--output', 'json']

        command_args += args

        logging.debug('AWS command: ' + subprocess.list2cmdline(command_args))

        if capture_output:
            res = subprocess.run(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = res.stdout.decode('utf-8')

            logging.debug('AWS command output: ' + output)

            if res.returncode:
                raise AwsCommandError(output)

            if json_format:
                output = json.loads(output)
        else:
            subprocess.run(command_args)
            output = None

        return output
