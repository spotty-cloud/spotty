from spotty.providers.aws.aws_resources.snapshot import Snapshot


class Volume(object):

    def __init__(self, ec2, volume_info):
        self._ec2 = ec2
        self._volume_info = volume_info

    @staticmethod
    def get_by_name(ec2, volume_name: str):
        """Returns a volume by its name."""
        res = ec2.describe_volumes(Filters=[
            {'Name': 'tag:Name', 'Values': [volume_name]},
        ])

        if len(res['Volumes']) > 1:
            raise ValueError('Several volumes with Name=%s found.' % volume_name)

        if not len(res['Volumes']):
            return None

        return Volume(ec2, res['Volumes'][0])

    @property
    def name(self) -> str:
        volume_name = [tag['Value'] for tag in self._volume_info['Tags'] if tag['Key'] == 'Name']
        if not volume_name:
            return ''

        return volume_name[0]

    @property
    def volume_id(self) -> str:
        return self._volume_info['VolumeId']

    @property
    def size(self) -> int:
        return self._volume_info['Size']

    @property
    def availability_zone(self) -> str:
        return self._volume_info['AvailabilityZone']

    def is_available(self):
        return self._volume_info['State'] == 'available'

    def create_snapshot(self) -> Snapshot:
        snapshot_info = self._ec2.create_snapshot(
            VolumeId=self._volume_info['VolumeId'],
            TagSpecifications=[{
                'ResourceType': 'snapshot',
                'Tags': [{
                    'Key': 'Name',
                    'Value': self.name,
                }],
            }],
        )

        return Snapshot(self._ec2, snapshot_info)

    def delete(self):
        return self._ec2.delete_volume(VolumeId=self._volume_info['VolumeId'])
