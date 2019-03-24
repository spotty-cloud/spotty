import boto3
import re
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.utils import random_string


class BucketResource(object):

    def __init__(self, project_name: str, region: str):
        self._s3 = boto3.client('s3', region_name=region)
        self._region = region
        self._bucket_prefix = 'spotty-%s' % project_name.lower()

    def _find_bucket(self):
        res = self._s3.list_buckets()
        regex = re.compile('-'.join([self._bucket_prefix, '[a-z0-9]{12}', self._region]))
        buckets = [bucket['Name'] for bucket in res['Buckets'] if regex.match(bucket['Name']) is not None]

        if len(buckets) > 1:
            raise ValueError('Found several buckets in the same region: %s.' % ', '.join(buckets))

        bucket_name = buckets[0] if len(buckets) else False

        return bucket_name

    def get_or_create_bucket(self, output: AbstractOutputWriter, dry_run=False):
        bucket_name = self._find_bucket()
        if not bucket_name:
            bucket_name = '-'.join([self._bucket_prefix, random_string(12), self._region])
            if not dry_run:
                self._s3.create_bucket(ACL='private', Bucket=bucket_name,
                                       CreateBucketConfiguration={'LocationConstraint': self._region})
            output.write('Bucket "%s" was created.' % bucket_name)

        return bucket_name

    def delete_bucket(self):
        pass
