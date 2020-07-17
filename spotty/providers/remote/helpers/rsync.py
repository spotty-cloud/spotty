from shutil import which
from typing import List
from spotty.deployment.utils.cli import shlex_join


def check_rsync_installed():
    """Checks that rsync is installed."""
    if which('rsync') is None:
        raise ValueError('rsync is not installed.')


def get_upload_command(local_dir: str, remote_dir: str, ssh_user: str, ssh_host: str, ssh_port: int,
                       ssh_key_path: str, filters: List[dict] = None, use_sudo: bool = False, dry_run: bool = False):
    # make sure there is only one list of exclude filters
    if (len(filters) > 1) or (len(filters[0]) > 1) or ('include' in filters[0]):
        raise ValueError('At the moment "remote" provider supports only one list of exclude filters.')

    remote_path = '%s@%s:%s' % (ssh_user, ssh_host, remote_dir)

    return _get_rsync_command(local_dir, remote_path, ssh_port, ssh_key_path, filters, mkdir=remote_dir,
                              use_sudo=use_sudo, dry_run=dry_run)


def get_download_command(remote_dir: str, local_dir: str, ssh_user: str, ssh_host: str, ssh_port: int,
                         ssh_key_path: str, filters: List[dict] = None, use_sudo: bool = False, dry_run: bool = False):
    filters = filters[::-1]
    remote_path = '%s@%s:%s' % (ssh_user, ssh_host, remote_dir)

    return _get_rsync_command(remote_path, local_dir, ssh_port, ssh_key_path, filters, use_sudo=use_sudo,
                              dry_run=dry_run)


def _get_rsync_command(src_path: str, dst_path: str, ssh_port: int, ssh_key_path: str, filters: List[dict] = None,
                       mkdir: str = None, use_sudo: bool = False, dry_run: bool = False):

    sudo_str = 'sudo ' if use_sudo else ''
    remote_rsync_cmd = sudo_str + 'rsync'
    if mkdir:
        remote_rsync_cmd = '%smkdir -p \'%s\' && %s' % (sudo_str, mkdir, remote_rsync_cmd)

    rsync_cmd = 'rsync -av ' \
                '--no-owner ' \
                '--no-group ' \
                '--prune-empty-dirs ' \
                '-e "ssh -i \'%s\' -p %d -o StrictHostKeyChecking=no -o ConnectTimeout=10" ' \
                '--rsync-path="%s"'  \
                % (ssh_key_path, ssh_port, remote_rsync_cmd)

    if dry_run:
        rsync_cmd += ' --dry-run'

    if filters:
        args = []
        for sync_filter in filters:
            if 'exclude' in sync_filter:
                for path in sync_filter['exclude']:
                    args += ['--exclude', _fix_filter_path(path)]

            if 'include' in sync_filter:
                for path in sync_filter['include']:
                    args += ['--include', _fix_filter_path(path)]

        rsync_cmd += ' ' + shlex_join(args)

    rsync_cmd += ' %s/ %s' % (src_path.rstrip('/'), dst_path)

    return rsync_cmd


def _fix_filter_path(path: str) -> str:
    return '/' + path.replace('*', '**').lstrip('/')
