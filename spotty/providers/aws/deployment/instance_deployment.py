from subprocess import list2cmdline
from typing import List
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.project_config import ProjectConfig
from spotty.config.validation import is_subdir
from spotty.deployment.abstract_instance_volume import AbstractInstanceVolume
from spotty.providers.aws.config.instance_config import VOLUME_TYPE_EBS
from spotty.deployment.container_deployment import ContainerDeployment, VolumeMount
from spotty.providers.aws.deployment.abstract_aws_deployment import AbstractAwsDeployment
from spotty.providers.aws.deployment.checks import check_az_and_subnet, check_max_price
from spotty.providers.aws.deployment.project_resources.ebs_volume import EbsVolume
from spotty.providers.aws.deployment.cf_templates.instance_template import prepare_instance_template
from spotty.providers.aws.errors.ami_not_found import AmiNotFoundError
from spotty.providers.aws.helpers.download import get_tmp_instance_s3_path
from spotty.providers.aws.helpers.sync import sync_project_with_s3, get_project_s3_path, get_instance_sync_arguments
from spotty.providers.aws.deployment.project_resources.bucket import BucketResource
from spotty.providers.aws.deployment.project_resources.instance_profile_stack import create_or_update_instance_profile
from spotty.providers.aws.deployment.project_resources.instance_stack import InstanceStackResource
from spotty.providers.aws.config.validation import is_nitro_instance, is_gpu_instance
from spotty.utils import render_table


class InstanceDeployment(AbstractAwsDeployment):

    @property
    def ec2_instance_name(self) -> str:
        return '%s-%s' % (self._project_name.lower(), self.instance_config.name.lower())

    @property
    def bucket(self) -> BucketResource:
        return BucketResource(self._project_name, self.instance_config.region)

    @property
    def stack(self) -> InstanceStackResource:
        return InstanceStackResource(self._project_name, self.instance_config.name, self.instance_config.region)

    def get_instance(self):
        return self.stack.get_instance()

    def deploy(self, project_config: ProjectConfig, output: AbstractOutputWriter, dry_run=False):
        # check that it's not a Nitro-based instance
        if is_nitro_instance(self.instance_config.instance_type):
            raise ValueError('Currently Nitro-based instances are not supported.')

        # check availability zone and subnet configuration
        check_az_and_subnet(self._ec2, self.instance_config.region, self.instance_config.availability_zone,
                            self.instance_config.subnet_id)

        # get volumes
        volumes = self._get_volumes()

        # get deployment availability zone
        availability_zone = self._get_availability_zone(volumes)

        # check the maximum price for a spot instance
        check_max_price(self._ec2, self.instance_config.instance_type, self.instance_config.on_demand,
                        self.instance_config.max_price, availability_zone)

        # create or get existing bucket for the project
        bucket_name = self.bucket.get_or_create_bucket(output, dry_run)

        # sync the project with the bucket
        output.write('Syncing the project with S3 bucket...')
        sync_project_with_s3(project_config.project_dir, bucket_name, self.instance_config.region,
                             project_config.sync_filters, dry_run)

        # create or update instance profile
        if not dry_run:
            instance_profile_arn = create_or_update_instance_profile(self.instance_config.region, output)
        else:
            instance_profile_arn = None

        output.write('Preparing CloudFormation template...')

        # prepare CloudFormation template
        container = ContainerDeployment(project_config.project_name, volumes, project_config.container)
        with output.prefix('  '):
            template = prepare_instance_template(self.instance_config, volumes, availability_zone, container,
                                                 output)

            # get parameters for the template
            parameters = self._get_template_parameters(instance_profile_arn, self.instance_config.name, bucket_name,
                                                       project_config.sync_filters, volumes, container, output,
                                                       dry_run=dry_run)

        # print information about the volumes
        output.write('\nVolumes:\n%s\n' % self._render_volumes_info_table(container.volume_mounts, volumes))

        # create stack
        if not dry_run:
            self.stack.create_or_update_stack(template, parameters, output)

    def _get_availability_zone(self, volumes: List[AbstractInstanceVolume]):
        """Checks that existing volumes located in the same AZ and the AZ from the
        config file matches volumes AZ.

        Args:
            volumes: List of volume objects.

        Returns:
            The final AZ where the instance should be run or an empty string if
            the instance can be run in any AZ.

        Raises:
            ValueError: AZ in the config file doesn't match the AZs of the volumes or
                AZs of the volumes are different.
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

    def _get_template_parameters(self, instance_profile_arn: str, instance_name: str, bucket_name: str,
                                 sync_filters: list, volumes: List[AbstractInstanceVolume],
                                 container: ContainerDeployment, output: AbstractOutputWriter, dry_run=False):
        # get VPC ID
        vpc_id = self.get_vpc_id()

        # get image info
        ami = self.get_ami()
        if not ami:
            raise AmiNotFoundError(self.instance_config.ami_name)

        # check root volume size
        root_volume_size = self.instance_config.root_volume_size
        if root_volume_size and root_volume_size < ami.size:
            raise ValueError('Root volume size cannot be less than the size of AMI (%dGB).' % ami.size)
        elif not root_volume_size:
            # if a root volume size is not specified, make it 5GB larger than the AMI size
            root_volume_size = ami.size + 5

        # create key pair
        key_name = self.key_pair.get_or_create_key(dry_run)

        # get mount directories for the volumes
        mount_dirs = [volume.mount_dir for volume in volumes]

        # get Docker runtime parameters
        runtime_parameters = container.get_runtime_parameters(is_gpu_instance(self.instance_config.instance_type))

        # print info about the Docker data root
        if self.instance_config.docker_data_root:
            docker_data_volume_name = [volume.name for volume in volumes
                                       if is_subdir(self.instance_config.docker_data_root, volume.mount_dir)][0]
            output.write('- Docker data will be stored on the "%s" volume' % docker_data_volume_name)

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
            'DockerRuntimeParameters': runtime_parameters,
            'DockerWorkingDirectory': container.config.working_dir,
            'InstanceNameTag': self.ec2_instance_name,
            'ProjectS3Path': get_project_s3_path(bucket_name),
            'HostProjectDirectory': container.host_project_dir,
            'SyncCommandArgs': list2cmdline(get_instance_sync_arguments(sync_filters)),
            'UploadS3Path': get_tmp_instance_s3_path(bucket_name, instance_name),
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
            except Exception as e:
                output.write('- volume "%s" not found. Error: %s' % (volume.ec2_volume_name, str(e)))
                continue

            if not ec2_volume:
                output.write('- volume "%s" not found' % volume.ec2_volume_name)
                continue

            if not ec2_volume.is_available():
                output.write('- volume "%s" is not available' % volume.ec2_volume_name)
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
                    prev_snapshot = volume.get_snapshot()
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

    @staticmethod
    def _render_volumes_info_table(volume_mounts: List[VolumeMount], volumes: List[AbstractInstanceVolume]):
        table = [('Name', 'Container Dir', 'Type', 'Deletion Policy')]

        # add volume mounts to the info table
        volumes_dict = {volume.name: volume for volume in volumes}
        for volume_mount in volume_mounts:
            if volume_mount.name in volumes_dict:
                # the volume will be mounted to the container
                volume = volumes_dict[volume_mount.name]
                deletion_policy = volume.deletion_policy_title if volume.deletion_policy_title else '-'
                table.append((volume_mount.name, volume_mount.container_dir, volume.title, deletion_policy))
            else:
                # a temporary directory will be mounted to the container
                vol_mount_name = '-' if volume_mount.name is None else volume_mount.name
                table.append((vol_mount_name, volume_mount.container_dir, 'temporary directory', '-'))

        # add volumes that were not mounted to the container to the info table
        volume_mounts_dict = {volume_mount.name for volume_mount in volume_mounts}
        for volume in volumes:
            if volume.name not in volume_mounts_dict:
                deletion_policy = volume.deletion_policy_title if volume.deletion_policy_title else '-'
                table.append((volume.name, '-', volume.title, deletion_policy))

        return render_table(table, separate_title=True)
