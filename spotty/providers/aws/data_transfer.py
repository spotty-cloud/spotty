import logging
import subprocess
from spotty.deployment.abstract_cloud_instance.abstract_data_transfer import AbstractDataTransfer
from spotty.providers.aws.helpers.s3_sync import get_s3_sync_command, check_aws_installed


class DataTransfer(AbstractDataTransfer):

    def __init__(self, local_project_dir: str, host_project_dir: str, sync_filters: list, instance_name: str,
                 region: str):
        super().__init__(local_project_dir, host_project_dir, sync_filters, instance_name)

        self._region = region

    @property
    def scheme_name(self) -> str:
        return 's3'

    def upload_local_to_bucket(self, bucket_name: str, dry_run: bool = False):
        """Uploads files from local to the bucket."""
        # check AWS CLI is installed
        check_aws_installed()

        # sync the project with S3, deleted files will be deleted from S3
        local_cmd = get_s3_sync_command(self._local_project_dir, self._get_bucket_project_path(bucket_name),
                                        region=self._region, filters=self._sync_filters, delete=True, dry_run=dry_run)

        # execute the command locally
        logging.debug('Local sync command: ' + local_cmd)
        exit_code = subprocess.call(local_cmd, shell=True)
        if exit_code != 0:
            raise ValueError('Failed to upload the project files to the S3 bucket.')

    def download_bucket_to_local(self, bucket_name: str, download_filters: list):
        """Downloads files from the bucket to local."""
        # check AWS CLI is installed
        check_aws_installed()

        # download files from S3 bucket to local
        local_cmd = get_s3_sync_command(self._get_bucket_downloads_path(bucket_name), self._local_project_dir,
                                        region=self._region, filters=download_filters, exact_timestamp=True)

        # execute the command locally
        logging.debug('Local sync command: ' + local_cmd)
        exit_code = subprocess.call(local_cmd, shell=True)
        if exit_code != 0:
            raise ValueError('Failed to download files from the S3 bucket to local')

    def get_download_bucket_to_instance_command(self, bucket_name: str, use_sudo: bool = False) -> str:
        """A remote command to download files from the bucket to the instance."""
        remote_cmd = get_s3_sync_command(self._get_bucket_project_path(bucket_name), self._host_project_dir,
                                         region=self._region, filters=self._sync_filters, exact_timestamp=True)
        if use_sudo:
            remote_cmd = 'sudo ' + remote_cmd

        return remote_cmd

    def get_upload_instance_to_bucket_command(self, bucket_name: str, download_filters: list, use_sudo: bool = False,
                                              dry_run: bool = False) -> str:
        """A remote command to upload files from the instance to the bucket.

        It uses a temporary S3 directory that is unique for the instance. This
        directory keeps all downloaded from the instance files to sync only changed
        files with local.
        """

        # "sudo" should be called with the "-i" flag to use the root environment, so aws-cli will read
        # the config file from the root home directory
        remote_cmd = get_s3_sync_command(self._host_project_dir, self._get_bucket_downloads_path(bucket_name),
                                         region=self._region, filters=download_filters, delete=True, dry_run=dry_run)
        if use_sudo:
            remote_cmd = 'sudo ' + remote_cmd

        return remote_cmd
