from abc import ABC, abstractmethod


class AbstractDataTransfer(ABC):

    @property
    @abstractmethod
    def instance_name(self) -> str:
        raise NotImplementedError

    def _get_bucket_project_path(self, bucket_name: str) -> str:
        """A bucket path where the project files are located."""
        return bucket_name + '/project'

    def _get_bucket_downloads_path(self, bucket_name: str) -> str:
        """A bucket path where the downloaded files are located."""
        return bucket_name + '/download/instance-' + self.instance_name

    @abstractmethod
    def upload_local_to_bucket(self, bucket_name: str, dry_run: bool = False):
        """Uploads files from local to the bucket."""
        raise NotImplementedError

    @abstractmethod
    def download_bucket_to_local(self, bucket_name: str, download_filters: list):
        """Downloads files from the bucket to local."""
        raise NotImplementedError

    @abstractmethod
    def get_download_bucket_to_instance_command(self, bucket_name: str) -> str:
        """A remote command to download files from the bucket to the instance."""
        raise NotImplementedError

    @abstractmethod
    def get_upload_instance_to_bucket_command(self, bucket_name: str, download_filters: list,
                                              dry_run: bool = False) -> str:
        """A remote command to upload files from the instance to the bucket."""
        raise NotImplementedError
