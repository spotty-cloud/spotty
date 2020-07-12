from spotty.deployment.abstract_cloud_instance.resources.abstract_bucket import AbstractBucket


class Bucket(AbstractBucket):

    def __init__(self, data: dict):
        self._data = data

    @property
    def name(self) -> str:
        return self._data['Name']
