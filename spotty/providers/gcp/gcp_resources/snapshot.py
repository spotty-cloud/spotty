from spotty.providers.gcp.helpers.ce_client import CEClient


class Snapshot(object):

    def __init__(self, data: dict):
        """
        Args:
            data (dict): Example:
               {'creationTimestamp': '2019-04-20T12:40:13.291-07:00',
                'diskSizeGb': '10',
                'id': '714587297862306675',
                'kind': 'compute#snapshot',
                'labelFingerprint': '42WmSpB8rSM=',
                'name': 'snapshot-test',
                'selfLink': 'https://www.googleapis.com/compute/v1/projects/spotty-221422/global/snapshots/snapshot-test',
                'sourceDisk': 'https://www.googleapis.com/compute/v1/projects/spotty-221422/zones/us-east1-b/disks/disk-test',
                'sourceDiskId': '599723469887162882',
                'status': 'READY',
                'storageBytes': '0',
                'storageBytesStatus': 'UP_TO_DATE',
                'storageLocations': ['us-central1']}
        """
        self._data = data

    @staticmethod
    def get_by_name(ce: CEClient, snapshot_name: str):
        """Returns a snapshot by its name."""
        res = ce.list_snapshots(snapshot_name)
        if not res:
            return None

        return Snapshot(res[0])

    @property
    def name(self) -> str:
        return self._data['name']

    @property
    def size(self) -> int:
        return self._data['diskSizeGb']

    @property
    def self_link(self) -> str:
        return self._data['selfLink']
