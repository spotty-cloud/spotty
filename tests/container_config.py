import unittest
from spotty.config.container_config import ContainerConfig


class TestContainerConfig(unittest.TestCase):

    def test_working_dir(self):
        container_config = ContainerConfig({
            'projectDir': '/workspace/project',
            'workingDir': '',
        })

        self.assertEqual(container_config.project_dir, '/workspace/project')
        self.assertEqual(container_config.working_dir, '/workspace/project')

        container_config = ContainerConfig({
            'projectDir': '/workspace/project',
            'workingDir': '/working-dir',
        })

        self.assertEqual(container_config.project_dir, '/workspace/project')
        self.assertEqual(container_config.working_dir, '/working-dir')


if __name__ == '__main__':
    unittest.main()
