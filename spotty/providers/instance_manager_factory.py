from importlib import import_module
from spotty.config.project_config import ProjectConfig
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class InstanceManagerFactory(object):

    INSTANCE_MANAGER_CLASSES = {
        'aws': 'AwsInstanceManager',
    }

    @classmethod
    def get_instance(cls, instance_config: dict, project_config: ProjectConfig) -> AbstractInstanceManager:
        provider_name = instance_config['provider']
        if provider_name not in cls.INSTANCE_MANAGER_CLASSES:
            raise ValueError('Provider "%s" is not supported' % provider_name)

        InstanceManagerClass = getattr(import_module('spotty.providers.%s.instance_manager' % provider_name),
                                       cls.INSTANCE_MANAGER_CLASSES[provider_name])

        return InstanceManagerClass(instance_config, project_config)
