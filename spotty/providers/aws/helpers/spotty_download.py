from spotty.providers.aws.helpers.s3_sync import get_s3_sync_command


def _get_downloads_s3_path(bucket_name: str, instance_name: str):
    """Returns an S3 path to the downloads directory."""
    return 's3://%s/download/instance-%s' % (bucket_name, instance_name)


def get_instance_to_s3_command(instance_project_dir: str, bucket_name: str, instance_name: str, region: str,
                               download_filters: list, dry_run: bool = False):
    """Uploads files from the running instance to the S3 bucket.

    It uses a temporary S3 directory that is unique for the instance. This
    directory keeps all downloaded from the instance files to sync only changed
    files with local.
    """

    # "sudo" should be called with the "-i" flag to use the root environment, so aws-cli will read
    # the config file from the root home directory
    remote_cmd = get_s3_sync_command(instance_project_dir, _get_downloads_s3_path(bucket_name, instance_name),
                                     region=region, filters=download_filters, delete=True, dry_run=dry_run)
    remote_cmd = 'sudo -i ' + remote_cmd

    return remote_cmd


def get_s3_to_local_command(bucket_name: str, instance_name: str, local_project_dir: str, region: str,
                            download_filters: list):
    """Downloads files from a temporary S3 directory to local."""
    local_cmd = get_s3_sync_command(_get_downloads_s3_path(bucket_name, instance_name), local_project_dir,
                                    region=region, filters=download_filters, exact_timestamp=True)

    return local_cmd
