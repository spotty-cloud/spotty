from typing import List
from google.cloud import storage
from google.cloud.storage import Bucket


class GSClient(object):
    """Google Storage client."""

    def __init__(self):
        self._client = storage.Client()

    def list_buckets(self) -> List[Bucket]:
        res = list(self._client.list_buckets())
        return res

    def create_bucket(self, bucket_name: str, region: str) -> Bucket:
        bucket = Bucket(self._client, name=bucket_name)
        bucket.create(location=region)

        return bucket

    def create_dir(self, bucket_name: str, path: str):
        bucket = Bucket(self._client, name=bucket_name)
        blob = bucket.blob(path.rstrip('/') + '/')
        blob.upload_from_string('')
