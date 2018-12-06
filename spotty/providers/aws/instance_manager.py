from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.project_config import ProjectConfig
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.providers.aws.config.instance_config import InstanceConfig
from spotty.providers.aws.deployment.instance_deployment import InstanceDeployment
from spotty.providers.aws.helpers.sync import sync_project_with_s3, sync_instance_with_s3
from spotty.providers.abstract_instance_manager import AbstractInstanceManager
from spotty.utils import render_table


class InstanceManager(AbstractInstanceManager):

    def __init__(self, project_config: ProjectConfig, instance_config: dict):
        super().__init__(project_config, instance_config)

        self._deployment = InstanceDeployment(project_config.project_name, self.instance_config)

    def _get_instance_config(self, config: dict) -> InstanceConfig:
        return InstanceConfig(config)

    def is_running(self):
        instance = self.deployment.get_instance()
        if not instance:
            return False

        return instance.is_running()

    def start(self, output: AbstractOutputWriter, dry_run=False):
        if not dry_run:
            # check if the instance is already running
            instance = self.deployment.get_instance()
            if instance and instance.is_running():
                print('Are you sure you want to restart the instance with new parameters?')
                res = input('Type "y" to confirm: ')
                if res != 'y':
                    return

                # terminating the instance to make EBS volumes available
                output.write('Terminating the instance...')
                instance.terminate()
                instance.wait_instance_terminated()

        self.deployment.deploy(self.project_config, output, dry_run=dry_run)

    def stop(self, output: AbstractOutputWriter):
        # terminate the instance
        instance = self.deployment.get_instance()
        if instance and instance.is_running():
            output.write('Terminating the instance...')
            instance.terminate()
            instance.wait_instance_terminated()

        # delete the stack
        self.deployment.instance_stack.delete_stack(output, no_wait=True)

        output.write('Applying deletion policies for the volumes...')

        # apply deletion policies for the volumes
        with output.prefix('  '):
            self.deployment.apply_deletion_policies(output)

    def clean(self, output: AbstractOutputWriter):
        pass

    def sync(self, output: AbstractOutputWriter, dry_run=False):
        # create or get existing bucket for the project
        bucket_name = self.deployment.bucket.get_or_create_bucket(output, dry_run)

        # sync the project with S3 bucket
        output.write('Syncing the project with S3 bucket...')
        sync_project_with_s3(self.project_config.project_dir, bucket_name, self.instance_config.region,
                             self.project_config.sync_filters, dry_run)

        # sync S3 with the instance
        output.write('Syncing S3 bucket with the instance...')
        if not dry_run:
            sync_instance_with_s3(self.ip_address, self.ssh_user, self.ssh_key_path, self.instance_config.local_ssh_port)

    @property
    def status_text(self):
        instance = self.deployment.get_instance()
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
        instance = self.deployment.get_instance()
        if not instance:
            raise InstanceNotRunningError()

        ip_address = instance.public_ip_address if instance.public_ip_address else instance.private_ip_address

        return ip_address

    @property
    def ssh_user(self):
        return 'ubuntu'

    @property
    def ssh_key_path(self):
        return self.deployment.key_pair.key_path

    @property
    def deployment(self) -> InstanceDeployment:
        return self._deployment
