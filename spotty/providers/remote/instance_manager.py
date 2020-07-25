import logging
import subprocess
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.abstract_ssh_instance_manager import AbstractSshInstanceManager
from spotty.providers.remote.config.instance_config import InstanceConfig
from spotty.providers.remote.helpers.rsync import get_upload_command, check_rsync_installed, get_download_command


class InstanceManager(AbstractSshInstanceManager):

    instance_config: InstanceConfig

    def _get_instance_config(self, instance_config: dict) -> InstanceConfig:
        """Validates the instance config and returns an InstanceConfig object."""
        return InstanceConfig(instance_config, self.project_config)

    def is_running(self):
        """Assuming the remote instance is running."""
        return True

    def clean(self, output: AbstractOutputWriter):
        pass

    def sync(self, output: AbstractOutputWriter, dry_run=False):

        output.write('Syncing files with the instance...')

        # check rsync is installed
        check_rsync_installed()

        # sync the project with the instance
        rsync_cmd = get_upload_command(
            local_dir=self.project_config.project_dir,
            remote_dir=self.instance_config.host_project_dir,
            ssh_user=self.ssh_user,
            ssh_host=self.ssh_host,
            ssh_key_path=self.ssh_key_path,
            ssh_port=self.ssh_port,
            filters=self.project_config.sync_filters,
            use_sudo=(not self.instance_config.container_config.run_as_host_user),
            dry_run=dry_run,
        )

        # execute the command locally
        logging.debug('rsync command: ' + rsync_cmd)
        exit_code = subprocess.call(rsync_cmd, shell=True)
        if exit_code != 0:
            raise ValueError('Failed to upload files to the instance.')

    def download(self, download_filters: list, output: AbstractOutputWriter, dry_run=False):

        output.write('Downloading files from the instance...')

        # check rsync is installed
        check_rsync_installed()

        # sync the project with the instance
        rsync_cmd = get_download_command(
            local_dir=self.project_config.project_dir,
            remote_dir=self.instance_config.host_project_dir,
            ssh_user=self.ssh_user,
            ssh_host=self.ssh_host,
            ssh_key_path=self.ssh_key_path,
            ssh_port=self.ssh_port,
            filters=download_filters,
            use_sudo=(not self.instance_config.container_config.run_as_host_user),
            dry_run=dry_run,
        )

        # execute the command locally
        logging.debug('rsync command: ' + rsync_cmd)
        exit_code = subprocess.call(rsync_cmd, shell=True)
        if exit_code != 0:
            raise ValueError('Failed to download files from the instance.')

    @property
    def ssh_host(self) -> str:
        return self.instance_config.host

    @property
    def ssh_key_path(self) -> str:
        return self.instance_config.key_path

    @property
    def ssh_port(self) -> int:
        return self.instance_config.port
