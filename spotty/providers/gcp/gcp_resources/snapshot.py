from spotty.providers.gcp.helpers.ce_client import CEClient


class Snapshot(object):

    def __init__(self, data: dict):
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
