import re
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.gcp.helpers.gs_client import GSClient
from spotty.providers.gcp.helpers.sync import BUCKET_SYNC_DIR
from spotty.utils import random_string


class BucketResource(object):

    def __init__(self, project_name: str, region: str):
        self._gs = GSClient()
        self._region = region
        self._bucket_prefix = 'spotty-%s' % project_name.lower()

    def _find_bucket(self):
        buckets = self._gs.list_buckets()

        regex = re.compile('-'.join([self._bucket_prefix, '[a-z0-9]{12}', self._region]))
        bucket_names = [bucket.name for bucket in buckets if regex.match(bucket.name) is not None]

        if len(bucket_names) > 1:
            raise ValueError('Found several project buckets in the same region: %s.' % ', '.join(bucket_names))

        bucket_name = bucket_names[0] if len(bucket_names) else False

        return bucket_name

    def get_or_create_bucket(self, output: AbstractOutputWriter, dry_run=False):
        bucket_name = self._find_bucket()
        if not bucket_name:
            bucket_name = '-'.join([self._bucket_prefix, random_string(12), self._region])
            if not dry_run:
                self._gs.create_bucket(bucket_name, self._region)
                self._gs.create_dir(bucket_name, BUCKET_SYNC_DIR)

            output.write('Bucket "%s" was created.' % bucket_name)

        return bucket_name
