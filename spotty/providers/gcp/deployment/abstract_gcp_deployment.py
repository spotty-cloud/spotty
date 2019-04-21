from abc import ABC, abstractmethod
from spotty.providers.gcp.config.instance_config import InstanceConfig
from spotty.providers.gcp.deployment.project_resources.key_pair import KeyPairResource
from spotty.providers.gcp.gcp_resources.image import Image
from spotty.providers.gcp.helpers.ce_client import CEClient


class AbstractGcpDeployment(ABC):

    def __init__(self, project_name: str, instance_config: InstanceConfig):
        self._project_name = project_name
        self._instance_config = instance_config
        self._ce = CEClient(instance_config.project_id, instance_config.zone)

    @property
    def instance_config(self) -> InstanceConfig:
        return self._instance_config

    @property
    @abstractmethod
    def machine_name(self) -> str:
        """Name of the Compute Engine instance."""
        raise NotImplementedError

    @property
    def key_pair(self) -> KeyPairResource:
        return KeyPairResource(self._project_name, self.instance_config.project_id, self.instance_config.zone)

    def get_image(self) -> Image:
        return Image.get_by_name(self._ce, self.instance_config.image_name)
