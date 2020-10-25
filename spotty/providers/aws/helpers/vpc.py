from spotty.providers.aws.resources.subnet import Subnet
from spotty.providers.aws.resources.vpc import Vpc


def get_vpc_id(ec2, subnet_id: str = None) -> str:
    """Returns VPC ID that should be used for deployment."""
    if subnet_id:
        vpc_id = Subnet.get_by_id(ec2, subnet_id).vpc_id
    else:
        default_vpc = Vpc.get_default_vpc(ec2)
        if not default_vpc:
            raise ValueError('Default VPC not found')

        vpc_id = default_vpc.vpc_id

    return vpc_id
