from spotty.providers.aws.helpers.aws_cli import AwsCli


def get_tmp_instance_s3_path(bucket_name, instance_name):
    return 's3://%s/download/instance-%s' % (bucket_name, instance_name)


def get_upload_instance_to_s3_cmd(instance_project_dir: str, instance_name: str, bucket_name: str,
                                  download_filters: list, dry_run: bool = False):
    """Uploads files from the running instance to the S3 bucket.

    It uses a temporary S3 directory that is unique for the instance. This
    directory keeps downloaded from the instance files in order to sync only
    changed files with local, not all of them every download).
    """

    # "sudo" should be called with the "-i" flag to use the root environment, so aws-cli will read
    # the config file from the root home directory
    upload_s3_path = get_tmp_instance_s3_path(bucket_name, instance_name),
    upload_cmd = ['sudo', '-i', 'aws', 's3', 'sync', instance_project_dir, upload_s3_path]
    upload_cmd += AwsCli.get_s3_sync_arguments(filters=download_filters, delete=True, quote=True, dry_run=dry_run)

    return upload_cmd


def download_from_s3_to_local(bucket_name: str, instance_name: str, local_project_dir: str, region: str,
                              download_filters: list, dry_run: bool = False):
    """Downloads files from a temporary S3 directory to local."""
    AwsCli(region=region).s3_sync(get_tmp_instance_s3_path(bucket_name, instance_name), local_project_dir,
                                  filters=download_filters, exact_timestamp=True, capture_output=False,
                                  dry_run=dry_run)
