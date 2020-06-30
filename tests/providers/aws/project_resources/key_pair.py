import unittest
import boto3
import os
from moto import mock_ec2
from spotty.providers.aws.resource_managers.key_pair_manager import KeyPairManager


class TestKeyPairResource(unittest.TestCase):

    def test_key_path(self):
        region = 'eu-central-1'
        project_name = 'TEST_PROJECT'
        provider_name = 'aws'
        key_resource = KeyPairManager(project_name, region, provider_name)

        # check key path
        key_name = 'spotty-key-%s-%s' % (project_name.lower(), region)
        key_path = os.path.join(os.path.expanduser('~'), '.spotty', 'keys', provider_name, key_name)
        self.assertEqual(key_resource.key_path, key_path)

    @mock_ec2
    def test_create_and_delete_key(self):
        region = 'eu-central-1'
        project_name = 'TEST_PROJECT'
        provider_name = 'aws'
        ec2 = boto3.client('ec2', region_name=region)
        key_resource = KeyPairManager(project_name, region, provider_name)

        # key doesn't exist
        self.assertFalse(key_resource._ec2_key_exists())

        # create the key
        key_name = key_resource.get_or_create_key()
        self.assertTrue(key_resource._ec2_key_exists())
        self.assertTrue(os.path.isfile(key_resource.key_path))
        with open(key_resource.key_path) as f:
            key_content = f.read()

        # get the existing key
        key_resource.get_or_create_key()
        with open(key_resource.key_path) as f:
            same_key_content = f.read()

        self.assertEqual(key_content, same_key_content)

        # create the key and rewrite the key file
        ec2.delete_key_pair(KeyName=key_name)
        self.assertFalse(key_resource._ec2_key_exists())
        self.assertTrue(os.path.isfile(key_resource.key_path))
        key_resource.get_or_create_key()
        self.assertTrue(key_resource._ec2_key_exists())
        self.assertTrue(os.path.isfile(key_resource.key_path))
        with open(key_resource.key_path) as f:
            new_key_content = f.read()

        self.assertNotEqual(key_content, new_key_content)

        # recreate the key if the key file doesn't exist
        os.unlink(key_resource.key_path)
        self.assertFalse(os.path.isfile(key_resource.key_path))
        key_resource.get_or_create_key()
        self.assertTrue(key_resource._ec2_key_exists())
        self.assertTrue(os.path.isfile(key_resource.key_path))

        # delete key
        key_resource.delete_key()
        self.assertFalse(key_resource._ec2_key_exists())
        self.assertFalse(os.path.isfile(key_resource.key_path))


if __name__ == '__main__':
    unittest.main()
