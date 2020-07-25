from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.deployment.abstract_cloud_instance.abstract_cloud_instance_manager import AbstractCloudInstanceManager
from spotty.providers.aws.resource_managers.bucket_manager import BucketManager
from spotty.providers.aws.config.instance_config import InstanceConfig
from spotty.providers.aws.data_transfer import DataTransfer
from spotty.providers.aws.instance_deployment import InstanceDeployment
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
        """Returns an bucket manager."""
        return BucketManager(self.instance_config.project_config.project_name, self.instance_config.region)

    def _get_data_transfer(self) -> DataTransfer:
        """Returns a data transfer object."""
        return DataTransfer(
            local_project_dir=self.project_config.project_dir,
            host_project_dir=self.instance_config.host_project_dir,
            sync_filters=self.project_config.sync_filters,
            instance_name=self.instance_config.name,
            region=self.instance_config.region,
        )

    def _get_instance_deployment(self) -> InstanceDeployment:
        """Returns an instance deployment manager."""
        return InstanceDeployment(self.instance_config)

    def get_status_text(self):
        instance = self.instance_deployment.get_instance()
        if not instance:
            raise InstanceNotRunningError(self.instance_config.name)

        table = [
            ('Instance State', instance.state),
            ('Instance Type', instance.instance_type),
            ('Availability Zone', instance.availability_zone),
        ]

        if instance.public_ip_address:
            table.append(('Public IP Address', instance.public_ip_address))

        if instance.lifecycle == 'spot':
            spot_price = instance.get_spot_price()
            table.append(('Purchasing Option', 'Spot Instance'))
            table.append(('Spot Instance Price', '$%.04f' % spot_price))
        else:
            on_demand_price = instance.get_on_demand_price()
            table.append(('Purchasing Option', 'On-Demand Instance'))
            table.append(('Instance Price', ('$%.04f (us-east-1)' % on_demand_price) if on_demand_price else 'Unknown'))

        return render_table(table)

    @property
    def ssh_key_path(self):
        return self.instance_deployment.key_pair_manager.key_path
