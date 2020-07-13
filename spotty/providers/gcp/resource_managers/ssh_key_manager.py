import os
import subprocess
from spotty.configuration import get_spotty_keys_dir
from shutil import which
from spotty.providers.instance_manager_factory import PROVIDER_GCP


class SshKeyManager(object):

    def __init__(self, project_name: str, zone: str):
        self._key_name = 'spotty-key-%s-%s' % (project_name.lower(), zone)
        self._keys_dir = get_spotty_keys_dir(PROVIDER_GCP)

    @property
    def private_key_file(self):
        return os.path.join(self._keys_dir, self._key_name)

    @property
    def public_key_file(self):
        return os.path.join(self._keys_dir, self._key_name + '.pub')

    def get_public_key_value(self):
        # generate a key if it doesn't exist
        if not os.path.isfile(self.private_key_file) or not os.path.isfile(self.public_key_file):
            self._generate_ssh_key()

        # read the public key value
        with open(self.public_key_file, 'r') as f:
            public_key_value = f.read().split()[1]

        return public_key_value

    def _generate_ssh_key(self):
        # delete the private key file if it already exists
        if os.path.isfile(self.private_key_file):
            os.unlink(self.private_key_file)

        # create a provider subdirectory
        if not os.path.isdir(self._keys_dir):
            os.makedirs(self._keys_dir, mode=0o755, exist_ok=True)

        # check that the "ssh-keygen" tool is installed
        ssh_keygen_cmd = 'ssh-keygen'
        if which(ssh_keygen_cmd) is None:
            raise ValueError('"ssh-keygen" command not found.')

        generate_key_cmd = [ssh_keygen_cmd, '-t', 'rsa', '-N', '', '-f', self.private_key_file, '-q']

        # generate a key pair
        res = subprocess.run(generate_key_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode:
            raise subprocess.CalledProcessError(res.returncode, generate_key_cmd)
