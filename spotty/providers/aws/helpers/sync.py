import subprocess
from spotty.providers.aws.helpers.aws_cli import AwsCli
from spotty.providers.aws.project_resources.key_pair import KeyPairResource


def sync_project_with_s3(project_dir, bucket_name, region, sync_filters, dry_run=False):
    # sync the project with S3
    AwsCli(region=region).s3_sync(project_dir, 's3://%s/project' % bucket_name, delete=True,
                                  filters=sync_filters, capture_output=False, dry_run=dry_run)


def sync_instance_with_s3(instance_ip_address, project_name, region):
    # command to sync S3 with the instance
    remote_cmd = subprocess.list2cmdline(['sudo', '-i', '/bin/bash', '-e', '/tmp/scripts/sync_project.sh',
                                          '>', '/dev/null'])

    # connect to the instance and run remote command
    host = 'ubuntu@%s' % instance_ip_address
    key_path = KeyPairResource(project_name, region).key_path
    ssh_command = ['ssh', '-i', key_path, '-o', 'StrictHostKeyChecking no', '-tq', host, remote_cmd]

    subprocess.call(ssh_command)
