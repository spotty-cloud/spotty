import boto3
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.abstract_cloud_instance.abstract_instance_deployment import AbstractInstanceDeployment
from spotty.deployment.container.docker.docker_commands import DockerCommands
from spotty.providers.aws.cfn_templates.instance.template import prepare_instance_template, get_template_parameters
from spotty.providers.aws.data_transfer import DataTransfer
from spotty.providers.aws.helpers.availability_zone import update_availability_zone
from spotty.providers.aws.helpers.instance_prices import check_max_spot_price
from spotty.providers.aws.helpers.subnet import check_az_and_subnet
from spotty.providers.aws.resource_managers.key_pair_manager import KeyPairManager
from spotty.deployment.utils.print_info import render_volumes_info_table
from spotty.providers.aws.resources.instance import Instance
from spotty.providers.aws.config.instance_config import InstanceConfig
from spotty.providers.aws.deletion_policies import apply_deletion_policies
from spotty.providers.aws.resource_managers.instance_profile_stack_manager import InstanceProfileStackManager
from spotty.providers.aws.helpers.logs import download_logs
from spotty.providers.aws.resource_managers.instance_stack_manager import InstanceStackManager


class InstanceDeployment(AbstractInstanceDeployment):

    instance_config: InstanceConfig

    def __init__(self, instance_config: InstanceConfig):
        super().__init__(instance_config)

        self._project_name = instance_config.project_config.project_name
        self._ec2 = boto3.client('ec2', region_name=instance_config.region)

    @property
    def stack_manager(self) -> InstanceStackManager:
        return InstanceStackManager(self._project_name, self.instance_config.name, self.instance_config.region)

    @property
    def key_pair_manager(self) -> KeyPairManager:
        return KeyPairManager(self._ec2, self._project_name, self.instance_config.region)

    def get_instance(self) -> Instance:
        return Instance.get_by_stack_name(self._ec2, self.stack_manager.name)

    def deploy(self, container_commands: DockerCommands, bucket_name: str,
               data_transfer: DataTransfer, output: AbstractOutputWriter, dry_run: bool = False):
        # get deployment availability zone
        availability_zone = update_availability_zone(self._ec2, self.instance_config.availability_zone,
                                                     self.instance_config.volumes)

        # check availability zone and subnet configuration
        check_az_and_subnet(self._ec2, self.instance_config.region, availability_zone, self.instance_config.subnet_id)

        # check the maximum price for a spot instance
        check_max_spot_price(self._ec2, self.instance_config.instance_type, self.instance_config.is_spot_instance,
                             self.instance_config.max_price, availability_zone)

        # sync the project with the S3 bucket
        if bucket_name is not None:
            output.write('Syncing the project with the S3 bucket...')
            data_transfer.upload_local_to_bucket(bucket_name, dry_run=dry_run)

        # create or update instance profile
        if not dry_run:
            instance_profile_stack_manager = InstanceProfileStackManager(
                self._project_name, self.instance_config.name, self.instance_config.region)
            if not self.instance_config.instance_profile_arn:
                instance_profile_arn = instance_profile_stack_manager.create_or_update_stack(
                    self.instance_config.managed_policy_arns, output=output)
            else:
                instance_profile_arn = self.instance_config.instance_profile_arn
        else:
            instance_profile_arn = None

        # create a key pair if it doesn't exist
        if not dry_run:
            self.key_pair_manager.maybe_create_key()

        output.write('Preparing CloudFormation template...')

        # prepare CloudFormation template
        with output.prefix('  '):
            template = prepare_instance_template(
                ec2=self._ec2,
                instance_config=self.instance_config,
                docker_commands=container_commands,
                availability_zone=availability_zone,
                sync_project_cmd=data_transfer.get_download_bucket_to_instance_command(bucket_name=bucket_name),
                output=output,
            )

            # get parameters for the template
            parameters = get_template_parameters(
                ec2=self._ec2,
                instance_config=self.instance_config,
                instance_profile_arn=instance_profile_arn,
                bucket_name=bucket_name,
                key_pair_name=self.key_pair_manager.key_name,
                output=output,
            )

        # print information about the volumes
        output.write('\nVolumes:\n%s\n'
                     % render_volumes_info_table(self.instance_config.volume_mounts, self.instance_config.volumes))

        # create stack
        if not dry_run:
            stack = self.stack_manager.create_or_update_stack(template, parameters, self.instance_config, output)
            if stack.status != 'CREATE_COMPLETE':
                logs_str = 'Please, see CloudFormation logs for the details.'

                # download CloudFormation logs from the instance if it was created
                if self.get_instance():
                    log_paths = download_logs(
                        bucket_name=bucket_name,
                        instance_name=self.instance_config.name,
                        stack_uuid=stack.stack_uuid,
                        region=self.instance_config.region,
                    )

                    logs_str = 'Please, see the logs for the details:\n  '
                    logs_str += '\n  '.join(log_paths)

                raise ValueError('Stack "%s" was not created.\n%s' % (stack.name, logs_str))

    def delete(self, output: AbstractOutputWriter):
        # terminate the instance
        instance = self.get_instance()
        if instance:
            output.write('Terminating the instance... ', newline=False)
            instance.terminate()
            output.write('DONE')
        else:
            output.write('The instance was already terminated.')

        # delete the stack in background if it exists
        self.stack_manager.delete_stack(output, no_wait=True)

        output.write('Applying deletion policies for the volumes...')

        # apply deletion policies for the volumes
        with output.prefix('  '):
            apply_deletion_policies(self._ec2, self.instance_config.volumes, output)
