import os
import tempfile
from glob import glob
from spotty.providers.aws.helpers.aws_cli import AwsCli


def get_logs_s3_path(bucket_name: str, instance_name: str) -> str:
    return 's3://%s/logs/aws/%s' % (bucket_name, instance_name)


def download_logs(bucket_name: str, instance_name: str, stack_uuid: str, region: str) -> list:
    """Downloads logs from S3 bucket to temporary directory."""
    s3_logs_path = '%s/%s' % (get_logs_s3_path(bucket_name, instance_name), stack_uuid)
    local_logs_dir = tempfile.mkdtemp()

    # download logs
    AwsCli(region=region).s3_sync(s3_logs_path, local_logs_dir, exact_timestamp=True, quiet=True, capture_output=False)

    # get paths to the downloaded logs
    log_paths = glob(os.path.join(local_logs_dir, '**', '*'), recursive=True)

    return log_paths
