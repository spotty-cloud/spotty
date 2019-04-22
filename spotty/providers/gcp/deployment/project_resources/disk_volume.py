from spotty.deployment.abstract_instance_volume import AbstractInstanceVolume
from spotty.providers.gcp.config.validation import validate_disk_volume_parameters
from spotty.providers.gcp.gcp_resources.disk import Disk
from spotty.providers.gcp.gcp_resources.snapshot import Snapshot
from spotty.providers.gcp.helpers.ce_client import CEClient


class DiskVolume(AbstractInstanceVolume):

    DP_CREATE_SNAPSHOT = 'create_snapshot'
    DP_UPDATE_SNAPSHOT = 'update_snapshot'
    DP_RETAIN = 'retain'
    DP_DELETE = 'delete'

    def __init__(self, ce: CEClient, volume_config: dict, project_name: str, instance_name: str):
        self._ce = ce
        self._name = volume_config['name']
        self._params = validate_disk_volume_parameters(volume_config['parameters'])

        self._project_name = project_name
        self._instance_name = instance_name

    @property
    def title(self):
        return 'Disk'

    @property
    def name(self):
        return self._name

    @property
    def size(self) -> int:
        return self._params['size']

    @property
    def deletion_policy(self) -> str:
        return self._params['deletionPolicy']

    @property
    def deletion_policy_title(self) -> str:
        return {
            DiskVolume.DP_CREATE_SNAPSHOT: 'Create Snapshot',
            DiskVolume.DP_UPDATE_SNAPSHOT: 'Update Snapshot',
            DiskVolume.DP_RETAIN: 'Retain Volume',
            DiskVolume.DP_DELETE: 'Delete Volume',
        }[self.deletion_policy]

    @property
    def disk_name(self) -> str:
        """Returns the disk name."""
        disk_name = self._params['diskName']
        if not disk_name:
            disk_name = '%s-%s-%s' % (self._project_name.lower(), self._instance_name.lower(), self.name.lower())

        return disk_name

    @property
    def mount_dir(self) -> str:
        if self._params['mountDir']:
            mount_dir = self._params['mountDir']
        else:
            mount_dir = '/mnt/%s' % self.disk_name

        return mount_dir

    def get_disk(self) -> Disk:
        return Disk.get_by_name(self._ce, self.disk_name)

    def get_snapshot(self) -> Snapshot:
        return Snapshot.get_by_name(self._ce, self.disk_name)
