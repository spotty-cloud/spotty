class Vpc(object):

    def __init__(self, ec2, vpc_info):
        self._ec2 = ec2
        self._vpc_info = vpc_info

    @staticmethod
    def get_default_vpc(ec2):
        """Returns a default VPC."""
        res = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
        if not len(res['Vpcs']):
            return None

        return Vpc(ec2, res['Vpcs'][0])

    @property
    def vpc_id(self) -> str:
        return self._vpc_info['VpcId']
