import unittest
import boto3
from spotty.commands.writers.null_output_writrer import NullOutputWriter
from spotty.providers.aws.resource_managers.bucket_manager import BucketResource
from moto import mock_s3


class TestBucketResource(unittest.TestCase):

    @mock_s3
    def test_create_and_find_bucket(self):
        region = 'eu-central-1'
        project_name = 'TEST_PROJECT'
        s3 = boto3.client('s3', region_name=region)
        bucket_resource = BucketResource(project_name, region)
        output = NullOutputWriter()

        # bucket not found
        self.assertFalse(bucket_resource._find_bucket())

        # bucket found
        bucket_name = bucket_resource.get_or_create_bucket(output)
        self.assertEqual(bucket_name, bucket_resource._find_bucket())
        self.assertEqual(bucket_name, bucket_resource.get_or_create_bucket(output))

        # several buckets found
        second_bucket_name = 'spotty-%s-111111111111-%s' % (project_name.lower(), region)
        s3.create_bucket(Bucket=second_bucket_name)
        with self.assertRaises(ValueError):
            bucket_resource._find_bucket()
        with self.assertRaises(ValueError):
            bucket_resource.get_or_create_bucket(output)


if __name__ == '__main__':
    unittest.main()
