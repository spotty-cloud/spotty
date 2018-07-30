import base64
from argparse import ArgumentParser
import boto3
import subprocess
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.commands.helpers.validation import validate_instance_config
from spotty.commands.project_resources.key_pair import KeyPairResource
from spotty.commands.project_resources.stack import StackResource
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class RunCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'run'

    @staticmethod
    def _validate_config(config):
        return validate_instance_config(config)

    @staticmethod
    def configure(parser: ArgumentParser):
        AbstractConfigCommand.configure(parser)
        parser.add_argument('--session-name', '-s', type=str, default=None, help='tmux session name')
        parser.add_argument('script_name', metavar='SCRIPT_NAME', type=str, help='Script name')

    def run(self, output: AbstractOutputWriter):
        project_config = self._config['project']
        instance_config = self._config['instance']
        project_name = project_config['name']
        region = instance_config['region']

        script_name = self._args.script_name
        if script_name not in self._config['scripts']:
            raise ValueError('Script "%s" is not defined in the configuration file.' % script_name)

        cf = boto3.client('cloudformation', region_name=region)
        stack = StackResource(cf, project_name, region)

        # check that the stack exists
        if not stack.stack_exists():
            raise ValueError('Stack "%s" doesn\'t exists.' % stack.name)

        # get instance IP address
        info = stack.get_stack_info()
        ip_address = [row['OutputValue'] for row in info['Outputs'] if row['OutputKey'] == 'InstanceIpAddress'][0]

        host = 'ubuntu@%s' % ip_address
        key_path = KeyPairResource(None, project_name, region).key_path

        # run a script or attach to already running one
        session_name = self._args.session_name if self._args.session_name else 'spotty-script-%s' % script_name
        script_base64 = base64.b64encode(self._config['scripts'][script_name].encode('utf-8')).decode('utf-8')
        script_path = '/tmp/docker/%s.sh' % script_name
        working_dir = instance_config['docker']['workingDir']

        attach_session_cmd = subprocess.list2cmdline(['tmux', 'attach', '-t', session_name])
        upload_script_cmd = subprocess.list2cmdline(['echo', script_base64, '|', 'base64', '-d', '>', script_path])
        docker_cmd = subprocess.list2cmdline(['sudo', 'docker', 'exec', '-it', '-w', working_dir, 'spotty',
                                              '/bin/bash', '-xe', script_path, '2>&1', '|', 'sudo', 'tee', '-a',
                                              '/var/log/spotty-run/%s.log' % session_name])
        new_session_cmd = subprocess.list2cmdline(['tmux', 'new', '-s', session_name, docker_cmd])


        remote_cmd = '%s || (%s && %s)' % (attach_session_cmd, upload_script_cmd, new_session_cmd)
        ssh_command = ['ssh', '-i', key_path, '-o', 'StrictHostKeyChecking no', host, '-t', remote_cmd]

        subprocess.call(ssh_command)
