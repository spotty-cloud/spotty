from spotty.config.container_config import ContainerConfig
from spotty.config.validation import validate_basic_config
from spotty.utils import filter_list


class ProjectConfig(object):

    def __init__(self, config: dict, project_dir: str):
        # validate the config
        config = validate_basic_config(config, project_dir)

        self._project_dir = project_dir
        self._config = config
        self._container = ContainerConfig(config['container'])

    @property
    def project_dir(self) -> str:
        return self._project_dir

    @property
    def project_name(self) -> str:
        return self._config['project']['name']

    @property
    def sync_filters(self) -> list:
        return self._config['project']['syncFilters']

    @property
    def container(self) -> ContainerConfig:
        return self._container

    @property
    def scripts(self) -> dict:
        return self._config['scripts']

    @property
    def instances(self) -> list:
        return self._config['instances']
