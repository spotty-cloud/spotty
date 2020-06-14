import unittest
from spotty.config.container_config import ContainerConfig, VolumeMount
from spotty.deployment.container_deployment import ContainerDeployment
from spotty.providers.test.deployment.test_volume import TestVolume


class TestContainerDeployment(unittest.TestCase):

    def test_instance_volume(self):
        project_name = 'test-project'
        container_config = ContainerConfig({
            'file': 'docker/Dockerfile',
            'projectDir': '/workspace/project',
            'volumeMounts': [{
                'name': 'workspace',
                'mountPath': '/workspace',
            }],
        })

        volumes = [
            TestVolume('workspace', '/mnt/test'),
            TestVolume('docker', '/mnt/docker'),
        ]

        container = ContainerDeployment(project_name, volumes, container_config)

        self.assertEqual(container.host_project_dir, '/mnt/test/project')
        self.assertEqual(container.dockerfile_path, '/mnt/test/project/docker/Dockerfile')
        self.assertEqual(container.docker_context_path, '/mnt/test/project/docker')
        self.assertEqual(len(container.volume_mounts), 1)
        self.assertEqual(container.volume_mounts[0], VolumeMount(name='workspace', host_dir='/mnt/test',
                                                                 container_dir='/workspace'))

    def test_tmp_volume(self):
        project_name = 'test-project'
        container_config = ContainerConfig({
            'file': 'docker/Dockerfile',
            'projectDir': '/workspace/project',
            'volumeMounts': [{
                'name': 'workspace',
                'mountPath': '/workspace',
            }],
        })

        volumes = [
            TestVolume('docker', '/mnt/docker'),
        ]

        container = ContainerDeployment(project_name, volumes, container_config)

        self.assertRegex(container.host_project_dir, '/tmp/spotty/container/volumes/workspace/project')
        self.assertRegex(container.dockerfile_path, '/tmp/spotty/container/volumes/workspace/project/docker/Dockerfile')
        self.assertRegex(container.docker_context_path, '/tmp/spotty/container/volumes/workspace/project/docker')
        self.assertEqual(container.volume_mounts[0].name, 'workspace')
        self.assertEqual(container.volume_mounts[0].container_dir, '/workspace')
        self.assertRegex(container.volume_mounts[0].host_dir, '/tmp/spotty/container/volumes/workspace')
        self.assertEqual(len(container.volume_mounts), 1)

    def test_tmp_project_volume(self):
        project_name = 'test-project'
        container_config = ContainerConfig({
            'file': 'docker/Dockerfile',
            'projectDir': '/workspace/project',
            'volumeMounts': [],
        })

        volumes = [
            TestVolume('docker', '/mnt/docker'),
        ]

        container = ContainerDeployment(project_name, volumes, container_config)

        self.assertRegex(container.host_project_dir, '/tmp/spotty/container/volumes/.project')
        self.assertRegex(container.dockerfile_path, '/tmp/spotty/container/volumes/.project/docker/Dockerfile')
        self.assertRegex(container.docker_context_path, '/tmp/spotty/container/volumes/.project/docker')
        self.assertEqual(container.volume_mounts[0].name, None)
        self.assertEqual(container.volume_mounts[0].container_dir, '/workspace/project')
        self.assertRegex(container.volume_mounts[0].host_dir, '/tmp/spotty/container/volumes/.project')
        self.assertEqual(len(container.volume_mounts), 1)


if __name__ == '__main__':
    unittest.main()
