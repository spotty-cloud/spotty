from typing import List
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.providers.gcp.config.disk_volume import DiskVolume
from spotty.providers.gcp.helpers.ce_client import CEClient
from spotty.providers.gcp.resources.disk import Disk
from spotty.providers.gcp.resources.snapshot import Snapshot


def create_disks(ce: CEClient, volumes: List[AbstractInstanceVolume], output: AbstractOutputWriter,
                 dry_run: bool = False):
    disks_to_create = []

    # do some checks and prepare disk parameters
    for i, volume in enumerate(volumes):
        if isinstance(volume, DiskVolume):
            # check if the disk already exists
            disk = Disk.get_by_name(ce, volume.disk_name)
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
                snapshot = Snapshot.get_by_name(ce, volume.disk_name)
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
            ce.create_disk(disk_name, disk_size, snapshot_link)

        output.write('- disk "%s" was created' % disk_name)
