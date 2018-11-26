from importlib import import_module
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class InstanceManagerFactory(object):
    INSTANCE_MANAGER_CLASSES = {
        'aws': 'AwsInstanceManager',
    }

    @classmethod
    def get_instance(cls, project_name: str, instance_config: dict, container_config: dict) -> AbstractInstanceManager:
        provider_name = instance_config['provider']
        if provider_name not in cls.INSTANCE_MANAGER_CLASSES:
            raise ValueError('Provider "%s" is not supported' % provider_name)

        InstanceManagerClass = getattr(import_module('spotty.providers.%s.instance_manager' % provider_name),
                                       cls.INSTANCE_MANAGER_CLASSES[provider_name])

        instance_name = instance_config['name']
        instance_params = instance_config['parameters']

        return InstanceManagerClass(project_name, instance_name, instance_params, container_config)
