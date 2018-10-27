import base64
from argparse import ArgumentParser
import boto3
import subprocess
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.resources import get_instance_ip_address
from spotty.helpers.sync import sync_project_with_s3, sync_instance_with_s3
from spotty.helpers.validation import validate_instance_config
from spotty.project_resources.key_pair import KeyPairResource
from spotty.project_resources.stack import StackResource
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class RunCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'run'

    @staticmethod
    def get_description():
        return 'Run a script from configuration file inside the Docker container'

    @staticmethod
    def _validate_config(config):
        return validate_instance_config(config)

    @staticmethod
    def configure(parser: ArgumentParser):
        AbstractConfigCommand.configure(parser)
        parser.add_argument('--session-name', '-s', type=str, default=None, help='tmux session name')
        parser.add_argument('--sync', '-S', action='store_true', help='Sync the project before running the command')
        parser.add_argument('script_name', metavar='SCRIPT_NAME', type=str, help='Script name')

    def run(self, output: AbstractOutputWriter):
        project_config = self._config['project']
        instance_config = self._config['instance']
        project_name = project_config['name']
        region = instance_config['region']

        script_name = self._args.script_name
        if script_name not in self._config['scripts']:
            raise ValueError('Script "%s" is not defined in the configuration file.' % script_name)

        # get instance IP address
        stack = StackResource(None, project_name, region)
        ec2 = boto3.client('ec2', region_name=region)
        ip_address = get_instance_ip_address(ec2, stack.name)

        # sync the project with the instance
        if self._args.sync:
            output.write('Syncing the project with S3 bucket...')

            # sync the project with S3 bucket
            sync_filters = project_config['syncFilters']
            sync_project_with_s3(self._project_dir, project_name, region, sync_filters, output)

            output.write('Syncing S3 bucket with the instance...')

            # sync S3 with the instance
            sync_instance_with_s3(ip_address, project_name, region)

        # tmux session name
        session_name = self._args.session_name if self._args.session_name else 'spotty-script-%s' % script_name

        # base64 encoded user script from the configuration file
        script_base64 = base64.b64encode(self._config['scripts'][script_name].encode('utf-8')).decode('utf-8')

        # remote path where the script will be uploaded
        script_path = '/tmp/docker/%s.sh' % script_name

        # log file for the script outputs
        script_log_file = '/var/log/spotty-run/%s.log' % script_name

        # command to attach user to existing tmux session
        attach_session_cmd = subprocess.list2cmdline(['tmux', 'attach', '-t', session_name, '>', '/dev/null', '2>&1'])

        # command to upload user script to the instance
        upload_script_cmd = subprocess.list2cmdline(['echo', script_base64, '|', 'base64', '-d', '>', script_path])

        # command to log the time when user script started
        start_time_cmd = subprocess.list2cmdline(['echo', '-e', '\\nScript started: `date \'+%Y-%m-%d %H:%M:%S\'`\\n',
                                                  '>>', script_log_file])

        # command to run user script inside the docker container
        docker_cmd = subprocess.list2cmdline(['sudo', '/scripts/container_bash.sh', '-xe', script_path, '2>&1',
                                              '|', 'tee', '-a', script_log_file])

        # command to create new tmux session and run user script
        new_session_cmd = subprocess.list2cmdline(['tmux', 'new', '-s', session_name,
                                                   '%s && %s' % (start_time_cmd, docker_cmd)])

        # composition of the commands: if user cannot be attached to the tmux session (assume the session doesn't
        # exist), then we uploading user script to the instance, creating new tmux session and running that script
        # inside the Docker container
        remote_cmd = '%s || (%s && %s)' % (attach_session_cmd, upload_script_cmd, new_session_cmd)

        # connect to the instance and run the command above
        host = 'ubuntu@%s' % ip_address
        key_path = KeyPairResource(None, project_name, region).key_path
        ssh_command = ['ssh', '-i', key_path, '-o', 'StrictHostKeyChecking no', host, '-t', remote_cmd]

        subprocess.call(ssh_command)
