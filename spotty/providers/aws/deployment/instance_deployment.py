from typing import List
import boto3
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.project_config import ProjectConfig
from spotty.deployment.abstract_instance_volume import AbstractInstanceVolume
from spotty.providers.aws.config.instance_config import InstanceConfig, VOLUME_TYPE_EBS
from spotty.deployment.container_deployment import ContainerDeployment
from spotty.providers.aws.deployment.cf_templates.ami_template import prepare_ami_template
from spotty.providers.aws.deployment.ebs_volume import EbsVolume
from spotty.providers.aws.deployment.cf_templates.instance_template import prepare_instance_template
from spotty.providers.aws.deployment.project_resources.ami_stack import AmiStackResource
from spotty.providers.aws.helpers.spot_prices import get_current_spot_price
from spotty.providers.aws.helpers.sync import sync_project_with_s3
from spotty.providers.aws.deployment.project_resources.bucket import BucketResource
from spotty.providers.aws.deployment.project_resources.instance_profile_stack import create_or_update_instance_profile
from spotty.providers.aws.deployment.project_resources.instance_stack import InstanceStackResource
from spotty.providers.aws.deployment.project_resources.key_pair import KeyPairResource
from spotty.providers.aws.aws_resources.image import Image
from spotty.providers.aws.aws_resources.subnet import Subnet
from spotty.providers.aws.aws_resources.vpc import Vpc
from spotty.providers.aws.config.validation import is_nitro_instance, is_gpu_instance


class InstanceDeployment(object):

    def __init__(self, project_name: str, instance_config: InstanceConfig):
        self._project_name = project_name
        self._instance_config = instance_config
        self._ec2 = boto3.client('ec2', region_name=instance_config.region)

    @property
    def instance_config(self):
        return self._instance_config

    @property
    def ec2_instance_name(self) -> str:
        return '%s-%s' % (self._project_name.lower(), self.instance_config.name.lower())

    @property
    def bucket(self) -> BucketResource:
        return BucketResource(self._project_name, self.instance_config.region)

    @property
    def key_pair(self) -> KeyPairResource:
        return KeyPairResource(self._project_name, self.instance_config.region)

    @property
    def instance_stack(self) -> InstanceStackResource:
        return InstanceStackResource(self._project_name, self.instance_config.name, self.instance_config.region)

    def get_ami(self) -> Image:
        return Image.get_by_name(self._ec2, self.instance_config.ami_name)

    def get_vpc_id(self) -> str:
        if self.instance_config.subnet_id:
            vpc_id = Subnet.get_by_id(self._ec2, self.instance_config.subnet_id)['VpcId']
        else:
            default_vpc = Vpc.get_default_vpc(self._ec2)
            if not default_vpc:
                raise ValueError('Default VPC not found')

            vpc_id = default_vpc.vpc_id

        return vpc_id

    def get_instance(self):
        return self.instance_stack.get_instance()

    def deploy(self, project_config: ProjectConfig, output: AbstractOutputWriter, dry_run=False):
        # check that it's not a Nitro-based instance
        if is_nitro_instance(self.instance_config.instance_type):
            raise ValueError('Currently Nitro-based instances are not supported.')

        # check availability zone and subnet configuration
        self._check_az_and_subnet()

        # get volumes
        volumes = self._get_volumes()

        # get deployment availability zone
        availability_zone = self._get_availability_zone(volumes)

        # check the maximum price for a spot instance
        self._check_max_price(availability_zone)

        # create or get existing bucket for the project
        bucket_name = self.bucket.get_or_create_bucket(output, dry_run)

        # sync the project with the bucket
        sync_project_with_s3(project_config.project_dir, bucket_name, self.instance_config.region,
                             project_config.sync_filters, dry_run)

        # create or update instance profile
        if not dry_run:
            instance_profile_arn = create_or_update_instance_profile(self.instance_config.region, output)

        output.write('Preparing CloudFormation template...')

        # prepare CloudFormation template
        container = ContainerDeployment(project_config.project_name, volumes, project_config.container)
        with output.prefix('  '):
            template = prepare_instance_template(self.instance_config, volumes, availability_zone, container,
                                                 output)

        # get parameters for the template
        parameters = self._get_instance_template_parameters(instance_profile_arn, bucket_name, volumes, container,
                                                            dry_run)

        # print container volumes
        output.write('\nContainer volumes:')
        with output.prefix('  '):
            volumes_dict = {volume.name: volume for volume in volumes}
            for volume_mount in container.volume_mounts:
                if volume_mount.name in volumes_dict:
                    volume = volumes_dict[volume_mount.name]
                    if isinstance(volume, EbsVolume):
                        output.write('%s -> EBS volume (%s)' % (volume_mount.container_dir, volume.ec2_volume_name))
                    else:
                        raise ValueError('Unknown volume type')
                else:
                    output.write('%s -> temporary directory' % volume_mount.container_dir)
        output.write()

        # create stack
        if not dry_run:
            self.instance_stack.create_or_update_stack(template, parameters, output)

    def create_ami(self, key_name, keep_instance: bool, output: AbstractOutputWriter):
        # check that it's a GPU instance type
        instance_type = self.instance_config.instance_type
        if not is_gpu_instance(instance_type):
            raise ValueError('"%s" is not a GPU instance' % instance_type)

        if keep_instance and not key_name:
            output.write('Key Pair name is not specified, you will not be able to connect to the instance.')

        # check that an image with this name doesn't exist yet
        ami = self.get_ami()
        if ami:
            raise ValueError('AMI with the name "%s" already exists.' % ami.name)

        # check availability zone and subnet
        self._check_az_and_subnet()

        # check the maximum price for a spot instance
        availability_zone = self.instance_config.availability_zone
        self._check_max_price(availability_zone)

        # prepare CF template
        subnet_id = self.instance_config.subnet_id
        on_demand = self.instance_config.on_demand
        template = prepare_ami_template(availability_zone, subnet_id, key_name, on_demand)

        # create stack
        ami_stack = AmiStackResource(self.instance_config.region)
        ami_name = self.instance_config.ami_name
        ami_stack.create_stack(template, instance_type, ami_name, key_name, keep_instance, output)

    def _check_az_and_subnet(self):
        # get all availability zones for the region
        zones = self._ec2.describe_availability_zones()
        zone_names = [zone['ZoneName'] for zone in zones['AvailabilityZones']]

        # check availability zone
        if self.instance_config.availability_zone and self.instance_config.availability_zone not in zone_names:
            raise ValueError('Availability zone "%s" doesn\'t exist in the "%s" region.'
                             % (self.instance_config.availability_zone, self.instance_config.region))

        if self.instance_config.availability_zone:
            if self.instance_config.subnet_id:
                subnet = Subnet.get_by_id(self._ec2, self.instance_config.subnet_id)
                if not subnet:
                    raise ValueError('Subnet "%s" not found.' % self.instance_config.subnet_id)

                if subnet.availability_zone != self.instance_config.availability_zone:
                    raise ValueError('Availability zone of the subnet doesn\'t match the specified availability zone')
            else:
                default_subnets = Subnet.get_default_subnets(self._ec2)
                default_subnet = [subnet for subnet in default_subnets
                                  if subnet.availability_zone == self.instance_config.availability_zone]
                if not default_subnet:
                    raise ValueError('Default subnet for the "%s" availability zone not found.\n'
                                     'Use the "subnetId" parameter to specify a subnet for this availability zone.'
                                     % self.instance_config.availability_zone)
        else:
            if self.instance_config.subnet_id:
                raise ValueError('An availability zone should be specified if a custom subnet is used.')
            else:
                default_subnets = Subnet.get_default_subnets(self._ec2)
                default_azs = {subnet.availability_zone for subnet in default_subnets}
                zones_wo_subnet = [zone_name for zone_name in zone_names if zone_name not in default_azs]
                if zones_wo_subnet:
                    raise ValueError('Default subnets for the following availability zones were not found: %s.\n'
                                     'Use "subnetId" and "availabilityZone" parameters or create missing default '
                                     'subnets.' % ', '.join(zones_wo_subnet))

    def _check_max_price(self, availability_zone=''):
        if not self.instance_config.on_demand and self.instance_config.max_price:
            current_price = get_current_spot_price(self._ec2, self.instance_config.instance_type, availability_zone)
            if current_price > self.instance_config.max_price:
                raise ValueError('Current price for the instance (%.04f) is higher than the maximum price in the '
                                 'configuration file (%.04f).' % (current_price, self.instance_config.max_price))

    def _get_availability_zone(self, volumes):
        """Checks that existing volumes located in the same AZ and
           the AZ from the config file matches volumes AZ.
           Returns the final AZ where the instance should be run or empty string
           if the instance can be run in any AZ.
        """
        availability_zone = self.instance_config.availability_zone
        for volume in volumes:
            if isinstance(volume, EbsVolume):
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

    def _get_volumes(self) -> List[AbstractInstanceVolume]:
        volumes = []
        for volume_config in self.instance_config.volumes:
            volume_type = volume_config['type']
            if volume_type == VOLUME_TYPE_EBS:
                volumes.append(EbsVolume(self._ec2, volume_config, self._project_name, self.instance_config.name))
            else:
                raise ValueError('AWS volume type "%s" not supported.' % volume_type)

        return volumes

    def _get_instance_template_parameters(self, instance_profile_arn: str, bucket_name: str,
                                          volumes: List[AbstractInstanceVolume], container: ContainerDeployment,
                                          dry_run=False):
        # get VPC ID
        vpc_id = self.get_vpc_id()

        # get image info
        ami = self.get_ami()
        if not ami:
            raise ValueError('AMI with name "%s" not found.\n'
                             'Use the "spotty aws create-ami" command to create an AMI with NVIDIA Docker.'
                             % self.instance_config.ami_name)

        # check root volume size
        root_volume_size = self.instance_config.root_volume_size
        if root_volume_size and root_volume_size < ami.size:
            raise ValueError('Root volume size cannot be less than the size of AMI (%dGB).' % ami.size)
        elif not root_volume_size:
            # if a root volume size is not specified, make it 5GB larger than the AMI size
            root_volume_size = ami.size + 5

        # create key pair
        key_name = self.key_pair.get_or_create_key(dry_run)

        # split container volumes mapping to two different lists
        docker_host_dirs = []
        docker_container_dirs = []
        for volume_mount in container.volume_mounts:
            docker_host_dirs.append(volume_mount.host_dir)
            docker_container_dirs.append(volume_mount.container_dir)

        # get mount directories for the volumes
        mount_dirs = [volume.mount_dir for volume in volumes]

        # create stack
        parameters = {
            'VpcId': vpc_id,
            'InstanceProfileArn': instance_profile_arn,
            'InstanceType': self.instance_config.instance_type,
            'KeyName': key_name,
            'ImageId': ami.image_id,
            'RootVolumeSize': str(root_volume_size),
            'VolumeMountDirectories': ('"%s"' % '" "'.join(mount_dirs)) if mount_dirs else '',
            'DockerDataRootDirectory': self.instance_config.docker_data_root,
            'DockerImage': container.config.image,
            'DockerfilePath': container.dockerfile_path,
            'DockerBuildContextPath': container.docker_context_path,
            'DockerNvidiaRuntime': 'true' if is_gpu_instance(self.instance_config.instance_type) else 'false',
            'DockerWorkingDirectory': container.config.working_dir,
            'DockerVolumesHostDirs': ('"%s"' % '" "'.join(docker_host_dirs)) if docker_host_dirs else '',
            'DockerVolumesContainerDirs': (
                        '"%s"' % '" "'.join(docker_container_dirs)) if docker_container_dirs else '',
            'InstanceNameTag': self.ec2_instance_name,
            'ProjectS3Bucket': bucket_name,
            'HostProjectDirectory': container.host_project_dir,
        }

        return parameters

    def apply_deletion_policies(self, output: AbstractOutputWriter):
        """Applies deletion policies to the EBS volumes."""
        wait_snapshots = []
        delete_snapshots = []
        delete_volumes = []

        # get volumes
        volumes = self._get_volumes()
        ebs_volumes = [volume for volume in volumes if isinstance(volume, EbsVolume)]

        # no volumes
        if not ebs_volumes:
            output.write('- no EBS volumes configured')
            return

        # apply deletion policies
        for volume in ebs_volumes:
            # get EC2 volume
            try:
                ec2_volume = volume.get_ec2_volume()
                if not ec2_volume:
                    output.write('- volume "%s" not found' % volume.ec2_volume_name)
                    continue
            except Exception as e:
                output.write('- volume "%s" not found. Error: %s' % (volume.ec2_volume_name, str(e)))
                continue

            # apply deletion policies
            if volume.deletion_policy == EbsVolume.DP_RETAIN:
                # do nothing
                output.write('- volume "%s" is retained' % ec2_volume.name)

            elif volume.deletion_policy == EbsVolume.DP_DELETE:
                # volume will be deleted later
                delete_volumes.append(ec2_volume)

            elif volume.deletion_policy == EbsVolume.DP_CREATE_SNAPSHOT \
                    or volume.deletion_policy == EbsVolume.DP_UPDATE_SNAPSHOT:
                try:
                    # rename or delete previous snapshot
                    prev_snapshot = volume.get_snapshot(from_volume_name=True)
                    if prev_snapshot:
                        # rename previous snapshot
                        if volume.deletion_policy == EbsVolume.DP_CREATE_SNAPSHOT:
                            prev_snapshot.rename('%s-%d' % (prev_snapshot.name, prev_snapshot.creation_time))

                        # once new snapshot will be created, the old one should be deleted
                        if volume.deletion_policy == EbsVolume.DP_UPDATE_SNAPSHOT:
                            delete_snapshots.append(prev_snapshot)

                    output.write('- creating snapshot for the volume "%s"...' % ec2_volume.name)

                    # create new snapshot
                    new_snapshot = ec2_volume.create_snapshot()
                    wait_snapshots.append((new_snapshot, ec2_volume))

                    # once the snapshot will be created, the volume should be deleted
                    delete_volumes.append(ec2_volume)
                except Exception as e:
                    output.write('- snapshot for the volume "%s" was not created. Error: %s'
                                 % (volume.ec2_volume_name, str(e)))

            else:
                raise ValueError('Unsupported deletion policy: "%s".' % volume.deletion_policy)

        # wait until all snapshots will be created
        for snapshot, ec2_volume in wait_snapshots:
            try:
                snapshot.wait_snapshot_completed()
                output.write('- snapshot for the volume "%s" was created' % snapshot.name)
            except Exception as e:
                output.write('- snapshot "%s" was not created. Error: %s' % (snapshot.name, str(e)))

        # delete old snapshots
        for snapshot in delete_snapshots:
            try:
                snapshot.delete()
                output.write('- previous snapshot "%s" was deleted' % snapshot.name)
            except Exception as e:
                output.write('- previous snapshot "%s" was not deleted. Error: %s' % (snapshot.name, str(e)))

        # delete volumes
        for ec2_volume in delete_volumes:
            try:
                ec2_volume.delete()
                output.write('- volume "%s" was deleted' % ec2_volume.name)
            except Exception as e:
                output.write('- volume "%s" was not deleted. Error: %s' % (ec2_volume.name, str(e)))
