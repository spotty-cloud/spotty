import unittest
from spotty.deployment.abstract_cloud.errors.bucket_not_found import BucketNotFoundError
from spotty.providers.aws.resource_managers.bucket_manager import BucketManager
from moto import mock_s3


class TestBucketResource(unittest.TestCase):

    @mock_s3
    def test_create_and_find_bucket(self):
        region = 'eu-central-1'
        project_name = 'TEST_PROJECT'
        bucket_resource = BucketManager(project_name, region)

        # bucket not found
        with self.assertRaises(BucketNotFoundError):
            bucket_resource.get_bucket()

        # bucket found
        bucket_name = bucket_resource.create_bucket().name
        self.assertEqual(bucket_name, bucket_resource.get_bucket().name)

        # several buckets found
        bucket_resource.create_bucket()
        with self.assertRaises(ValueError):
            bucket_resource.get_bucket()


if __name__ == '__main__':
    unittest.main()
