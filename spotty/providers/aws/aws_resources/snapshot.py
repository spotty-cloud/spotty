import time


class Snapshot(object):

    def __init__(self, ec2, snapshot_info):
        self._ec2 = ec2
        self._snapshot_info = snapshot_info

    @staticmethod
    def get_by_name(ec2, snapshot_name: str):
        """Returns a snapshot by its name."""
        res = ec2.describe_snapshots(Filters=[
            {'Name': 'tag:Name', 'Values': [snapshot_name]},
        ])

        if len(res['Snapshots']) > 1:
            raise ValueError('Several snapshots with Name=%s found.' % snapshot_name)

        if not len(res['Snapshots']):
            return None

        return Snapshot(ec2, res['Snapshots'][0])

    @property
    def name(self) -> str:
        snapshot_name = [tag['Value'] for tag in self._snapshot_info['Tags'] if tag['Key'] == 'Name']
        if not snapshot_name:
            return ''

        return snapshot_name[0]

    @property
    def snapshot_id(self):
        return self._snapshot_info['SnapshotId']

    @property
    def size(self) -> int:
        return self._snapshot_info['VolumeSize']

    @property
    def creation_time(self) -> int:
        return int(time.mktime(self._snapshot_info['StartTime'].timetuple()))

    def rename(self, new_name):
        return self._ec2.create_tags(Resources=[self.snapshot_id],
                                     Tags=[{'Key': 'Name', 'Value': new_name}])

    def delete(self):
        return self._ec2.delete_snapshot(SnapshotId=self.snapshot_id)

    def wait_snapshot_completed(self):
        waiter = self._ec2.get_waiter('snapshot_completed')
        waiter.wait(SnapshotIds=[self.snapshot_id])
