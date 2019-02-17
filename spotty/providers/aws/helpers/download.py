import subprocess
from spotty.helpers.ssh import get_ssh_command
from spotty.providers.aws.helpers.aws_cli import AwsCli


def get_tmp_instance_s3_path(bucket_name, instance_name):
    return 's3://%s/download/instance-%s' % (bucket_name, instance_name)


def upload_from_instance_to_s3(download_filters: list, host: str, user: str, key_path: str, local_ssh_port: int = None,
                               dry_run: bool = False):
    """Uploads files from the running instance to S3 bucket.

    It uses a temporary S3 directory that is unique for the instance. This
    directory keeps downloaded from the instance files in order to sync only
    changed files with local, not all of them every download).
    """
    args = ['sudo', '/tmp/spotty/instance/scripts/upload_files.sh']
    args += AwsCli.get_s3_sync_arguments(filters=download_filters, delete=True, dry_run=dry_run)

    if not dry_run:
        args += ['>', '/dev/null']

    remote_cmd = subprocess.list2cmdline(args)

    # connect to the instance and run the remote command
    ssh_command = get_ssh_command(host, user, key_path, remote_cmd, local_ssh_port, quiet=not dry_run)
    subprocess.call(ssh_command)


def download_from_s3_to_local(bucket_name: str, instance_name: str, project_dir: str, region: str,
                              download_filters: list, dry_run: bool = False):
    """Downloads files from a temporary S3 directory to local."""
    AwsCli(region=region).s3_sync(get_tmp_instance_s3_path(bucket_name, instance_name), project_dir,
                                  filters=download_filters, exact_timestamp=True, capture_output=False,
                                  dry_run=dry_run)
