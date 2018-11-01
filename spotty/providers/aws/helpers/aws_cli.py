import json
import logging
import subprocess


class AwsCommandError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class AwsCli(object):
    def __init__(self, profile: str = None, region: str = None):
        self._profile = profile
        self._region = region

    def s3_sync(self, from_path: str, to_path: str, delete=False, filters=None, capture_output=True) -> str:
        args = ['s3', 'sync', from_path, to_path]

        if delete:
            args.append('--delete')

        if filters:
            for sync_filter in filters:
                if ('exclude' in sync_filter and 'include' in sync_filter) \
                        or ('exclude' not in sync_filter and 'include' not in sync_filter):
                    raise ValueError('S3 sync filter has wrong format.')

                if 'exclude' in sync_filter:
                    for path in sync_filter['exclude']:
                        args += ['--exclude', path]

                if 'include' in sync_filter:
                    for path in sync_filter['include']:
                        args += ['--include', path]

        return self._run(args, False, capture_output=capture_output)

    def _run(self, args: list, json_format=True, capture_output=True):
        command_args = ['aws']
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
