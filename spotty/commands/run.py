import base64
from argparse import ArgumentParser
import subprocess
import re
import pystache
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.config import get_instance_config
from spotty.helpers.validation import validate_instance_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.instance_factory import InstanceFactory


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
        parser.add_argument('--sync', '-S', action='store_true', help='Sync the project before running the script')
        parser.add_argument('script_name', metavar='SCRIPT_NAME', type=str, help='Script name')
        parser.add_argument('script_params', metavar='PARAMETER=VALUE', nargs='*', type=str, help='Script parameters')

    def run(self, output: AbstractOutputWriter):
        project_name = self._config['project']['name']
        sync_filters = self._config['project']['syncFilters']

        if self._args.instance_name and '=' in self._args.script_name:
            # fix argument values if at least two arguments provided and the second argument is a script parameter
            instance_name = None
            script_name = self._args.instance_name
            script_params = [self._args.script_name] + self._args.script_params
        else:
            instance_name = self._args.instance_name
            script_name = self._args.script_name
            script_params = self._args.script_params

        # get the instance config
        instance_config = get_instance_config(self._config['instances'], instance_name)

        # check that the script exists
        if script_name not in self._config['scripts']:
            raise ValueError('Script "%s" is not defined in the configuration file.' % script_name)

        # get script parameters
        params = {}
        for param in script_params:
            match = re.match('(\w+)=(.*)', param)
            if not match:
                raise ValueError('Invalid script parameter: "%s"' % param)

            param_name, param_value = match.groups()
            if param_name in params:
                raise ValueError('Parameter "%s" defined twice' % param_name)

            params[param_name] = param_value

        # check that the instance is started
        instance = InstanceFactory.get_instance(project_name, instance_config)
        if not instance.is_started():
            raise ValueError('Instance "%s" is not started.' % instance_name)

        # sync the project with the instance
        if self._args.sync:
            instance.sync(self._project_dir, sync_filters, output)

        # get instance info
        instance_info = instance.get_info()
        ip_address = instance_info.ip_address
        key_path = instance_info.ssh_key_path

        # tmux session name
        session_name = self._args.session_name if self._args.session_name else 'spotty-script-%s' % script_name

        # base64 encoded user script from the configuration file
        script_content = pystache.render(self._config['scripts'][script_name], script_params)
        script_base64 = base64.b64encode(script_content.encode('utf-8')).decode('utf-8')

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
        # exist), then we're uploading user script to the instance, creating new tmux session and running that script
        # inside the Docker container
        remote_cmd = '%s || (%s && %s)' % (attach_session_cmd, upload_script_cmd, new_session_cmd)

        # connect to the instance and run the command above
        host = 'ubuntu@%s' % ip_address
        ssh_command = ['ssh', '-i', key_path, '-o', 'StrictHostKeyChecking no', host, '-t', remote_cmd]

        subprocess.call(ssh_command)
