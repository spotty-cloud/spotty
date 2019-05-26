from abc import ABC, abstractmethod
from spotty.providers.gcp.config.instance_config import InstanceConfig
from spotty.providers.gcp.helpers.gcp_credentials import GcpCredentials
from spotty.providers.gcp.helpers.ssh_key import SshKey
from spotty.providers.gcp.helpers.ce_client import CEClient


class AbstractGcpDeployment(ABC):

    def __init__(self, project_name: str, instance_config: InstanceConfig):
        self._project_name = project_name
        self._instance_config = instance_config
        self._credentials = GcpCredentials()
        self._ce = CEClient(self._credentials.project_id, instance_config.zone)

    @property
    def instance_config(self) -> InstanceConfig:
        return self._instance_config

    @property
    @abstractmethod
    def machine_name(self) -> str:
        """Name of the Compute Engine instance."""
        raise NotImplementedError

    @property
    def ssh_key(self) -> SshKey:
        return SshKey(self._project_name, self.instance_config.zone, self.instance_config.provider_name)
