from spotty.config.abstract_volume_config import AbstractVolumeConfig
from spotty.providers.aws.resources.snapshot import Snapshot
from spotty.providers.aws.resources.volume import Volume


class VolumeConfig(AbstractVolumeConfig):

    DP_CREATE_SNAPSHOT = 'create_snapshot'
    DP_UPDATE_SNAPSHOT = 'update_snapshot'
    DP_RETAIN = 'retain'
    DP_DELETE = 'delete'

    def __init__(self, ec2, volume_name, volume_params, project_name, instance_name):
        self._ec2 = ec2
        self._name = volume_name
        self._params = volume_params
        self._project_name = project_name
        self._instance_name = instance_name

    @property
    def name(self) -> str:
        """Returns internal name for the volume."""
        return self._name

    @property
    def ec2_volume_name(self) -> str:
        """Returns EBS volume name."""
        return '%s-%s-%s' % (self._project_name, self._instance_name, self._name)

    @property
    def snapshot_name(self) -> str:
        return self._params['snapshotName']

    @property
    def size(self) -> int:
        return self._params['size']

    @property
    def mount_dir(self) -> str:
        if self._params['mountDir']:
            mount_dir = self._params['mountDir']
        else:
            mount_dir = '/mnt/%s' % self.ec2_volume_name

        return mount_dir

    @property
    def deletion_policy(self) -> str:
        return self._params['deletionPolicy']

    def get_ec2_volume(self) -> Volume:
        return Volume.get_by_name(self._ec2, self.ec2_volume_name)

    def get_snapshot(self, from_volume_name=False) -> Snapshot:
        snapshot_name = self.snapshot_name if self.snapshot_name and not from_volume_name else self.ec2_volume_name
        return Snapshot.get_by_name(self._ec2, snapshot_name)
