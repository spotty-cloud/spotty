from typing import List
from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.providers.aws.config.ebs_volume import EbsVolume
from spotty.providers.aws.resources.volume import Volume


def update_availability_zone(ec2, availability_zone: str, volumes: List[AbstractInstanceVolume]):
    """Checks that existing volumes located in the same AZ and the AZ from the
    config file matches volumes AZ.

    Args:
        ec2: EC2 boto3 client
        availability_zone: Availability Zone from the configuration.
        volumes: List of volume objects.

    Returns:
        The final AZ where the instance should be run or an empty string if
        the instance can be run in any AZ.

    Raises:
        ValueError: AZ in the config file doesn't match the AZs of the volumes or
            AZs of the volumes are different.
    """
    availability_zone = availability_zone
    for volume in volumes:
        if isinstance(volume, EbsVolume):
            ec2_volume = Volume.get_by_name(ec2, volume.ec2_volume_name)
            if ec2_volume:
                if availability_zone and (availability_zone != ec2_volume.availability_zone):
                    raise ValueError(
                        'The availability zone in the configuration file doesn\'t match the availability zone '
                        'of the existing volume or you have two existing volumes in different availability '
                        'zones.')

                # update availability zone
                availability_zone = ec2_volume.availability_zone

    return availability_zone
