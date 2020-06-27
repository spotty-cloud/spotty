from spotty.providers.aws.helpers.s3_sync import get_s3_sync_command


def _get_project_s3_path(bucket_name: str):
    """Returns an S3 path to the project directory."""
    return 's3://%s/project' % bucket_name


def _get_downloads_s3_path(bucket_name: str, instance_name: str):
    """Returns an S3 path to the downloads directory."""
    return 's3://%s/download/instance-%s' % (bucket_name, instance_name)


def get_local_to_s3_command(local_project_dir: str, bucket_name: str, region: str, sync_filters: list,
                            dry_run: bool = False) -> str:
    # sync the project with S3, deleted files will be deleted from S3
    local_cmd = get_s3_sync_command(local_project_dir, _get_project_s3_path(bucket_name), region=region,
                                   filters=sync_filters, delete=True, dry_run=dry_run)

    return local_cmd


def get_s3_to_instance_command(bucket_name: str, instance_project_dir: str, region: str, sync_filters: list) -> str:
    """Returns a command that syncs the project from the S3 bucket to the instance."""

    # "sudo" should be called with the "-i" flag to use the root environment and let aws-cli find
    # the config file in the root home directory
    remote_cmd = get_s3_sync_command(_get_project_s3_path(bucket_name), instance_project_dir, region=region,
                                   filters=sync_filters, exact_timestamp=True, quiet=True)
    remote_cmd = 'sudo -i ' + remote_cmd

    return remote_cmd
