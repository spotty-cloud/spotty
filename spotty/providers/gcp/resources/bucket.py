from spotty.deployment.abstract_cloud_instance.resources.abstract_bucket import AbstractBucket
from google.cloud.storage import Bucket as GSBucket


class Bucket(AbstractBucket):

    def __init__(self, bucket: GSBucket):
        self._bucket = bucket

    @property
    def name(self) -> str:
        return self._bucket.name
