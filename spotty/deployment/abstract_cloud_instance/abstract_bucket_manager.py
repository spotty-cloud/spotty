from abc import ABC
from spotty.deployment.abstract_cloud_instance.resources.abstract_bucket import AbstractBucket


class AbstractBucketManager(ABC):

    def __init__(self, project_name: str):
        self._project_name = project_name

    @property
    def project_name(self) -> str:
        return self._project_name

    def get_bucket(self) -> AbstractBucket:
        raise NotImplementedError

    def create_bucket(self) -> AbstractBucket:
        raise NotImplementedError
