import logging
import subprocess
from spotty.deployment.abstract_cloud_instance.abstract_data_transfer import AbstractDataTransfer
from spotty.providers.gcp.helpers.gsutil_rsync import check_gsutil_installed, get_rsync_command


class DataTransfer(AbstractDataTransfer):

    @property
    def scheme_name(self) -> str:
        return 'gs'

    def upload_local_to_bucket(self, bucket_name: str, dry_run: bool = False):
        """Uploads files from local to the bucket."""
        # check gsutil is installed
        check_gsutil_installed()

        # sync the project with S3, deleted files will be deleted from S3
        local_cmd = get_rsync_command(self._local_project_dir, self._get_bucket_project_path(bucket_name),
                                      filters=self._sync_filters, delete=True, dry_run=dry_run)

        # execute the command locally
        logging.debug('Local sync command: ' + local_cmd)
        exit_code = subprocess.call(local_cmd, shell=True)
        if exit_code != 0:
            raise ValueError('Failed to upload the project files to the GS bucket.')

    def download_bucket_to_local(self, bucket_name: str, download_filters: list):
        """Downloads files from the bucket to local."""
        raise NotImplementedError

    def get_download_bucket_to_instance_command(self, bucket_name: str, use_sudo: bool = False) -> str:
        """A remote command to download files from the bucket to the instance."""
        remote_cmd = get_rsync_command(self._get_bucket_project_path(bucket_name), self._host_project_dir,
                                       filters=self._sync_filters)
        if use_sudo:
            remote_cmd = 'sudo ' + remote_cmd

        return remote_cmd

    def get_upload_instance_to_bucket_command(self, bucket_name: str, download_filters: list, use_sudo: bool = False,
                                              dry_run: bool = False) -> str:
        """A remote command to upload files from the instance to the bucket.

        It uses a temporary directory on the bucket that is unique for the instance. This
        directory keeps all downloaded from the instance files to sync only changed
        files with local.
        """
        raise NotImplementedError
