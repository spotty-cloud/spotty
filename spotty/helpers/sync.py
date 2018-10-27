import subprocess
import boto3
from spotty.aws_cli import AwsCli
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.project_resources.bucket import BucketResource
from spotty.project_resources.key_pair import KeyPairResource


def sync_project_with_s3(project_dir, project_name, region, sync_filters, output: AbstractOutputWriter):
    # create or get existing bucket for the project
    s3 = boto3.client('s3', region_name=region)
    project_bucket = BucketResource(s3, project_name, region)
    bucket_name = project_bucket.create_bucket(output)

    # sync the project with S3
    AwsCli(region=region).s3_sync(project_dir, 's3://%s/project' % bucket_name, delete=True,
                                  filters=sync_filters, capture_output=False)


def sync_instance_with_s3(instance_ip_address, project_name, region):
    # command to sync S3 with the instance
    remote_cmd = subprocess.list2cmdline(['sudo', '-i', '/bin/bash', '-e', '/tmp/scripts/sync_project.sh',
                                          '>', '/dev/null'])

    # connect to the instance and run remote command
    host = 'ubuntu@%s' % instance_ip_address
    key_path = KeyPairResource(None, project_name, region).key_path
    ssh_command = ['ssh', '-i', key_path, '-o', 'StrictHostKeyChecking no', '-tq', host, remote_cmd]

    subprocess.call(ssh_command)
