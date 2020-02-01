from typing import List
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.project_config import ProjectConfig
from spotty.deployment.abstract_instance_volume import AbstractInstanceVolume
from spotty.helpers.print_info import render_volumes_info_table
from spotty.providers.gcp.config.instance_config import VOLUME_TYPE_DISK
from spotty.deployment.container_deployment import ContainerDeployment
from spotty.providers.gcp.deployment.abstract_gcp_deployment import AbstractGcpDeployment
from spotty.providers.gcp.deployment.project_resources.bucket import BucketResource
from spotty.providers.gcp.deployment.project_resources.disk_volume import DiskVolume
from spotty.providers.gcp.deployment.dm_templates.instance_template import prepare_instance_template
from spotty.providers.gcp.deployment.project_resources.instance_stack import InstanceStackResource
from spotty.providers.gcp.gcp_resources.image import Image
from spotty.providers.gcp.gcp_resources.instance import Instance
from spotty.providers.gcp.helpers.deployment import check_gpu_configuration
from spotty.providers.gcp.helpers.sync import sync_local_to_bucket


class InstanceDeployment(AbstractGcpDeployment):

    @property
    def machine_name(self) -> str:
        """Name of the Compute Engine instance."""
        return '%s-%s' % (self._project_name.lower(), self.instance_config.name.lower())

    @property
    def bucket(self) -> BucketResource:
        region = '-'.join(self.instance_config.zone.split('-')[:-1])
        return BucketResource(self._project_name, region)

    @property
    def stack(self) -> InstanceStackResource:
        return InstanceStackResource(self.machine_name, self._credentials.project_id, self.instance_config.zone)

    def get_instance(self):
        return Instance.get_by_name(self._ce, self.machine_name)

    def deploy(self, project_config: ProjectConfig, output: AbstractOutputWriter, dry_run=False):
        # remove the stack it it exists to make all the disks available
        stack = self.stack
        stack.delete_stack(output=output)

        # create or get existing bucket for the project
        bucket_name = self.bucket.get_or_create_bucket(output, dry_run)

        # sync the project with the bucket
        output.write('Syncing the project with the bucket...')
        sync_local_to_bucket(project_config.project_dir, bucket_name, project_config.sync_filters, dry_run)

        # check GPU configuration
        check_gpu_configuration(self._ce, self.instance_config.gpu)

        # get volumes
        volumes = self._get_volumes()
        if volumes:
            # create disks
            output.write('\nCreating disks...')
            with output.prefix('  '):
                self._create_disks(volumes, output=output, dry_run=dry_run)
            output.write('')

        # prepare Deployment Manager template
        output.write('Preparing the deployment template...')
        with output.prefix('  '):
            # get an image
            image = self._get_image()

            # get or create an SSH key
            public_key_value = self.ssh_key.get_public_key_value()

            container = ContainerDeployment(project_config.project_name, volumes, project_config.container)
            template = prepare_instance_template(self.instance_config, container, project_config.sync_filters, volumes,
                                                 self.machine_name, image.self_link, bucket_name, public_key_value,
                                                 self._credentials.service_account_email, output)
        output.write('')

        # print information about the volumes
        output.write('Volumes:\n%s\n' % render_volumes_info_table(container.volume_mounts, volumes))

        # create stack
        if not dry_run:
            stack.create_stack(template, output=output)

    def delete(self, output: AbstractOutputWriter):
        self.stack.delete_stack(output)

        # TODO: apply deletion policies

    def _get_volumes(self) -> List[AbstractInstanceVolume]:
        volumes = []
        for volume_config in self.instance_config.volumes:
            volume_type = volume_config['type']
            if volume_type == VOLUME_TYPE_DISK:
                volumes.append(DiskVolume(self._ce, volume_config, self._project_name, self.instance_config.name))
            else:
                raise ValueError('GCP volume type "%s" not supported.' % volume_type)

        return volumes

    def _create_disks(self, volumes: List[AbstractInstanceVolume], output: AbstractOutputWriter, dry_run: bool = False):
        disks_to_create = []

        # do some checks and prepare disk parameters
        for i, volume in enumerate(volumes):
            if isinstance(volume, DiskVolume):
                # check if the disk already exists
                disk = volume.get_disk()
                if disk:
                    # check if the volume is available
                    if not disk.is_available():
                        raise ValueError('Disk "%s" is not available (status: %s).'
                                         % (volume.disk_name, disk.status))

                    # check size of the volume
                    if volume.size and (volume.size != disk.size):
                        raise ValueError('Specified size for the "%s" volume (%dGB) doesn\'t match the size of the '
                                         'existing disk (%dGB).' % (volume.name, volume.size, disk.size))

                    output.write('- disk "%s" will be attached' % disk.name)
                else:
                    # check if the snapshot exists
                    snapshot = volume.get_snapshot()
                    if snapshot:
                        # disk will be restored from the snapshot
                        # check size of the volume
                        if volume.size and (volume.size < snapshot.size):
                            raise ValueError('Specified size for the "%s" volume (%dGB) is less than size of the '
                                             'snapshot (%dGB).'
                                             % (volume.name, volume.size, snapshot.size))

                        output.write('- disk "%s" will be restored from the snapshot' % volume.disk_name)

                        disks_to_create.append((volume.disk_name, volume.size, snapshot.self_link))
                    else:
                        # empty volume will be created, check that the size is specified
                        if not volume.size:
                            raise ValueError('Size for the new disk is required.')

                        if volume.size < 10:
                            raise ValueError('Size of a disk cannot be less than 10GB.')

                        disks_to_create.append((volume.disk_name, volume.size, None))

        # create disks
        for disk_name, disk_size, snapshot_link in disks_to_create:
            if not dry_run:
                self._ce.create_disk(disk_name, disk_size, snapshot_link)

            output.write('- disk "%s" was created' % disk_name)

    def _get_image(self) -> Image:
        """Returns an image that should be used for deployment.

        Raises:
            ValueError: If an image not found.
        """
        if self.instance_config.image_url:
            # get an image by its URL if the "imageUrl" parameter is specified
            image = Image.get_by_url(self._ce, self.instance_config.image_url)
            if not image:
                raise ValueError('Image "%s" not found.' % self.instance_config.image_url)
        else:
            # try to get an image by its name (if the "imageName" parameter is not specified, the default value is used)
            image = Image.get_by_name(self._ce, self.instance_config.image_name)
            if not image:
                if self.instance_config.has_image_name:
                    # if an image name was explicitly specified, but the image was not found, raise an error
                    raise ValueError('Image with the name "%s" was not found.' % self.instance_config.image_name)
                else:
                    # get the latest image from the "spotty-cloud" project
                    spotty_image_family_url = 'projects/spotty-cloud/global/images/family/spotty-1-2-5'
                    image = Image.get_by_url(self._ce, spotty_image_family_url)
                    if not image:
                        raise ValueError('Image "%s" not found.\n'
                                         'Use the "spotty gcp create-image" command to create an image with NVIDIA '
                                         'Docker.' % spotty_image_family_url)

        return image
