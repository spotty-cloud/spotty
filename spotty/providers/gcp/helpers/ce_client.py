from collections import OrderedDict
import googleapiclient.discovery


class CEClient(object):
    """Compute Engine client."""

    def __init__(self, project_id: str, zone: str):
        self._project_id = project_id
        self._zone = zone
        self._client = googleapiclient.discovery.build('compute', 'v1', cache_discovery=False)

    def list_images(self, image_name=None):
        filter_str = ('name=%s' % image_name) if image_name else None
        res = self._client.images().list(project=self._project_id, filter=filter_str).execute()

        if not res.get('items'):
            return []

        return res['items']

    def list_instances(self, machine_name=None):
        filter_str = ('name=%s' % machine_name) if machine_name else None
        res = self._client.instances().list(project=self._project_id, zone=self._zone, filter=filter_str).execute()

        if not res.get('items'):
            return []

        return res['items']

    def get_accelerator_types(self) -> OrderedDict:
        res = self._client.acceleratorTypes().list(project=self._project_id, zone=self._zone).execute()

        accelerator_types = OrderedDict([(item['name'], item['maximumCardsPerInstance']) for item in res['items']])

        return accelerator_types
