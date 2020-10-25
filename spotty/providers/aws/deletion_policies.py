from typing import List
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.providers.aws.resources.snapshot import Snapshot
from spotty.providers.aws.resources.volume import Volume
from spotty.providers.aws.config.ebs_volume import EbsVolume


def apply_deletion_policies(ec2, volumes: List[AbstractInstanceVolume], output: AbstractOutputWriter):
    """Applies deletion policies to the EBS volumes."""

    # get volumes
    ebs_volumes = [volume for volume in volumes if isinstance(volume, EbsVolume)]

    # no volumes
    if not ebs_volumes:
        output.write('- no EBS volumes configured')
        return

    # apply deletion policies
    wait_snapshots = []
    for volume in ebs_volumes:
        # get EC2 volume
        try:
            ec2_volume = Volume.get_by_name(ec2, volume.ec2_volume_name)
        except Exception as e:
            output.write('- volume "%s" not found. Error: %s' % (volume.ec2_volume_name, str(e)))
            continue

        if not ec2_volume:
            output.write('- volume "%s" not found' % volume.ec2_volume_name)
            continue

        if not ec2_volume.is_available():
            output.write('- volume "%s" is not available (state: %s)'
                         % (volume.ec2_volume_name, ec2_volume.state))
            continue

        # apply deletion policies
        if volume.deletion_policy == EbsVolume.DP_RETAIN:
            # do nothing
            output.write('- volume "%s" is retained' % ec2_volume.name)

        elif volume.deletion_policy == EbsVolume.DP_DELETE:
            # delete EBS volume
            _delete_ec2_volume(ec2_volume, output)

        elif volume.deletion_policy == EbsVolume.DP_CREATE_SNAPSHOT \
                or volume.deletion_policy == EbsVolume.DP_UPDATE_SNAPSHOT:
            try:
                # rename a previous snapshot
                prev_snapshot = Snapshot.get_by_name(ec2, volume.ec2_volume_name)
                if prev_snapshot:
                    prev_snapshot.rename('%s-%d' % (prev_snapshot.name, prev_snapshot.creation_time))

                output.write('- creating a snapshot for the volume "%s"...' % ec2_volume.name)

                # create a new snapshot
                new_snapshot = ec2_volume.create_snapshot()

                # delete the EBS volume and a previous snapshot only after a new snapshot will be created
                wait_snapshots.append({
                    'new_snapshot': new_snapshot,
                    'prev_snapshot': prev_snapshot,
                    'ec2_volume': ec2_volume,
                    'deletion_policy': volume.deletion_policy,
                })
            except Exception as e:
                output.write('- snapshot for the volume "%s" was not created. Error: %s'
                             % (volume.ec2_volume_name, str(e)))

        else:
            raise ValueError('Unsupported deletion policy: "%s".' % volume.deletion_policy)

    # wait until all snapshots will be created
    for resources in wait_snapshots:
        try:
            resources['new_snapshot'].wait_snapshot_completed()
            output.write('- snapshot for the volume "%s" was created' % resources['new_snapshot'].name)
        except Exception as e:
            output.write('- snapshot "%s" was not created. Error: %s' % (resources['new_snapshot'].name, str(e)))
            continue

        # delete a previous snapshot if it's the "update_snapshot" deletion policy
        if (resources['deletion_policy'] == EbsVolume.DP_UPDATE_SNAPSHOT) and resources['prev_snapshot']:
            _delete_snapshot(resources['prev_snapshot'], output)

        # delete the EBS volume
        _delete_ec2_volume(resources['ec2_volume'], output)


def _delete_ec2_volume(ec2_volume: Volume, output: AbstractOutputWriter):
    try:
        ec2_volume.delete()
        output.write('- volume "%s" was deleted' % ec2_volume.name)
    except Exception as e:
        output.write('- volume "%s" was not deleted. Error: %s' % (ec2_volume.name, str(e)))


def _delete_snapshot(snapshot: Snapshot, output: AbstractOutputWriter):
    try:
        snapshot.delete()
        output.write('- previous snapshot "%s" was deleted' % snapshot.name)
    except Exception as e:
        output.write('- previous snapshot "%s" was not deleted. Error: %s' % (snapshot.name, str(e)))
