from spotty.config.abstract_instance_volume import AbstractInstanceVolume


class TestVolume(AbstractInstanceVolume):

    def _validate_volume_parameters(self, params: dict) -> dict:
        return params

    @property
    def title(self) -> str:
        return 'test'

    @property
    def host_path(self) -> str:
        return self._params['host_path']
