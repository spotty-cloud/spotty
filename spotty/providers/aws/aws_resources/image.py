class Image(object):

    def __init__(self, ec2, ami_info):
        self._ec2 = ec2
        self._ami_info = ami_info

    @staticmethod
    def get_by_name(ec2, ami_name: str):
        """Returns a AMI by its name."""
        res = ec2.describe_images(Owners=['self'], Filters=[
            {'Name': 'name', 'Values': [ami_name]},
        ])

        if len(res['Images']) > 1:
            raise ValueError('Several AMIs use the same name: "%s".' % ami_name)

        if not len(res['Images']):
            return None

        return Image(ec2, res['Images'][0])

    @staticmethod
    def get_by_id(ec2, ami_id: str):
        """Returns a AMI by its ID."""
        res = ec2.describe_images(Filters=[{'Name': 'image-id', 'Values': [ami_id]}])

        if not len(res['Images']):
            return None

        return Image(ec2, res['Images'][0])

    @property
    def image_id(self) -> str:
        return self._ami_info['ImageId']

    @property
    def name(self) -> str:
        return self._ami_info['Name']

    @property
    def size(self) -> int:
        return self._ami_info['BlockDeviceMappings'][0]['Ebs']['VolumeSize']

    def get_tag_value(self, tag_name):
        tag_values = [tag['Value'] for tag in self._ami_info['Tags'] if tag['Key'] == tag_name]
        if not tag_values:
            return None

        return tag_values[0]
