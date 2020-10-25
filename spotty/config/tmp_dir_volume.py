from spotty.config.host_path_volume import HostPathVolume


class TmpDirVolume(HostPathVolume):

    @property
    def title(self):
        return 'temporary directory'

    @property
    def deletion_policy_title(self) -> str:
        return ''
