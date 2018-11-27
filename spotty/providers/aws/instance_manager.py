from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.project_config import ProjectConfig
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.providers.aws.helpers.instance_config import InstanceConfig
from spotty.providers.aws.helpers.sync import sync_project_with_s3, sync_instance_with_s3
from spotty.providers.aws.helpers.volume_config import VolumeConfig
from spotty.providers.aws.project_resources.instance_profile_stack import create_or_update_instance_profile
from spotty.providers.abstract_instance_manager import AbstractInstanceManager
from spotty.providers.aws.project_resources.instance_stack import InstanceStackResource
from spotty.providers.aws.templates.run_instance import RunInstanceTemplate
from spotty.providers.aws.validation import is_nitro_instance
from spotty.utils import render_table


class AwsInstanceManager(AbstractInstanceManager):

    def __init__(self, instance_config: dict, project_config: ProjectConfig):
        super().__init__(instance_config, project_config)

        self._instance_config = InstanceConfig(project_config.project_name, instance_config, project_config.container)
        self._stack = InstanceStackResource(project_config.project_name, self._instance_config.name,
                                            self._instance_config.region)
        self._template = RunInstanceTemplate(self._instance_config)

    @property
    def instance_config(self) -> InstanceConfig:
        return self._instance_config

    def is_running(self):
        instance = self._stack.get_instance()
        if not instance:
            return False

        return instance.is_running()

    def start(self, output: AbstractOutputWriter, dry_run=False):
        # check that it's not a Nitro-based instance
        if is_nitro_instance(self.instance_config.instance_type):
            raise ValueError('Currently Nitro-based instances are not supported.')

        # check availability zone and subnet
        self.instance_config.check_az_and_subnet()

        # check the maximum price for a spot instance
        self.instance_config.check_max_price()

        # check if the instance is already running
        instance = self._stack.get_instance()
        if instance and instance.is_running():
            print('Are you sure you want to restart the instance with new parameters?')
            res = input('Type "y" to confirm: ')
            if res != 'y':
                return

            # terminating the instance to make volumes available
            output.write('Terminating the instance...')
            instance.terminate()
            instance.wait_instance_terminated()

        # create or get existing bucket for the project
        bucket_name = self.instance_config.bucket.get_or_create_bucket(output, dry_run)

        # sync the project with the bucket
        sync_project_with_s3(self.project_config.project_dir, bucket_name, self.instance_config.region,
                             self.project_config.sync_filters, dry_run)

        # create or update instance profile
        instance_profile_arn = create_or_update_instance_profile(self.instance_config.region, output, dry_run)

        output.write('Preparing CloudFormation template...')

        # prepare CloudFormation template
        with output.prefix('  '):
            template = self._template.prepare(output)

        # get template parameters
        parameters = self._template.get_parameters(instance_profile_arn, bucket_name, dry_run)

        # print container volumes
        output.write('\nContainer volumes:')
        with output.prefix('  '):
            volumes_dict = {volume.name: volume for volume in self.instance_config.volumes}
            for volume_mount in self.instance_config.volume_mounts:
                if volume_mount.name in volumes_dict:
                    output.write('%s -> EBS volume (%s)'
                                 % (volume_mount.container_dir, volumes_dict[volume_mount.name].ec2_volume_name))
                else:
                    output.write('%s -> temporary directory' % volume_mount.container_dir)
        output.write('')

        # create stack
        if not dry_run:
            self._stack.create_or_update_stack(template, parameters, output)

    def stop(self, output: AbstractOutputWriter):
        # terminate the instance
        instance = self._stack.get_instance()
        if instance and instance.is_running():
            output.write('Terminating the instance...')
            instance.terminate()
            instance.wait_instance_terminated()

        # delete the stack
        self._stack.delete_stack(output, no_wait=True)

        output.write('Applying deletion policies for the volumes...')

        # apply deletion policies for the volumes
        with output.prefix('  '):
            self.apply_deletion_policies(output)

    def clean(self, output: AbstractOutputWriter):
        pass

    def sync(self, output: AbstractOutputWriter, dry_run=False):
        # create or get existing bucket for the project
        bucket_name = self.instance_config.bucket.get_or_create_bucket(output, dry_run)

        # sync the project with S3 bucket
        output.write('Syncing the project with S3 bucket...')
        sync_project_with_s3(self.project_config.project_dir, bucket_name, self.instance_config.region,
                             self.project_config.sync_filters, dry_run)

        # sync S3 with the instance
        output.write('Syncing S3 bucket with the instance...')
        if not dry_run:
            sync_instance_with_s3(self.ip_address, self.ssh_user, self.ssh_key_path, self.local_ssh_port)

    @property
    def status_text(self):
        instance = self._stack.get_instance()
        if not instance:
            raise InstanceNotRunningError()

        table = [
            ('Instance State', instance.state),
            ('Instance Type', instance.instance_type),
            ('Availability Zone', instance.availability_zone),
            ('Public IP Address', instance.public_ip_address),
            ('Private IP Address', instance.private_ip_address),
            ('Launch Time', instance.launch_time.strftime('%Y-%m-%d %H:%M:%S')),
        ]

        if instance.lifecycle == 'spot':
            spot_price = instance.get_spot_price()
            table.append(('Purchasing Option', 'Spot Instance'))
            table.append(('Spot Instance Price', '$%.04f' % spot_price))
        else:
            table.append(('Purchasing Option', 'On-Demand Instance'))

        return render_table(table)

    @property
    def ip_address(self):
        instance = self._stack.get_instance()
        if not instance:
            raise InstanceNotRunningError()

        ip_address = instance.public_ip_address if instance.public_ip_address else instance.private_ip_address

        return ip_address

    @property
    def ssh_user(self):
        return 'ubuntu'

    @property
    def ssh_key_path(self):
        return self.instance_config.key_pair.key_path

    def apply_deletion_policies(self, output: AbstractOutputWriter):
        """Applies deletion policies to the volumes."""
        wait_snapshots = []
        delete_snapshots = []
        delete_volumes = []

        for volume in self.instance_config.volumes:
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
            if volume.deletion_policy == VolumeConfig.DP_RETAIN:
                # do nothing
                output.write('- volume "%s" is retained' % ec2_volume.name)

            elif volume.deletion_policy == VolumeConfig.DP_DELETE:
                # volume will be deleted later
                delete_volumes.append(ec2_volume)

            elif volume.deletion_policy == VolumeConfig.DP_CREATE_SNAPSHOT \
                    or volume.deletion_policy == VolumeConfig.DP_UPDATE_SNAPSHOT:
                try:
                    # rename or delete previous snapshot
                    prev_snapshot = volume.get_snapshot(from_volume_name=True)
                    if prev_snapshot:
                        # rename previous snapshot
                        if volume.deletion_policy == VolumeConfig.DP_CREATE_SNAPSHOT:
                            prev_snapshot.rename('%s-%d' % (prev_snapshot.name, prev_snapshot.creation_time))

                        # once new snapshot will be created, the old one should be deleted
                        if volume.deletion_policy == VolumeConfig.DP_UPDATE_SNAPSHOT:
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
