from spotty.config.abstract_instance_config import AbstractInstanceConfig
from spotty.providers.gcp.config.validation import validate_instance_parameters

VOLUME_TYPE_DISK = 'disk'
DEFAULT_IMAGE_NAME = 'spotty'


class InstanceConfig(AbstractInstanceConfig):

    def __init__(self, config: dict):
        super().__init__(config)

        self._params = validate_instance_parameters(self._params)

    @property
    def project_id(self) -> str:
        return self._params['projectId']

    @property
    def zone(self) -> str:
        return self._params['zone']

    @property
    def machine_type(self) -> str:
        return self._params['machineType']

    @property
    def gpu(self) -> dict:
        return self._params['gpu']

    @property
    def on_demand(self) -> bool:
        return self._params['onDemandInstance']

    @property
    def boot_disk_size(self) -> int:
        return self._params['bootDiskSize']

    @property
    def image_name(self) -> str:
        return self._params['imageName'] if self._params['imageName'] else DEFAULT_IMAGE_NAME

    @property
    def has_image_name(self) -> bool:
        return bool(self._params['imageName'])

    @property
    def image_url(self) -> str:
        return self._params['imageUrl']
