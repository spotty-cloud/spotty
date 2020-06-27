import os
import subprocess
import tempfile
from glob import glob
from spotty.providers.aws.helpers.s3_sync import get_s3_sync_command


def get_logs_s3_path(bucket_name: str, instance_name: str) -> str:
    return 's3://%s/logs/aws/%s' % (bucket_name, instance_name)


def download_logs(bucket_name: str, instance_name: str, stack_uuid: str, region: str) -> list:
    """Downloads logs from S3 bucket to temporary directory."""
    logs_s3_path = '%s/%s' % (get_logs_s3_path(bucket_name, instance_name), stack_uuid)
    local_logs_dir = tempfile.mkdtemp()

    # download logs
    download_cmd = get_s3_sync_command(logs_s3_path, local_logs_dir, region=region, exact_timestamp=True, quiet=True)
    subprocess.call(download_cmd, shell=True)

    # get paths to the downloaded files
    log_paths = glob(os.path.join(local_logs_dir, '**', '*'), recursive=True)

    return log_paths
