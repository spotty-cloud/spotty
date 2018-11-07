import subprocess
import boto3
from spotty.aws_cli import AwsCli
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.helpers.ssh import get_ssh_command
from spotty.project_resources.bucket import BucketResource


def sync_project_with_s3(project_dir, project_name, region, sync_filters, output: AbstractOutputWriter):
    # create or get existing bucket for the project
    project_bucket = BucketResource(project_name, region)
    bucket_name = project_bucket.get_or_create_bucket(output)

    # sync the project with S3
    AwsCli(region=region).s3_sync(project_dir, 's3://%s/project' % bucket_name, delete=True,
                                  filters=sync_filters, capture_output=False)

    return bucket_name


def sync_instance_with_s3(instance_ip_address, project_name, region, local_ssh_port: None):
    # command to sync S3 with the instance
    remote_cmd = subprocess.list2cmdline(['sudo', '-i', '/bin/bash', '-e', '/tmp/scripts/sync_project.sh',
                                          '>', '/dev/null'])

    # connect to the instance and run remote command
    ssh_command = get_ssh_command(project_name, region, instance_ip_address, remote_cmd, local_ssh_port, quiet=True)
    subprocess.call(ssh_command)
