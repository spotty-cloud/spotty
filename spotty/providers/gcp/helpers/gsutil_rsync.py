import fnmatch
from shutil import which
import os
from typing import List

from spotty.deployment.utils.cli import shlex_join


def check_gsutil_installed():
    """Checks that gsutil is installed."""
    if which('gsutil') is None:
        raise ValueError('gsutil is not installed.')


def get_rsync_command(from_path: str, to_path: str, filters: List[dict] = None, delete: bool = False,
                      quiet: bool = False, dry_run: bool = False):
    args = ['gsutil', '-m']
    if quiet:
        args.append('-q')

    args += ['rsync', '-r']

    if filters:
        if (len(filters) > 1) or (len(filters[0]) > 1) or ('include' in filters[0]):
            raise ValueError('At the moment GCP provider supports only one list of exclude filters.')

        path_regs = []
        for path in filters[0]['exclude']:
            path = path.replace('/', os.sep)  # fix for Windows machines
            path_regs.append(fnmatch.translate(path)[4:-3])

        filter_regex = '^(%s)$' % '|'.join(path_regs)
        args += ['-x', filter_regex]

    if delete:
        args.append('-d')

    if dry_run:
        args.append('-n')

    args += [from_path, to_path]

    return shlex_join(args)
