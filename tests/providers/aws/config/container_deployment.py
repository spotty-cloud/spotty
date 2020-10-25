import os
import unittest
from spotty.config.abstract_instance_config import VolumeMount
from spotty.config.config_utils import _read_yaml
from spotty.config.project_config import ProjectConfig
from spotty.providers.aws.config.instance_config import InstanceConfig


class TestContainerDeployment(unittest.TestCase):

    def test_instance_volume(self):
        local_project_dir = os.path.join(os.path.dirname(__file__), 'data')
        config = _read_yaml(os.path.join(local_project_dir, 'config1.yaml'))

        project_config = ProjectConfig(config, local_project_dir)
        instance_config = InstanceConfig(project_config.instances[0], project_config)

        self.assertEqual(instance_config.host_project_dir, '/mnt/test/project')
        self.assertEqual(instance_config.dockerfile_path, '/mnt/test/project/docker/Dockerfile')
        self.assertEqual(instance_config.docker_context_path, '/mnt/test/project/docker')
        self.assertEqual(len(instance_config.volume_mounts), 2)
        self.assertEqual(instance_config.volume_mounts[0], VolumeMount(name='workspace',
                                                                       host_path='/mnt/test',
                                                                       mount_path='/workspace',
                                                                       mode='rw',
                                                                       hidden=False))
        self.assertEqual(instance_config.volume_mounts[1], VolumeMount(name=None,
                                                                       host_path='/root/.aws',
                                                                       mount_path='/root/.aws',
                                                                       mode='ro',
                                                                       hidden=True,))

    def test_tmp_project_volume(self):
        local_project_dir = os.path.join(os.path.dirname(__file__), 'data')
        config = _read_yaml(os.path.join(local_project_dir, 'config-wo-mounts.yaml'))

        project_config = ProjectConfig(config, local_project_dir)
        instance_config = InstanceConfig(project_config.instances[0], project_config)

        host_project_dir = '/tmp/spotty/containers/spotty-my-project-aws-1-default/volumes/.project'

        self.assertEqual(instance_config.host_project_dir, host_project_dir)
        self.assertEqual(instance_config.dockerfile_path, os.path.join(host_project_dir, 'docker', 'Dockerfile'))
        self.assertEqual(instance_config.docker_context_path, os.path.join(host_project_dir, 'docker'))
        self.assertEqual(len(instance_config.volume_mounts), 1)
        self.assertEqual(instance_config.volume_mounts[0], VolumeMount(name=None,
                                                                       host_path=host_project_dir,
                                                                       mount_path='/workspace/project',
                                                                       mode='rw',
                                                                       hidden=True))


if __name__ == '__main__':
    unittest.main()
