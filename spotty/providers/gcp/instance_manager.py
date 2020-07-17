from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.deployment.abstract_cloud_instance.abstract_cloud_instance_manager import AbstractCloudInstanceManager
from spotty.providers.gcp.config.instance_config import InstanceConfig
from spotty.providers.gcp.data_transfer import DataTransfer
from spotty.providers.gcp.instance_deployment import InstanceDeployment
from spotty.providers.gcp.resource_managers.bucket_manager import BucketManager
from spotty.utils import render_table


class InstanceManager(AbstractCloudInstanceManager):

    instance_config: InstanceConfig
    bucket_manager: BucketManager
    data_transfer: DataTransfer
    instance_deployment: InstanceDeployment

    def _get_instance_config(self, instance_config: dict) -> InstanceConfig:
        """Validates the instance config and returns an InstanceConfig object."""
        return InstanceConfig(instance_config, self.project_config)

    def _get_bucket_manager(self) -> BucketManager:
        region = '-'.join(self.instance_config.zone.split('-')[:-1])
        return BucketManager(self.instance_config.project_config.project_name, region)

    def _get_data_transfer(self) -> DataTransfer:
        """Returns a data transfer object."""
        return DataTransfer(
            local_project_dir=self.project_config.project_dir,
            host_project_dir=self.instance_config.host_project_dir,
            sync_filters=self.project_config.sync_filters,
            instance_name=self.instance_config.name,
        )

    def _get_instance_deployment(self) -> InstanceDeployment:
        """Returns an instance deployment manager."""
        return InstanceDeployment(self.instance_config)

    def download(self, download_filters: list, output: AbstractOutputWriter, dry_run=False):
        raise NotImplementedError('GCP provider doesn\'t have an implementation of the "download" command yet.')

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

        table.append(('Purchasing Option', 'Preemtible VM' if instance.is_preemtible else 'On-demand VM'))

        return render_table(table)

    @property
    def ssh_key_path(self):
        return self.instance_deployment.ssh_key_manager.private_key_file
