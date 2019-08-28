import subprocess
from spotty.helpers.ssh import get_ssh_command
from spotty.providers.gcp.helpers.gsutil import GSUtil


BUCKET_SYNC_DIR = 'project'


def get_project_gs_path(bucket_name: str):
    return 'gs://%s/%s' % (bucket_name, BUCKET_SYNC_DIR)


def get_instance_sync_arguments(sync_filters: list):
    """Returns arguments for the "gsutil rsync" command that will be run the instance side."""
    return GSUtil.get_rsync_arguments(sync_filters, quote=True)


def sync_local_to_bucket(project_dir, bucket_name, sync_filters, dry_run=False):
    # sync the project from local to the bucket, deleted local files will be deleted from the bucket
    GSUtil().rsync(project_dir, get_project_gs_path(bucket_name), filters=sync_filters, delete=True,
                   capture_output=False, dry_run=dry_run)


def sync_bucket_to_instance(sync_filters: list, host: str, port: int, user: str, key_path: str):
    """Syncs the project from the bucket to the instance."""
    remote_cmd = subprocess.list2cmdline(['sudo', '/tmp/spotty/instance/scripts/sync_project.sh',
                                          *get_instance_sync_arguments(sync_filters), '>', '/dev/null'])

    # connect to the instance and run remote command
    ssh_command = get_ssh_command(host, port, user, key_path, remote_cmd, quiet=True)
    subprocess.call(ssh_command)
