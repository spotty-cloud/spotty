from shutil import which
from spotty.deployment.utils.cli import shlex_join


def check_aws_installed():
    """Checks that AWS CLI is installed."""
    if which('aws') is None:
        raise ValueError('AWS CLI is not installed.')


def get_s3_sync_command(from_path: str, to_path: str, profile: str = None, region: str = None, filters: list = None,
                        exact_timestamp: bool = False, delete: bool = False, quiet: bool = False,
                        dry_run: bool = False):
    """Builds an "aws s3 sync" command."""
    args = ['aws']

    if profile:
        args += ['--profile', profile]

    if region:
        args += ['--region', region]

    args += ['s3', 'sync', from_path, to_path]

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

    if exact_timestamp:
        args.append('--exact-timestamp')

    if delete:
        args.append('--delete')

    if quiet:
        args.append('--quiet')

    if dry_run:
        args.append('--dryrun')

    command = shlex_join(args)

    return command
