import unittest
import boto3
import os
from moto import mock_ec2
from spotty.providers.aws.resource_managers.key_pair_manager import KeyPairManager
from spotty.providers.instance_manager_factory import PROVIDER_AWS


class TestKeyPairResource(unittest.TestCase):

    def test_key_path(self):
        region = 'eu-central-1'
        project_name = 'TEST_PROJECT'
        key_pair_manager = KeyPairManager(None, project_name, region)

        # check key path
        key_name = 'spotty-key-%s-%s' % (project_name.lower(), region)
        key_path = os.path.join(os.path.expanduser('~'), '.spotty', 'keys', PROVIDER_AWS, key_name)
        self.assertEqual(key_pair_manager.key_path, key_path)

    @mock_ec2
    def test_create_and_delete_key(self):
        region = 'eu-central-1'
        project_name = 'TEST_PROJECT'
        ec2 = boto3.client('ec2', region_name=region)
        key_pair_manager = KeyPairManager(ec2, project_name, region)

        # key doesn't exist
        self.assertFalse(key_pair_manager._ec2_key_exists())

        # create the key
        key_pair_manager.maybe_create_key()
        self.assertTrue(key_pair_manager._ec2_key_exists())
        self.assertTrue(os.path.isfile(key_pair_manager.key_path))
        with open(key_pair_manager.key_path) as f:
            key_content = f.read()

        # make sure the key is not being recreated
        key_pair_manager.maybe_create_key()
        with open(key_pair_manager.key_path) as f:
            same_key_content = f.read()
        self.assertEqual(key_content, same_key_content)

        # create the key and rewrite the key file
        ec2.delete_key_pair(KeyName=key_pair_manager.key_name)
        self.assertFalse(key_pair_manager._ec2_key_exists())
        self.assertTrue(os.path.isfile(key_pair_manager.key_path))
        key_pair_manager.maybe_create_key()
        self.assertTrue(key_pair_manager._ec2_key_exists())
        self.assertTrue(os.path.isfile(key_pair_manager.key_path))
        with open(key_pair_manager.key_path) as f:
            new_key_content = f.read()

        self.assertNotEqual(key_content, new_key_content)

        # recreate the key if the key file doesn't exist
        os.unlink(key_pair_manager.key_path)
        self.assertFalse(os.path.isfile(key_pair_manager.key_path))
        key_pair_manager.maybe_create_key()
        self.assertTrue(key_pair_manager._ec2_key_exists())
        self.assertTrue(os.path.isfile(key_pair_manager.key_path))

        # delete key
        key_pair_manager.delete_key()
        self.assertFalse(key_pair_manager._ec2_key_exists())
        self.assertFalse(os.path.isfile(key_pair_manager.key_path))


if __name__ == '__main__':
    unittest.main()
