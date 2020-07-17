from typing import List
from spotty.config.abstract_instance_config import AbstractInstanceConfig, VolumeMount
from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.providers.gcp.config.disk_volume import DiskVolume
from spotty.providers.gcp.config.validation import validate_instance_parameters


VOLUME_TYPE_DISK = 'Disk'
DEFAULT_IMAGE_NAME = 'spotty'


class InstanceConfig(AbstractInstanceConfig):

    def _validate_instance_params(self, params: dict) -> dict:
        return validate_instance_parameters(params)

    def _get_instance_volumes(self) -> List[AbstractInstanceVolume]:
        volumes = []
        for volume_config in self._params['volumes']:
            volume_type = volume_config['type']
            if volume_type == DiskVolume.TYPE_NAME:
                volumes.append(DiskVolume(volume_config, self.project_config.project_name, self.name))
            else:
                raise ValueError('GCP volume type "%s" not supported.' % volume_type)

        return volumes

    @property
    def user(self):
        return 'spotty'

    @property
    def machine_name(self) -> str:
        """Name of the Compute Engine instance."""
        return '%s-%s' % (self.project_config.project_name.lower(), self.name.lower())

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
    def is_preemptible_instance(self) -> bool:
        return self._params['preemptibleInstance']

    @property
    def boot_disk_size(self) -> int:
        return self._params['bootDiskSize']

    @property
    def ports(self) -> List[int]:
        return list(set(self._params['ports']))

    @property
    def image_name(self) -> str:
        return self._params['imageName']

    @property
    def has_image_name(self) -> bool:
        return bool(self._params['imageName'])

    @property
    def image_uri(self) -> str:
        return self._params['imageUri']
