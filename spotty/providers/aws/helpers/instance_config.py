from collections import namedtuple, OrderedDict
import boto3
import os
from spotty.config.container_config import ContainerConfig
from spotty.providers.aws.helpers.spot_prices import get_current_spot_price
from spotty.providers.aws.helpers.volume_config import VolumeConfig
from spotty.providers.aws.project_resources.bucket import BucketResource
from spotty.providers.aws.project_resources.key_pair import KeyPairResource
from spotty.providers.aws.resources.image import Image
from spotty.providers.aws.resources.subnet import Subnet
from spotty.providers.aws.resources.vpc import Vpc
from spotty.providers.aws.validation import validate_aws_instance_parameters
from spotty.utils import random_string

VolumeMount = namedtuple('VolumeMount', ['name', 'host_dir', 'container_dir'])


class InstanceConfig(object):

    def __init__(self, instance_name: str, instance_params: dict, project_name: str, container_config: dict):
        # validate instance configuration
        self._params = validate_aws_instance_parameters(instance_params)

        self._ec2 = boto3.client('ec2', region_name=self.region)

        # volume configs
        self._volumes = [VolumeConfig(self._ec2, volume['name'], volume['parameters'], project_name, instance_name)
                         for volume in self._params['volumes']]

        # container config
        self._container = ContainerConfig(container_config)

        # get container volumes and host project directory
        self._volume_mounts, self._host_project_dir = self._get_volume_mounts(self._volumes)

        self._name = instance_name
        self._project_name = project_name

    @property
    def region(self) -> str:
        return self._params['region']

    @property
    def availability_zone(self) -> str:
        return self._params['availabilityZone']

    @property
    def subnet_id(self) -> str:
        return self._params['subnetId']

    @property
    def instance_type(self) -> str:
        return self._params['instanceType']

    @property
    def max_price(self) -> float:
        return self._params['maxPrice']

    @property
    def volumes(self):
        return self._volumes

    @property
    def container(self) -> ContainerConfig:
        return self._container

    @property
    def on_demand(self) -> bool:
        return self._params['onDemandInstance']

    @property
    def ami_name(self) -> str:
        return self._params['amiName']

    @property
    def root_volume_size(self) -> int:
        return self._params['rootVolumeSize']

    @property
    def docker_data_root(self) -> str:
        return self._params['dockerDataRoot']

    @property
    def local_ssh_port(self) -> int:
        return self._params['localSshPort']

    @property
    def ec2_instance_name(self) -> str:
        return '%s-%s' % (self._project_name, self._name)

    @property
    def bucket(self) -> BucketResource:
        return BucketResource(self._project_name, self.region)

    @property
    def key_pair(self) -> KeyPairResource:
        return KeyPairResource(self._project_name, self.region)

    @property
    def dockerfile_path(self):
        """Dockerfile path on the host OS."""
        dockerfile_path = self.container.file
        if dockerfile_path:
            dockerfile_path = self.host_project_dir + '/' + dockerfile_path

        return dockerfile_path

    @property
    def docker_context_path(self):
        """Docker build's context path on the host OS."""
        dockerfile_path = self.dockerfile_path
        if not dockerfile_path:
            return ''

        return os.path.dirname(dockerfile_path)

    @property
    def host_project_dir(self):
        return self._host_project_dir

    @property
    def volume_mounts(self):
        return self._volume_mounts

    def get_ami(self) -> Image:
        return Image.get_by_name(self._ec2, self.ami_name)

    def get_vpc_id(self) -> str:
        if self.subnet_id:
            vpc_id = Subnet.get_by_id(self._ec2, self.subnet_id)['VpcId']
        else:
            default_vpc = Vpc.get_default_vpc(self._ec2)
            if not default_vpc:
                raise ValueError('Default VPC not found')

            vpc_id = default_vpc.vpc_id

        return vpc_id

    def check_az_and_subnet(self):
        # get all availability zones for the region
        zones = self._ec2.describe_availability_zones()
        zone_names = [zone['ZoneName'] for zone in zones['AvailabilityZones']]

        # check availability zone
        if self.availability_zone and self.availability_zone not in zone_names:
            raise ValueError('Availability zone "%s" doesn\'t exist in the "%s" region.'
                             % (self.availability_zone, self.region))

        if self.availability_zone:
            if self.subnet_id:
                subnet = Subnet.get_by_id(self._ec2, self.subnet_id)
                if not subnet:
                    raise ValueError('Subnet "%s" not found.' % self.subnet_id)

                if subnet.availability_zone != self.availability_zone:
                    raise ValueError('Availability zone of the subnet doesn\'t match the specified availability zone')
            else:
                default_subnets = Subnet.get_default_subnets(self._ec2)
                default_subnet = [subnet for subnet in default_subnets
                                  if subnet.availability_zone == self.availability_zone]
                if not default_subnet:
                    raise ValueError('Default subnet for the "%s" availability zone not found.\n'
                                     'Use the "subnetId" parameter to specify a subnet for this availability zone.'
                                     % self.availability_zone)
        else:
            if self.subnet_id:
                raise ValueError('An availability zone should be specified if a custom subnet is used.')
            else:
                default_subnets = Subnet.get_default_subnets(self._ec2)
                default_azs = {subnet.availability_zone for subnet in default_subnets}
                zones_wo_subnet = [zone_name for zone_name in zone_names if zone_name not in default_azs]
                if zones_wo_subnet:
                    raise ValueError('Default subnets for the following availability zones were not found: %s.\n'
                                     'Use "subnetId" and "availabilityZone" parameters or create missing default subnets.'
                                     % ', '.join(zones_wo_subnet))

    def check_max_price(self):
        if not self.on_demand and self.max_price:
            availability_zone = self.get_volumes_az()
            current_price = get_current_spot_price(self._ec2, self.instance_type, availability_zone)
            if current_price > self.max_price:
                raise ValueError('Current price for the instance (%.04f) is higher than the maximum price in the '
                                 'configuration file (%.04f).' % (current_price, self.max_price))

    def _get_volume_mounts(self, volumes: list):
        """Get container volume mounts."""
        # get mount directories for the volumes
        mount_dirs = OrderedDict([(volume.name, volume.mount_dir) for volume in volumes])

        # get container volumes mapping
        volume_mounts = []
        for container_mount in self.container.volume_mounts:
            container_dir = container_mount['path']
            if container_dir in mount_dirs:
                host_dir = mount_dirs[container_mount['name']]
            else:
                host_dir = '/tmp/spotty/volumes/%s-%s' % (container_mount['name'], random_string(8))

            volume_mounts.append(VolumeMount(
                name=container_mount['name'],
                host_dir=host_dir,
                container_dir=container_dir,
            ))

        # get project directory
        host_project_dir = None
        for name, host_dir, container_dir in volume_mounts:
            if (self.container.project_dir + '/').startswith(container_dir + '/'):
                project_subdir = os.path.relpath(self.container.project_dir, container_dir)
                host_project_dir = host_dir + '/' + project_subdir
                break

        if not host_project_dir:
            # use temporary directory for the project
            host_project_dir = '/tmp/spotty/volumes/project-%s' % random_string(8)
            volume_mounts.append(VolumeMount(
                name=None,
                host_dir=host_project_dir,
                container_dir=self.container.project_dir,
            ))

        return volume_mounts, host_project_dir

    def get_volumes_az(self):
        """Checks that existing volumes located in the same AZ and
           the AZ from the config file matches volumes AZ.
           Returns the final AZ where the instance should be run or empty string
           if the instance can be run in any AZ.
        """
        availability_zone = self.availability_zone
        for volume in self._volumes:
            ec2_volume = volume.get_ec2_volume()
            if ec2_volume:
                if availability_zone and (availability_zone != ec2_volume.availability_zone):
                    raise ValueError(
                        'The availability zone in the configuration file doesn\'t match the availability zone '
                        'of the existing volume or you have two existing volumes in different availability '
                        'zones.')

                # update availability zone
                availability_zone = ec2_volume.availability_zone

        return availability_zone
