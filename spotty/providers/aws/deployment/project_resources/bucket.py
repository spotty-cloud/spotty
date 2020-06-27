import boto3
import re
from spotty.providers.aws.errors.bucket_not_found import BucketNotFoundError
from spotty.utils import random_string


class BucketResource(object):

    def __init__(self, project_name: str, region: str):
        self._s3 = boto3.client('s3', region_name=region)
        self._region = region
        self._bucket_prefix = 'spotty-%s' % project_name.lower()

    def get_bucket(self) -> str:
        res = self._s3.list_buckets()
        regex = re.compile('-'.join([self._bucket_prefix, '[a-z0-9]{12}', self._region]))
        buckets = [bucket['Name'] for bucket in res['Buckets'] if regex.match(bucket['Name']) is not None]

        if len(buckets) > 1:
            raise ValueError('Found several buckets in the same region: %s.' % ', '.join(buckets))

        if not len(buckets):
            raise BucketNotFoundError

        bucket_name = buckets[0]

        return bucket_name

    def create_bucket(self) -> str:
        bucket_name = '-'.join([self._bucket_prefix, random_string(12), self._region])

        # a fix for the boto3 issue: https://github.com/boto/boto3/issues/125
        if self._region == 'us-east-1':
            self._s3.create_bucket(ACL='private', Bucket=bucket_name)
        else:
            self._s3.create_bucket(ACL='private', Bucket=bucket_name,
                                   CreateBucketConfiguration={'LocationConstraint': self._region})

        return bucket_name

    def delete_bucket(self):
        pass
