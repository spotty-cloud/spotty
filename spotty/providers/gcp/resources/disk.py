from spotty.providers.gcp.helpers.ce_client import CEClient


class Disk(object):

    def __init__(self, ce: CEClient, data: dict):
        """
        Args:
            data (dict): Example:
               {'creationTimestamp': '2019-04-20T16:21:49.579-07:00',
                'guestOsFeatures': [{'type': 'VIRTIO_SCSI_MULTIQUEUE'}],
                'id': '1546539587132069731',
                'kind': 'compute#disk',
                'labelFingerprint': '42WmSpB8rSM=',
                'lastAttachTimestamp': '2019-04-20T16:21:49.580-07:00',
                'licenseCodes': ['1000205'],
                'licenses': ['https://www.googleapis.com/compute/v1/projects/debian-cloud/global/licenses/debian-9-stretch'],
                'name': 'instance-1',
                'physicalBlockSizeBytes': '4096',
                'selfLink': 'https://www.googleapis.com/compute/v1/projects/spotty-221422/zones/us-east1-b/disks/instance-1',
                'sizeGb': '10',
                'sourceImage': 'https://www.googleapis.com/compute/v1/projects/debian-cloud/global/images/debian-9-stretch-v20190326',
                'sourceImageId': '6831652533131678657',
                'status': 'READY',
                'type': 'https://www.googleapis.com/compute/v1/projects/spotty-221422/zones/us-east1-b/diskTypes/pd-standard',
                'users': ['https://www.googleapis.com/compute/v1/projects/spotty-221422/zones/us-east1-b/instances/instance-1'],
                'zone': 'https://www.googleapis.com/compute/v1/projects/spotty-221422/zones/us-east1-b'}
        """
        self._ce = ce
        self._data = data

    @staticmethod
    def get_by_name(ce: CEClient, disk_name: str):
        """Returns a disk by its name."""
        res = ce.list_disks(disk_name)
        if not res:
            return None

        return Disk(ce, res[0])

    @property
    def name(self) -> str:
        return self._data['name']

    @property
    def status(self) -> str:
        return self._data['status']

    @property
    def size(self) -> int:
        return int(self._data['sizeGb'])

    @property
    def users(self) -> list:
        return self._data.get('users', [])

    def is_available(self):
        return (self.status == 'READY') and not self.users
