import os
from subprocess import list2cmdline
from typing import List
import chevron
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.validation import is_subdir
from spotty.deployment.abstract_instance_volume import AbstractInstanceVolume
from spotty.deployment.container_deployment import ContainerDeployment
from spotty.providers.gcp.config.instance_config import InstanceConfig
from spotty.providers.gcp.deployment.project_resources.disk_volume import DiskVolume
from spotty.providers.gcp.helpers.sync import BUCKET_SYNC_DIR, get_instance_sync_arguments
from spotty.utils import fix_indents_for_lines


def prepare_instance_template(instance_config: InstanceConfig, container: ContainerDeployment, sync_filters: list,
                              volumes: List[AbstractInstanceVolume], machine_name: str, image_link: str,
                              bucket_name: str, public_key_value: str, service_account_email: str,
                              output: AbstractOutputWriter):
    """Prepares deployment template to run an instance."""

    # get disk attachments
    disk_attachments, disk_device_names, disk_mount_dirs = _get_disk_attachments(volumes, instance_config.zone)

    # get Docker runtime parameters
    runtime_parameters = container.get_runtime_parameters(bool(instance_config.gpu))

    # render startup script
    with open(os.path.join(os.path.dirname(__file__), 'instance', 'cloud_init.yaml')) as f:
        startup_script = f.read()

    startup_script = chevron.render(startup_script, {
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
        'INSTANCE_STARTUP_COMMANDS': fix_indents_for_lines(instance_config.commands, startup_script,
                                                           '{{{INSTANCE_STARTUP_COMMANDS}}}'),
        'CONTAINER_STARTUP_COMMANDS': fix_indents_for_lines(container.config.commands, startup_script,
                                                            '{{{CONTAINER_STARTUP_COMMANDS}}}'),
    })

    # render the template
    with open(os.path.join(os.path.dirname(__file__), 'instance', 'template.yaml')) as f:
        template = f.read()

    template = chevron.render(template, {
        'SERVICE_ACCOUNT_EMAIL': service_account_email,
        'ZONE': instance_config.zone,
        'MACHINE_TYPE': instance_config.machine_type,
        'SOURCE_IMAGE': image_link,
        'BOOT_DISK_SIZE': instance_config.boot_disk_size,
        'STARTUP_SCRIPT': fix_indents_for_lines(startup_script, template, '{{{STARTUP_SCRIPT}}}'),
        'MACHINE_NAME': machine_name,
        'PREEMPTIBLE': 'false' if instance_config.on_demand else 'true',
        'GPU_TYPE': instance_config.gpu['type'] if instance_config.gpu else '',
        'GPU_COUNT': instance_config.gpu['count'] if instance_config.gpu else 0,
        'DISK_ATTACHMENTS': disk_attachments,
        'PUB_KEY_VALUE': public_key_value,
        'PORTS': ', '.join([str(port) for port in set(container.config.ports + [22])]),
    })

    # print some information about the deployment
    output.write('- image URL: ' + '/'.join(image_link.split('/')[-5:]))
    output.write('- zone: ' + instance_config.zone)
    output.write('- on-demand VM' if instance_config.on_demand else '- preemptible VM')
    output.write(('- GPUs: %d x %s' % (instance_config.gpu['count'], instance_config.gpu['type']))
                 if instance_config.gpu else '- no GPUs')

    # print name of the volume where Docker data will be stored
    if instance_config.docker_data_root:
        docker_data_volume_name = [volume.name for volume in volumes
                                   if is_subdir(instance_config.docker_data_root, volume.mount_dir)][0]
        output.write('- Docker data will be stored on the "%s" volume' % docker_data_volume_name)

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
