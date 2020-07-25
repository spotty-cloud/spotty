from abc import ABC, abstractmethod


class AbstractDataTransfer(ABC):

    def __init__(self, local_project_dir: str, host_project_dir: str, sync_filters: list, instance_name: str):
        self._instance_name = instance_name
        self._local_project_dir = local_project_dir
        self._host_project_dir = host_project_dir
        self._sync_filters = sync_filters

    @property
    def instance_name(self):
        return self._instance_name

    @property
    @abstractmethod
    def scheme_name(self) -> str:
        raise NotImplementedError

    def _get_bucket_project_path(self, bucket_name: str) -> str:
        """A bucket path where the project files are located."""
        return '%s://%s/project' % (self.scheme_name, bucket_name)

    def _get_bucket_downloads_path(self, bucket_name: str) -> str:
        """A bucket path where the downloaded files are located."""
        return '%s://%s/download/instance-%s' % (self.scheme_name, bucket_name, self.instance_name)

    @abstractmethod
    def upload_local_to_bucket(self, bucket_name: str, dry_run: bool = False):
        """Uploads files from local to the bucket."""
        raise NotImplementedError

    @abstractmethod
    def download_bucket_to_local(self, bucket_name: str, download_filters: list):
        """Downloads files from the bucket to local."""
        raise NotImplementedError

    @abstractmethod
    def get_download_bucket_to_instance_command(self, bucket_name: str, use_sudo: bool = False) -> str:
        """A remote command to download files from the bucket to the instance."""
        raise NotImplementedError

    @abstractmethod
    def get_upload_instance_to_bucket_command(self, bucket_name: str, download_filters: list, use_sudo: bool = False,
                                              dry_run: bool = False) -> str:
        """A remote command to upload files from the instance to the bucket."""
        raise NotImplementedError
