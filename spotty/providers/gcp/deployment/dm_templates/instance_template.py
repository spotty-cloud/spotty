import os
from subprocess import list2cmdline
from typing import List
import chevron
import pystache
import re
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.abstract_instance_volume import AbstractInstanceVolume
from spotty.deployment.container_deployment import ContainerDeployment
from spotty.providers.gcp.config.instance_config import InstanceConfig
from spotty.providers.gcp.deployment.project_resources.disk_volume import DiskVolume
from spotty.providers.gcp.helpers.sync import BUCKET_SYNC_DIR, get_instance_sync_arguments


def prepare_instance_template(instance_config: InstanceConfig, container: ContainerDeployment, sync_filters: list,
                              volumes: List[AbstractInstanceVolume], machine_name: str, bucket_name: str,
                              public_key_value: str, service_account_email: str, output: AbstractOutputWriter):
    """Prepares deployment template to run an instance."""

    # read and update the template
    with open(os.path.join(os.path.dirname(__file__), 'instance', 'template.yaml')) as f:
        template = f.read()

    # get disk attachments
    disk_attachments, disk_device_names, disk_mount_dirs = _get_disk_attachments(volumes, instance_config.zone)

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
        'SYNC_ARGS': list2cmdline(get_instance_sync_arguments(sync_filters)),
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
        'SERVICE_ACCOUNT_EMAIL': service_account_email,
        'ZONE': instance_config.zone,
        'MACHINE_TYPE': instance_config.machine_type,
        'SOURCE_IMAGE': instance_config.image_name,
        'STARTUP_SCRIPT': startup_script,
        'MACHINE_NAME': machine_name,
        'PREEMPTIBLE': 'false' if instance_config.on_demand else 'true',
        'GPU_TYPE': instance_config.gpu['type'] if instance_config.gpu else '',
        'GPU_COUNT': instance_config.gpu['count'] if instance_config.gpu else 0,
        'DISK_ATTACHMENTS': disk_attachments,
        'PUB_KEY_VALUE': public_key_value,
        'PORTS': ', '.join([str(port) for port in set(container.config.ports + [22])]),
    }
    template = chevron.render(template, parameters)

    return template


def _get_disk_attachments(volumes: List[AbstractInstanceVolume], zone: str):
    disk_attachments = []
    disk_device_names = []
    disk_mount_dirs = []

    for i, volume in enumerate(volumes):
        if isinstance(volume, DiskVolume):
            device_name = 'disk-%d' % (i + 1)
            disk_device_names.append(device_name)
            disk_mount_dirs.append(volume.mount_dir)
            disk_attachments.append({
                'DISK_LINK': 'zones/%s/disks/%s' % (zone, volume.disk_name),
                'DEVICE_NAME': device_name,
            })

    return disk_attachments, disk_device_names, disk_mount_dirs
