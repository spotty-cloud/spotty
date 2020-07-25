from spotty.providers.aws.resources.subnet import Subnet


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
