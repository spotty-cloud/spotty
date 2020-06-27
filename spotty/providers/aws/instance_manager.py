import logging
import subprocess
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.commands import get_script_command
from spotty.deployment.container_commands.docker_commands import DockerCommands
from spotty.deployment.container_scripts.docker.start_container_script import StartContainerScript
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.providers.aws.config.instance_config import InstanceConfig
from spotty.providers.aws.deployment.ami_deployment import AmiDeployment
from spotty.providers.aws.deployment.instance_deployment import InstanceDeployment
from spotty.providers.aws.helpers.s3_sync import check_aws_installed
from spotty.providers.aws.helpers.spotty_download import get_instance_to_s3_command, get_s3_to_local_command
from spotty.providers.abstract_ssh_instance_manager import AbstractSshInstanceManager
from spotty.providers.aws.helpers.spotty_sync import get_local_to_s3_command, get_s3_to_instance_command
from spotty.utils import render_table


class InstanceManager(AbstractSshInstanceManager):

    @property
    def instance_deployment(self) -> InstanceDeployment:
        """Returns an instance deployment manager."""
        return InstanceDeployment(self.instance_config)

    @property
    def ami_deployment(self) -> AmiDeployment:
        """Returns an AMI deployment manager."""
        return AmiDeployment(self.instance_config)

    def _get_instance_config(self, instance_config: dict) -> InstanceConfig:
        """Validates the instance config and returns an InstanceConfig object."""
        return InstanceConfig(instance_config, self.project_config)

    @property
    def instance_config(self) -> InstanceConfig:
        """This property is redefined just for a correct type hinting."""
        return self._instance_config

    @property
    def container_commands(self) -> DockerCommands:
        """A collection of commands to manage a container from the host OS."""
        return DockerCommands(self.instance_config)

    def is_running(self):
        """Checks if the instance is running."""
        return bool(self.instance_deployment.get_instance())

    def start(self, output: AbstractOutputWriter, dry_run=False):
        deployment = self.instance_deployment

        if not dry_run:
            # check if the instance is already running
            instance = deployment.get_instance()
            if instance:
                print('Instance is already running. Are you sure you want to restart it?')
                res = input('Type "y" to confirm: ')
                if res != 'y':
                    raise ValueError('The operation was cancelled.')

                # terminating the instance to make EBS volumes available
                output.write('Terminating the instance... ', newline=False)
                instance.terminate()
                instance.wait_instance_terminated()
                output.write('DONE')

        # deploy the instance
        deployment.deploy(self.container_commands, output, dry_run=dry_run)

    def start_container(self, output: AbstractOutputWriter, dry_run=False):
        """Starts or restarts container on the host OS."""
        start_container_script = StartContainerScript(self.container_commands).render()
        start_container_command = get_script_command('start-container', start_container_script)

        exit_code = self.exec(start_container_command)
        if exit_code != 0:
            raise ValueError('Failed to start the container')

    def stop(self, output: AbstractOutputWriter):
        # delete the stack and apply deletion policies
        self.instance_deployment.delete(output)

    def clean(self, output: AbstractOutputWriter):
        pass

    def sync(self, output: AbstractOutputWriter, dry_run=False):
        # get the project bucket
        bucket_name = self.instance_deployment.bucket.get_bucket()

        # sync the project with the S3 bucket
        self.instance_deployment.upload_project_to_s3(bucket_name, output, dry_run=dry_run)

        if not dry_run:
            # sync the S3 bucket with the instance
            output.write('Syncing S3 bucket with the instance...')
            remote_cmd = get_s3_to_instance_command(
                bucket_name=bucket_name,
                instance_project_dir=self.instance_config.host_project_dir,
                region=self.instance_config.region,
                sync_filters=self.project_config.sync_filters,
            )
            logging.debug('Remote sync command: ' + remote_cmd)

            # execute the command on the host OS
            exit_code = self.exec(remote_cmd)
            if exit_code != 0:
                raise ValueError('Failed to upload files from the S3 bucket to the instance')

    def download(self, download_filters: list, output: AbstractOutputWriter, dry_run=False):
        # check AWS CLI is installed
        check_aws_installed()

        # get the project bucket
        bucket_name = self.instance_deployment.bucket.get_bucket()

        # sync files from the instance to a temporary S3 directory
        output.write('Uploading files from the instance to S3 bucket...')
        remote_cmd = get_instance_to_s3_command(
            instance_project_dir=self.instance_config.host_project_dir,
            bucket_name=bucket_name,
            instance_name=self.instance_config.name,
            region=self.instance_config.region,
            download_filters=download_filters,
            dry_run=dry_run,
        )
        logging.debug('Remote sync command: ' + remote_cmd)

        # execute the command on the host OS
        exit_code = self.exec(remote_cmd)
        if exit_code != 0:
            raise ValueError('Failed to upload files from the instance to the S3 bucket')

        if not dry_run:
            # sync the project with the S3 bucket
            output.write('Downloading files from S3 bucket to local...')
            local_cmd = get_s3_to_local_command(
                bucket_name=bucket_name,
                instance_name=self.instance_config.name,
                local_project_dir=self.project_config.project_dir,
                region=self.instance_config.region,
                download_filters=download_filters,
            )
            logging.debug('Local sync command: ' + local_cmd)

            # execute the command locally
            exit_code = subprocess.call(local_cmd, shell=True)
            if exit_code != 0:
                raise ValueError('Failed to download files from the S3 bucket to local')

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

    def get_public_ip_address(self):
        """Returns a public IP address of the running instance."""
        instance = self.instance_deployment.get_instance()
        if not instance:
            raise InstanceNotRunningError(self.instance_config.name)

        return instance.public_ip_address

    @property
    def ssh_user(self):
        return 'ubuntu'

    @property
    def ssh_key_path(self):
        return self.instance_deployment.key_pair.key_path
