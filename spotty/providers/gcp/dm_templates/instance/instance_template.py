import os
from typing import List
import chevron
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.tmp_dir_volume import TmpDirVolume
from spotty.config.validation import is_subdir
from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.deployment.container.docker.docker_commands import DockerCommands
from spotty.deployment.container.docker.scripts.container_bash_script import ContainerBashScript
from spotty.deployment.container.docker.scripts.start_container_script import StartContainerScript
from spotty.deployment.abstract_cloud_instance.file_structure import CONTAINER_BASH_SCRIPT_PATH, \
    INSTANCE_STARTUP_SCRIPTS_DIR, CONTAINERS_TMP_DIR, INSTANCE_SPOTTY_TMP_DIR
from spotty.providers.gcp.config.disk_volume import DiskVolume
from spotty.providers.gcp.config.instance_config import InstanceConfig


def prepare_instance_template(instance_config: InstanceConfig, docker_commands: DockerCommands, image_link: str,
                              bucket_name: str, sync_project_cmd: str, public_key_value: str,
                              service_account_email: str, output: AbstractOutputWriter):
    """Prepares deployment template to run an instance."""

    # get disk attachments
    disk_attachments, disk_device_names, disk_mount_dirs = \
        _get_disk_attachments(instance_config.volumes, instance_config.zone)

    # run sync command as a non-root user
    if instance_config.container_config.run_as_host_user:
        sync_project_cmd = 'sudo -u %s %s' % (instance_config.user, sync_project_cmd)

    startup_scripts_templates = [
        {
            'filename': '01_prepare_instance.sh',
            'params': {
                'CONTAINER_BASH_SCRIPT_PATH': CONTAINER_BASH_SCRIPT_PATH,
                'CONTAINER_BASH_SCRIPT': ContainerBashScript(docker_commands).render(),
                'IS_GPU_INSTANCE': bool(instance_config.gpu),
                'SSH_USERNAME': instance_config.user,
                'SPOTTY_TMP_DIR': INSTANCE_SPOTTY_TMP_DIR,
                'CONTAINERS_TMP_DIR': CONTAINERS_TMP_DIR,
            },
        },
        {
            'filename': '02_mount_volumes.sh',
            'params': {
                'DISK_DEVICE_NAMES': ('"%s"' % '" "'.join(disk_device_names)) if disk_device_names else '',
                'DISK_MOUNT_DIRS': ('"%s"' % '" "'.join(disk_mount_dirs)) if disk_mount_dirs else '',
                'TMP_VOLUME_DIRS': [{'PATH': volume.host_path} for volume in instance_config.volumes
                                    if isinstance(volume, TmpDirVolume)],
            },
        },
        {
            'filename': '03_set_docker_root.sh',
            'params': {
                'DOCKER_DATA_ROOT_DIR': instance_config.docker_data_root,
            },
        },
        {
            'filename': '04_sync_project.sh',
            'params': {
                'HOST_PROJECT_DIR': instance_config.host_project_dir,
                'SYNC_PROJECT_CMD': sync_project_cmd,
            },
        },
        {
            'filename': '05_run_instance_startup_commands.sh',
            'params': {
                'INSTANCE_STARTUP_SCRIPTS_DIR': INSTANCE_STARTUP_SCRIPTS_DIR,
                'INSTANCE_STARTUP_COMMANDS': instance_config.commands,
            },
        },
    ]

    # render startup scripts
    startup_scripts_content = []
    for template in startup_scripts_templates:
        with open(os.path.join(os.path.dirname(__file__), 'data', 'startup_scripts', template['filename'])) as f:
            content = f.read()

        startup_scripts_content.append({
            'filename': template['filename'],
            'content': chevron.render(content, template['params'])
        })

    startup_scripts_content.append({
        'filename': '06_start_container.sh',
        'content': StartContainerScript(docker_commands).render(print_trace=True),
    })

    # render the main startup script
    with open(os.path.join(os.path.dirname(__file__), 'data', 'startup_script.sh.tpl')) as f:
        startup_script = f.read()

    startup_script = chevron.render(startup_script, {
        'MACHINE_NAME': instance_config.machine_name,
        'INSTANCE_STARTUP_SCRIPTS_DIR': INSTANCE_STARTUP_SCRIPTS_DIR,
        'STARTUP_SCRIPTS': startup_scripts_content,
    })

    # render the template
    with open(os.path.join(os.path.dirname(__file__), 'data', 'template.yaml')) as f:
        template = f.read()

    template = chevron.render(template, {
        'SERVICE_ACCOUNT_EMAIL': service_account_email,
        'ZONE': instance_config.zone,
        'MACHINE_TYPE': instance_config.machine_type,
        'SOURCE_IMAGE': image_link,
        'BOOT_DISK_SIZE': instance_config.boot_disk_size,
        'MACHINE_NAME': instance_config.machine_name,
        'PREEMPTIBLE': 'true' if instance_config.is_preemptible_instance else 'false',
        'GPU_TYPE': instance_config.gpu['type'] if instance_config.gpu else '',
        'GPU_COUNT': instance_config.gpu['count'] if instance_config.gpu else 0,
        'DISK_ATTACHMENTS': disk_attachments,
        'SSH_USERNAME': instance_config.user,
        'PUB_KEY_VALUE': public_key_value,
        'PORTS': ', '.join([str(port) for port in set([22] + instance_config.ports)]),
    }, partials_dict={
        'STARTUP_SCRIPT': startup_script,
    })

    # print some information about the deployment
    output.write('- image URL: ' + '/'.join(image_link.split('/')[-5:]))
    output.write('- zone: ' + instance_config.zone)
    output.write('- preemptible VM' if instance_config.is_preemptible_instance else '- on-demand VM')
    output.write(('- GPUs: %d x %s' % (instance_config.gpu['count'], instance_config.gpu['type']))
                 if instance_config.gpu else '- no GPUs')

    # print name of the volume where Docker data will be stored
    if instance_config.docker_data_root:
        docker_data_volume_name = [volume.name for volume in instance_config.volumes
                                   if is_subdir(instance_config.docker_data_root, volume.host_path)][0]
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
