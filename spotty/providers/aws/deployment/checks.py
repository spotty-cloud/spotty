from spotty.providers.aws.aws_resources.subnet import Subnet
from spotty.providers.aws.helpers.spot_prices import get_current_spot_price


def check_az_and_subnet(ec2, region: str, availability_zone: str, subnet_id: str):
    # get all availability zones for the region
    zones = ec2.describe_availability_zones()
    zone_names = [zone['ZoneName'] for zone in zones['AvailabilityZones']]

    # check availability zone
    if availability_zone and availability_zone not in zone_names:
        raise ValueError('Availability zone "%s" doesn\'t exist in the "%s" region.'
                         % (availability_zone, region))

    if availability_zone:
        if subnet_id:
            subnet = Subnet.get_by_id(ec2, subnet_id)
            if not subnet:
                raise ValueError('Subnet "%s" not found.' % subnet_id)

            if subnet.availability_zone != availability_zone:
                raise ValueError('Availability zone of the subnet doesn\'t match the specified availability zone')
        else:
            default_subnets = Subnet.get_default_subnets(ec2)
            default_subnet = [subnet for subnet in default_subnets
                              if subnet.availability_zone == availability_zone]
            if not default_subnet:
                raise ValueError('Default subnet for the "%s" availability zone not found.\n'
                                 'Use the "subnetId" parameter to specify a subnet for this availability zone.'
                                 % availability_zone)
    else:
        if subnet_id:
            raise ValueError('An availability zone should be specified if a custom subnet is used.')
        else:
            default_subnets = Subnet.get_default_subnets(ec2)
            default_azs = {subnet.availability_zone for subnet in default_subnets}
            zones_wo_subnet = [zone_name for zone_name in zone_names if zone_name not in default_azs]
            if zones_wo_subnet:
                raise ValueError('Default subnets for the following availability zones were not found: %s.\n'
                                 'Use "subnetId" and "availabilityZone" parameters or create missing default '
                                 'subnets.' % ', '.join(zones_wo_subnet))


def check_max_price(ec2, instance_type: str, on_demand: bool, max_price: float, availability_zone: str = ''):
    """Checks that the specified maximum Spot price is less than the
    current Spot price.

    Args:
        ec2: EC2 client
        instance_type (str): Instance Type
        on_demand (bool): True if it's on-demand instance
        max_price (float): requested maximum price for the instance
        availability_zone (str): Availability zone to check. If it's an empty string,
            checks the cheapest AZ.

    Raises:
        ValueError: Current price for the instance is higher than the
            maximum price in the configuration file.
    """
    if not on_demand and max_price:
        current_price = get_current_spot_price(ec2, instance_type, availability_zone)
        if current_price > max_price:
            raise ValueError('Current price for the instance (%.04f) is higher than the maximum price in the '
                             'configuration file (%.04f).' % (current_price, max_price))
