from spotty.providers.aws.helpers.aws_cli import AwsCli


def get_project_s3_path(bucket_name: str):
    return 's3://%s/project' % bucket_name


def get_instance_sync_arguments(sync_filters: list):
    """Returns arguments for the "aws sync" command that will be run the instance side."""
    return AwsCli.get_s3_sync_arguments(sync_filters, exact_timestamp=True, quote=True)


def sync_local_to_s3(local_project_dir, bucket_name, region, sync_filters, dry_run=False):
    # sync the project with S3, deleted files will be deleted from S3
    AwsCli(region=region).s3_sync(local_project_dir, get_project_s3_path(bucket_name), filters=sync_filters,
                                  delete=True, capture_output=False, dry_run=dry_run)


def get_sync_s3_to_instance_cmd(project_s3_path, instance_project_dir, sync_filters: list) -> list:
    """Returns a command that syncs the project from the S3 bucket to the instance."""

    # "sudo" should be called with the "-i" flag to use the root environment, so aws-cli will read
    # the config file from the root home directory
    sync_cmd = ['sudo', '-i', 'aws', 's3', 'sync', project_s3_path, instance_project_dir,
                *get_instance_sync_arguments(sync_filters), '>', '/dev/null']

    return sync_cmd
