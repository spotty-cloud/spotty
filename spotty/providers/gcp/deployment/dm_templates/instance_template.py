import os
from typing import List
import chevron
import pystache
import re
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.abstract_instance_volume import AbstractInstanceVolume
from spotty.deployment.container_deployment import ContainerDeployment
from spotty.providers.gcp.config.instance_config import InstanceConfig
from spotty.providers.gcp.deployment.project_resources.disk_volume import DiskVolume
from spotty.providers.gcp.helpers.sync import BUCKET_SYNC_DIR


def prepare_instance_template(instance_config: InstanceConfig, container: ContainerDeployment, sync_filters: list,
                              volumes: List[AbstractInstanceVolume], machine_name: str, bucket_name: str,
                              output: AbstractOutputWriter):
    """Prepares deployment template to run an instance."""

    # read and update the template
    with open(os.path.join(os.path.dirname(__file__), 'instance', 'template.yaml')) as f:
        template = f.read()

    # get disks
    disk_resources, disk_attachments, disk_device_names, disk_mount_dirs = _get_disks(volumes, output=output)

    # get Docker runtime parameters
    runtime_parameters = container.get_runtime_parameters(bool(instance_config.gpu))

    # render startup script
    startup_script = open(os.path.join(os.path.dirname(__file__), 'instance', 'cloud_init.yaml'), 'r').read()
    startup_script = pystache.render(startup_script, {
        'MACHINE_NAME': machine_name,
        'ZONE': instance_config.zone,
        'DISK_DEVICE_NAMES': ('"%s"' % '" "'.join(disk_device_names)) if disk_device_names else '',
        'DISK_MOUNT_DIRS': ('"%s"' % '" "'.join(disk_mount_dirs)) if disk_mount_dirs else '',
        'PROJECT_GS_BUCKET': bucket_name,
        'BUCKET_SYNC_DIR': BUCKET_SYNC_DIR,
        'HOST_PROJECT_DIR': container.host_project_dir,
        'DOCKER_DATA_ROOT_DIR': instance_config.docker_data_root,
        'DOCKER_IMAGE': container.config.image,
        'DOCKERFILE_PATH': container.dockerfile_path,
        'DOCKER_BUILD_CONTEXT_PATH': container.docker_context_path,
        'DOCKER_RUNTIME_PARAMS': runtime_parameters,
        'DOCKER_WORKING_DIR': container.config.working_dir,
    })

    indent_size = len(re.search('( *){{{STARTUP_SCRIPT}}}', template).group(1))
    startup_script = startup_script.replace('\n', '\n' + ' ' * indent_size)  # fix indent for the YAML file

    # render the template
    parameters = {
        'SERVICE_ACCOUNT_EMAIL': 'spotty@spotty-221422.iam.gserviceaccount.com',
        'GCP_PROJECT_ID': instance_config.project_id,
        'ZONE': instance_config.zone,
        'MACHINE_TYPE': instance_config.machine_type,
        'SOURCE_IMAGE': instance_config.image_name,
        'STARTUP_SCRIPT': startup_script,
        'MACHINE_NAME': machine_name,
        'PREEMPTIBLE': 'false' if instance_config.on_demand else 'true',
        'GPU_TYPE': instance_config.gpu['type'] if instance_config.gpu else '',
        'GPU_COUNT': instance_config.gpu['count'] if instance_config.gpu else 0,
        'DISK_RESOURCES': disk_resources,
        'DISK_ATTACHMENTS': disk_attachments,
    }
    template = chevron.render(template, parameters)

    return template


def _get_disks(volumes: List[AbstractInstanceVolume], output: AbstractOutputWriter):
    disk_resources = []
    disk_attachments = []
    disk_device_names = []
    disk_mount_dirs = []

    # create and attach volumes
    for i, volume in enumerate(volumes):
        if isinstance(volume, DiskVolume):
            snapshot_link = False

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

                    snapshot_link = snapshot.self_link
                else:
                    # empty volume will be created, check that the size is specified
                    if not volume.size:
                        raise ValueError('Size for the new disk is required.')

                    if volume.size < 10:
                        raise ValueError('Size of a disk cannot be less than 10GB.')

                    output.write('- disk "%s" will be created' % volume.disk_name)

            # update template parameters
            device_name = 'disk-%d' % (i + 1)
            disk_device_names.append(device_name)
            disk_mount_dirs.append(volume.mount_dir)
            disk_resources.append({
                'VOLUME_NAME': volume.name,
                'DISK_SIZE': volume.size,
                'DISK_SNAPSHOT': snapshot_link,
            })
            disk_attachments.append({
                'VOLUME_NAME': volume.name,
                'DEVICE_NAME': device_name,
            })

    return disk_resources, disk_attachments, disk_device_names, disk_mount_dirs
