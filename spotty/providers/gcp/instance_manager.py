from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.providers.abstract_instance_manager import AbstractInstanceManager
from spotty.providers.gcp.config.instance_config import InstanceConfig
from spotty.providers.gcp.deployment.image_deployment import ImageDeployment
from spotty.providers.gcp.deployment.instance_deployment import InstanceDeployment
from spotty.providers.gcp.helpers.sync import sync_local_to_bucket, sync_bucket_to_instance
from spotty.utils import render_table


class InstanceManager(AbstractInstanceManager):

    @property
    def instance_deployment(self) -> InstanceDeployment:
        """Returns an instance deployment manager."""
        return InstanceDeployment(self.project_config.project_name, self.instance_config)

    @property
    def image_deployment(self) -> ImageDeployment:
        """Returns an image deployment manager."""
        return ImageDeployment(self.project_config.project_name, self.instance_config)

    def _get_instance_config(self, config: dict) -> InstanceConfig:
        return InstanceConfig(config)

    @property
    def instance_config(self) -> InstanceConfig:
        """This property is redefined just for a correct type hinting."""
        return self._instance_config

    def is_running(self):
        return bool(self.instance_deployment.get_instance())

    def start(self, output: AbstractOutputWriter, dry_run=False):
        deployment = self.instance_deployment

        if not dry_run:
            # check if the instance is already running
            instance = deployment.get_instance()
            if instance and instance.is_running:
                print('Instance is already running. Are you sure you want to restart it?')
                res = input('Type "y" to confirm: ')
                if res != 'y':
                    raise ValueError('The operation was cancelled.')

                # terminating the instance without applying deletion policies
                self.instance_deployment.stack.delete_stack(output)

        # deploy the instance
        deployment.deploy(self.project_config, output, dry_run=dry_run)

    def stop(self, output: AbstractOutputWriter):
        # delete the deployment and apply deletion policies for the volumes
        self.instance_deployment.delete(output)

    def sync(self, output: AbstractOutputWriter, dry_run=False):
        # create or get existing bucket for the project
        bucket_name = self.instance_deployment.bucket.get_or_create_bucket(output, dry_run)

        # sync the project with the bucket
        output.write('Syncing the project with the bucket...')
        sync_local_to_bucket(self.project_config.project_dir, bucket_name, self.project_config.sync_filters, dry_run)

        if not dry_run:
            # sync the bucket with the instance
            output.write('Syncing the bucket with the instance...')
            sync_bucket_to_instance(self.project_config.sync_filters, self.get_ip_address(), self.ssh_port,
                                    self.ssh_user, self.ssh_key_path)

    def download(self, download_filters: list, output: AbstractOutputWriter, dry_run=False):
        raise NotImplementedError('GCP provider doesn\'t have an implementation of the "download" command yet.')

    def clean(self, output: AbstractOutputWriter):
        raise NotImplementedError

    def get_status_text(self) -> str:
        instance = self.instance_deployment.get_instance()
        if not instance:
            raise InstanceNotRunningError(self.instance_config.name)

        table = [
            ('Instance Status', instance.status),
            ('Machine Type', instance.machine_type),
            ('Zone', instance.zone),
        ]

        if instance.public_ip_address:
            table.append(('Public IP Address', instance.public_ip_address))

        table.append(('Launch Time', instance.creation_timestamp.today().strftime('%Y-%m-%d %H:%M:%S')))
        table.append(('Purchasing Option', 'Preemtible VM' if instance.is_preemtible else 'On-demand VM'))

        return render_table(table)

    def get_public_ip_address(self) -> str:
        """Returns a public IP address of the running instance."""
        instance = self.instance_deployment.get_instance()
        if not instance or not instance.is_running:
            raise InstanceNotRunningError(self.instance_config.name)

        return instance.public_ip_address

    @property
    def ssh_user(self):
        return 'ubuntu'

    @property
    def ssh_key_path(self):
        return self.instance_deployment.ssh_key.private_key_file
