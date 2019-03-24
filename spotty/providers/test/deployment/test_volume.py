from spotty.deployment.abstract_instance_volume import AbstractInstanceVolume


class TestVolume(AbstractInstanceVolume):

    def __init__(self, volume_name, mount_dir):
        self._volume_name = volume_name
        self._mount_dir = mount_dir

    @property
    def title(self) -> str:
        return 'test'

    @property
    def name(self) -> str:
        return self._volume_name

    @property
    def mount_dir(self) -> str:
        return self._mount_dir
