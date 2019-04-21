from spotty.providers.gcp.helpers.ce_client import CEClient


class Disk(object):

    def __init__(self, data: dict):
        self._data = data

    @staticmethod
    def get_by_name(ce: CEClient, disk_name: str):
        """Returns a disk by its name."""
        res = ce.list_disks(disk_name)
        if not res:
            return None

        return Disk(res[0])

    @property
    def name(self) -> str:
        return self._data['name']
