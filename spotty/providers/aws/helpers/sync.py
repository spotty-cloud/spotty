import subprocess
from spotty.helpers.ssh import get_ssh_command
from spotty.providers.aws.helpers.aws_cli import AwsCli


def sync_project_with_s3(project_dir, bucket_name, region, sync_filters, dry_run=False):
    # sync the project with S3
    AwsCli(region=region).s3_sync(project_dir, 's3://%s/project' % bucket_name, delete=True,
                                  filters=sync_filters, capture_output=False, dry_run=dry_run)


def sync_instance_with_s3(host: str, user: str, key_path: str, local_ssh_port: int = None):
    # command to sync S3 with the instance
    remote_cmd = subprocess.list2cmdline(['sudo', '-i', '/bin/bash', '-e', '/tmp/scripts/sync_project.sh',
                                          '>', '/dev/null'])

    # connect to the instance and run remote command
    ssh_command = get_ssh_command(host, user, key_path, remote_cmd, local_ssh_port, quiet=True)
    subprocess.call(ssh_command)
