class Subnet(object):

    def __init__(self, ec2, subnet_info):
        self._ec2 = ec2
        self._subnet_info = subnet_info

    @staticmethod
    def get_by_id(ec2, subnet_id: str):
        """Returns a subnet by its ID."""
        res = ec2.describe_subnets(Filters=[
            {'Name': 'subnet-id', 'Values': [subnet_id]},
        ])

        if not len(res['Subnets']):
            return None

        return Subnet(ec2, res['Subnets'][0])

    @staticmethod
    def get_default_subnets(ec2):
        res = ec2.describe_subnets(Filters=[
            {'Name': 'defaultForAz', 'Values': ['true']},
        ])

        subnets = [Subnet(ec2, subnet_info) for subnet_info in res['Subnets']]

        return subnets

    @property
    def availability_zone(self) -> str:
        return self._subnet_info['AvailabilityZone']

    @property
    def vpc_id(self) -> str:
        return self._subnet_info['VpcId']
