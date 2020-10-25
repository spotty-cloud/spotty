import logging
from abc import ABC, abstractmethod
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.project_config import ProjectConfig
from spotty.deployment.abstract_cloud_instance.abstract_data_transfer import AbstractDataTransfer
from spotty.deployment.abstract_cloud_instance.abstract_instance_deployment import AbstractInstanceDeployment
from spotty.deployment.abstract_cloud_instance.abstract_bucket_manager import AbstractBucketManager
from spotty.deployment.abstract_cloud_instance.errors.bucket_not_found import BucketNotFoundError
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.deployment.abstract_ssh_instance_manager import AbstractSshInstanceManager


class AbstractCloudInstanceManager(AbstractSshInstanceManager, ABC):

    def __init__(self, project_config: ProjectConfig, instance_config: dict):
        super().__init__(project_config, instance_config)

        self._bucket_manager = self._get_bucket_manager()
        self._data_transfer = self._get_data_transfer()
        self._instance_deployment = self._get_instance_deployment()

    @abstractmethod
    def _get_bucket_manager(self) -> AbstractBucketManager:
        """Returns an bucket manager."""
        raise NotImplementedError

    @abstractmethod
    def _get_data_transfer(self) -> AbstractDataTransfer:
        """Returns a data transfer object."""
        raise NotImplementedError

    @abstractmethod
    def _get_instance_deployment(self) -> AbstractInstanceDeployment:
        """Returns an instance deployment manager."""
        raise NotImplementedError

    @property
    def bucket_manager(self) -> AbstractBucketManager:
        """Returns a bucket manager."""
        return self._bucket_manager

    @property
    def data_transfer(self) -> AbstractDataTransfer:
        """Returns a data transfer object."""
        return self._data_transfer

    @property
    def instance_deployment(self) -> AbstractInstanceDeployment:
        """Returns an instance deployment manager."""
        return self._instance_deployment

    def is_running(self) -> bool:
        """Checks if the instance is running."""
        instance = self.instance_deployment.get_instance()
        return instance and instance.is_running

    def start(self, output: AbstractOutputWriter, dry_run=False):
        # make sure the Dockerfile exists
        self._check_dockerfile_exists()

        if not dry_run:
            # check if the instance is already running
            instance = self.instance_deployment.get_instance()
            if instance:
                if instance.is_running:
                    print('Instance is already running. Are you sure you want to restart it?')
                    res = input('Type "y" to confirm: ')
                    if res != 'y':
                        raise ValueError('The operation was cancelled.')

                    # terminating the instance to make EBS volumes available (the stack will be deleted later)
                    output.write('Terminating the instance... ', newline=False)
                    instance.terminate()
                    output.write('DONE')

                elif instance.is_stopped:
                    # TODO: restart the instance if it stopped
                    pass

        # create or get existing bucket for the project
        bucket_name = None
        try:
            bucket_name = self.bucket_manager.get_bucket().name
        except BucketNotFoundError:
            if not dry_run:
                bucket_name = self.bucket_manager.create_bucket().name
                output.write('Bucket "%s" was created.' % bucket_name)

        # deploy the instance
        self.instance_deployment.deploy(
            container_commands=self.container_commands,
            bucket_name=bucket_name,
            data_transfer=self.data_transfer,
            output=output,
            dry_run=dry_run,
        )

    def stop(self, only_shutdown: bool, output: AbstractOutputWriter):
        if only_shutdown:
            output.write('Shutting down the instance... ', newline=False)
            self.instance_deployment.get_instance().stop()
            output.write('DONE')
        else:
            # delete the stack and apply deletion policies
            self.instance_deployment.delete(output)

    def clean(self, output: AbstractOutputWriter):
        pass

    def sync(self, output: AbstractOutputWriter, dry_run=False):
        # get the project bucket name
        bucket_name = self.bucket_manager.get_bucket().name

        # sync the project with the S3 bucket
        output.write('Syncing the project with the bucket...')
        self.data_transfer.upload_local_to_bucket(bucket_name, dry_run=dry_run)

        if not dry_run:
            # sync the S3 bucket with the instance
            output.write('Syncing the bucket with the instance...')
            remote_cmd = self.data_transfer.get_download_bucket_to_instance_command(
                bucket_name=bucket_name,
                use_sudo=(not self.instance_config.container_config.run_as_host_user),
            )
            logging.debug('Remote sync command: ' + remote_cmd)

            # execute the command on the host OS
            exit_code = self.exec(remote_cmd)
            if exit_code != 0:
                raise ValueError('Failed to download files from the bucket to the instance')

    def download(self, download_filters: list, output: AbstractOutputWriter, dry_run=False):
        # get the project bucket name
        bucket_name = self.bucket_manager.get_bucket().name

        # sync files from the instance to a temporary S3 directory
        output.write('Uploading files from the instance to the bucket...')
        remote_cmd = self.data_transfer.get_upload_instance_to_bucket_command(
            bucket_name=bucket_name,
            download_filters=download_filters,
            use_sudo=(not self.instance_config.container_config.run_as_host_user),
            dry_run=dry_run,
        )
        logging.debug('Remote sync command: ' + remote_cmd)

        # execute the command on the host OS
        exit_code = self.exec(remote_cmd)
        if exit_code != 0:
            raise ValueError('Failed to upload files from the instance to the bucket')

        if not dry_run:
            # sync the project with the S3 bucket
            output.write('Downloading files from the bucket to local...')
            self.data_transfer.download_bucket_to_local(bucket_name=bucket_name, download_filters=download_filters)

    @property
    def ssh_host(self):
        """Returns an IP address that will be used for SSH connections."""
        if self._instance_config.local_ssh_port:
            return '127.0.0.1'

        # get a public IP address of the running instance
        instance = self.instance_deployment.get_instance()
        if not instance or not instance.is_running:
            raise InstanceNotRunningError(self.instance_config.name)

        public_ip_address = instance.public_ip_address
        if not public_ip_address:
            raise ValueError('The running instance doesn\'t have a public IP address.\n'
                             'Use the "localSshPort" parameter if you want to create a tunnel to the instance.')

        return public_ip_address

    @property
    def ssh_port(self) -> int:
        if self._instance_config.local_ssh_port:
            return self._instance_config.local_ssh_port

        return 22

    @property
    def use_tmux(self) -> bool:
        return True
