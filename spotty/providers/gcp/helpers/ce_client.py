from collections import OrderedDict
import googleapiclient.discovery


class CEClient(object):
    """Compute Engine client."""

    def __init__(self, project_id: str, zone: str):
        self._project_id = project_id
        self._zone = zone
        self._client = googleapiclient.discovery.build('compute', 'v1', cache_discovery=False)

    @property
    def zone(self):
        return self._zone

    def list_images(self, image_name: str = None, project_id: str = None):
        """Returns a list of images that satisfy the name.
            This method is used instead of the "get" because it doesn't raise an exception if an image doesn't exist.
        """
        if not project_id:
            project_id = self._project_id

        filter_str = ('name=%s' % image_name) if image_name else None
        res = self._client.images().list(project=project_id, filter=filter_str).execute()

        if not res.get('items'):
            return []

        return res['items']

    def get_image_from_family(self, family_name: str, project_id: str = None):
        if not project_id:
            project_id = self._project_id

        res = self._client.images().getFromFamily(project=project_id, family=family_name).execute()

        return res

    def list_instances(self, machine_name=None):
        filter_str = ('name=%s' % machine_name) if machine_name else None
        res = self._client.instances().list(project=self._project_id, zone=self._zone, filter=filter_str).execute()

        if not res.get('items'):
            return []

        return res['items']

    def list_disks(self, disk_name=None):
        filter_str = ('name=%s' % disk_name) if disk_name else None
        res = self._client.disks().list(project=self._project_id, zone=self._zone, filter=filter_str).execute()

        if not res.get('items'):
            return []

        return res['items']

    def list_snapshots(self, snapshot_name=None):
        filter_str = ('name=%s' % snapshot_name) if snapshot_name else None
        res = self._client.snapshots().list(project=self._project_id, filter=filter_str).execute()

        if not res.get('items'):
            return []

        return res['items']

    def get_accelerator_types(self) -> OrderedDict:
        res = self._client.acceleratorTypes().list(project=self._project_id, zone=self._zone).execute()
        accelerator_types = OrderedDict([(item['name'], item['maximumCardsPerInstance'])
                                         for item in res.get('items', [])])

        return accelerator_types

    def create_disk(self, name: str, size: int = None, snapshot_link: str = None) -> str:
        params = {
            'name': name,
            'type': 'zones/%s/diskTypes/pd-standard' % self._zone,
            'physicalBlockSizeBytes': 4096,
        }

        if size:
            params['sizeGb'] = size

        if snapshot_link:
            params['sourceSnapshot'] = snapshot_link

        res = self._client.disks().insert(project=self._project_id, zone=self._zone, body=params).execute()

        return res['targetLink']
