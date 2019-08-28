from typing import List
from spotty.deployment.abstract_instance_volume import AbstractInstanceVolume
from spotty.deployment.container_deployment import VolumeMount
from spotty.utils import render_table


def render_volumes_info_table(volume_mounts: List[VolumeMount], volumes: List[AbstractInstanceVolume]):
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
