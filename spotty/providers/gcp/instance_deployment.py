from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.abstract_cloud_instance.abstract_instance_deployment import AbstractInstanceDeployment
from spotty.deployment.container.docker.docker_commands import DockerCommands
from spotty.deployment.utils.print_info import render_volumes_info_table
from spotty.providers.gcp.config.instance_config import InstanceConfig
from spotty.providers.gcp.data_transfer import DataTransfer
from spotty.providers.gcp.dm_templates.instance.instance_template import prepare_instance_template
from spotty.providers.gcp.helpers.image import get_image
from spotty.providers.gcp.helpers.volumes import create_disks
from spotty.providers.gcp.resource_managers.instance_stack_manager import InstanceStackManager
from spotty.providers.gcp.helpers.ce_client import CEClient
from spotty.providers.gcp.helpers.gcp_credentials import GcpCredentials
from spotty.providers.gcp.resource_managers.ssh_key_manager import SshKeyManager
from spotty.providers.gcp.resources.instance import Instance
from spotty.providers.gcp.helpers.deployment import check_gpu_configuration


class InstanceDeployment(AbstractInstanceDeployment):

    instance_config: InstanceConfig

    def __init__(self, instance_config: InstanceConfig):
        super().__init__(instance_config)

        self._project_name = instance_config.project_config.project_name
        self._credentials = GcpCredentials()
        self._ce = CEClient(self._credentials.project_id, instance_config.zone)

    @property
    def stack_manager(self) -> InstanceStackManager:
        return InstanceStackManager(self.instance_config.machine_name, self._credentials.project_id, self.instance_config.zone)

    @property
    def ssh_key_manager(self) -> SshKeyManager:
        return SshKeyManager(self._project_name, self.instance_config.zone)

    def get_instance(self) -> Instance:
        return Instance.get_by_name(self._ce, self.instance_config.machine_name)

    def deploy(self, container_commands: DockerCommands, bucket_name: str,
               data_transfer: DataTransfer, output: AbstractOutputWriter, dry_run: bool = False):
        # check machine type
        if not self._ce.get_machine_types(self.instance_config.machine_type):
            raise ValueError('"%s" machine type is not available in the "%s" zone.'
                             % (self.instance_config.machine_type, self.instance_config.zone))

        # check GPU configuration
        check_gpu_configuration(self._ce, self.instance_config.gpu)

        # remove the stack it it exists to make all the disks available
        stack_manager = self.stack_manager
        stack_manager.delete_stack(output=output)

        # sync the project with the S3 bucket
        if bucket_name is not None:
            output.write('Syncing the project with the bucket...')
            data_transfer.upload_local_to_bucket(bucket_name, dry_run=dry_run)

        # create volumes
        if self.instance_config.volumes:
            # create disks
            output.write('\nCreating disks...')
            with output.prefix('  '):
                create_disks(self._ce, self.instance_config.volumes, output=output, dry_run=dry_run)
            output.write('')

        # prepare Deployment Manager template
        output.write('Preparing the deployment template...')
        with output.prefix('  '):
            # get an image
            image_link = get_image(self._ce, self.instance_config.image_uri, self.instance_config.image_name).self_link

            # get or create an SSH key
            public_key_value = self.ssh_key_manager.get_public_key_value()

            # prepare the deployment template
            sync_project_cmd = data_transfer.get_download_bucket_to_instance_command(bucket_name=bucket_name)
            template = prepare_instance_template(
                instance_config=self.instance_config,
                docker_commands=container_commands,
                image_link=image_link,
                bucket_name=bucket_name,
                sync_project_cmd=sync_project_cmd,
                public_key_value=public_key_value,
                service_account_email=self._credentials.service_account_email,
                output=output,
            )

        output.write('')

        # print information about the volumes
        output.write('Volumes:\n%s\n' % render_volumes_info_table(self.instance_config.volume_mounts,
                                                                  self.instance_config.volumes))

        # create stack
        if not dry_run:
            stack_manager.create_stack(template, output=output)

    def delete(self, output: AbstractOutputWriter):
        self.stack_manager.delete_stack(output)

        # TODO: apply deletion policies
