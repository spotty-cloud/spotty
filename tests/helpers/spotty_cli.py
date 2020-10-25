import os
import shlex
from typing import List
from tests.helpers.cli import run


class SpottyCli:

    def __init__(self, instance_name: str):
        self._instance_name = instance_name

    def is_instance_running(self) -> bool:
        """Checks whether the instance is running or not."""
        exit_code, _ = run('spotty status ' + self._instance_name, capture_output=True, assert_zero_code=False)
        return exit_code == 0

    def start_instance(self):
        """Starts an instance."""
        if not self.is_instance_running():
            # start instance
            run('spotty start ' + self._instance_name)

    def list_remote_files(self) -> List[str]:
        """Returns a list of files in the project directory on the remote machine."""
        output = self.exec('find . -type f -print')
        remote_files = [os.path.normpath(file_path) for file_path in output.splitlines()]

        return remote_files

    def touch_file(self, file_path: str):
        """Returns a list of files in the project directory on the remote machine."""
        self.exec('touch ' + shlex.quote(file_path))

    def sync(self):
        """Syncs files with the remote instance."""
        _, output = run('spotty sync ' + self._instance_name, capture_output=True)

        uploaded_files = []
        downloaded_files = []
        for line in output.splitlines():
            if line.startswith('upload:'):
                uploaded_files.append(os.path.normpath(line.split()[1]))
            elif line.startswith('download:'):
                downloaded_files.append(line.split()[3].rsplit('.project/')[-1])

        return uploaded_files, downloaded_files

    def download(self, filter_pattern: str):
        """Syncs files with the remote instance."""
        _, output = run('spotty download %s -i %s' % (self._instance_name, shlex.quote(filter_pattern)),
                        capture_output=True)

        print('---')
        print(output)
        print('---')

        uploaded_files = []
        downloaded_files = []
        for line in output.splitlines():
            if line.startswith('upload:'):
                uploaded_files.append(os.path.normpath(line.split()[1]))
            elif line.startswith('download:'):
                downloaded_files.append(line.split()[3].rsplit('.project/')[-1])

        return uploaded_files, downloaded_files

    def exec(self, container_command: str):
        """Execs a custom command in the container."""
        _, output = run('spotty exec %s --no-sync -- %s' % (self._instance_name, container_command),
                        capture_output=True)

        return output
