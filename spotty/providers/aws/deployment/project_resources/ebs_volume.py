from spotty.deployment.abstract_instance_volume import AbstractInstanceVolume
from spotty.providers.aws.aws_resources.snapshot import Snapshot
from spotty.providers.aws.aws_resources.volume import Volume
from spotty.providers.aws.config.validation import validate_ebs_volume_parameters


class EbsVolume(AbstractInstanceVolume):

    DP_CREATE_SNAPSHOT = 'create_snapshot'
    DP_UPDATE_SNAPSHOT = 'update_snapshot'
    DP_RETAIN = 'retain'
    DP_DELETE = 'delete'

    def __init__(self, ec2, volume_config: dict, project_name: str, instance_name: str):
        self._ec2 = ec2
        self._name = volume_config['name']
        self._params = validate_ebs_volume_parameters(volume_config['parameters'])

        self._project_name = project_name
        self._instance_name = instance_name

    @property
    def title(self):
        return 'EBS volume'

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
            EbsVolume.DP_CREATE_SNAPSHOT: 'Create Snapshot',
            EbsVolume.DP_UPDATE_SNAPSHOT: 'Update Snapshot',
            EbsVolume.DP_RETAIN: 'Retain Volume',
            EbsVolume.DP_DELETE: 'Delete Volume',
        }[self.deletion_policy]

    @property
    def ec2_volume_name(self) -> str:
        """Returns EBS volume name."""
        volume_name = self._params['volumeName']
        if not volume_name:
            volume_name = '%s-%s-%s' % (self._project_name.lower(), self._instance_name.lower(), self.name.lower())

        return volume_name

    @property
    def mount_dir(self) -> str:
        if self._params['mountDir']:
            mount_dir = self._params['mountDir']
        else:
            mount_dir = '/mnt/%s' % self.ec2_volume_name

        return mount_dir

    def get_ec2_volume(self) -> Volume:
        return Volume.get_by_name(self._ec2, self.ec2_volume_name)

    def get_snapshot(self) -> Snapshot:
        return Snapshot.get_by_name(self._ec2, self.ec2_volume_name)
