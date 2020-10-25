import os
from spotty.configuration import get_spotty_keys_dir
from spotty.providers.instance_manager_factory import PROVIDER_AWS


class KeyPairManager(object):

    def __init__(self, ec2, project_name: str, region: str):
        self._ec2 = ec2
        self._key_name = 'spotty-key-%s-%s' % (project_name.lower(), region)
        self._key_path = os.path.join(get_spotty_keys_dir(PROVIDER_AWS), self._key_name)

    @property
    def key_name(self):
        return self._key_name

    @property
    def key_path(self):
        return self._key_path

    def maybe_create_key(self):

        key_file_exists = os.path.isfile(self.key_path)
        ec2_key_exists = self._ec2_key_exists()

        if not ec2_key_exists or not key_file_exists:
            # remove key from AWS (key file not found)
            if ec2_key_exists:
                self._ec2.delete_key_pair(KeyName=self._key_name)

            # remove the key file (in case it was the old path)
            if key_file_exists:
                os.unlink(self.key_path)

            # create new key
            res = self._ec2.create_key_pair(KeyName=self._key_name)

            # create a provider subdirectory
            keys_dir = os.path.dirname(self.key_path)
            if not os.path.isdir(keys_dir):
                os.makedirs(keys_dir, mode=0o755, exist_ok=True)

            # save the key to the new path
            with open(self.key_path, 'w') as f:
                f.write(res['KeyMaterial'])

            os.chmod(self.key_path, 0o600)

    def delete_key(self):
        # delete EC2 Key Pair
        if self._ec2_key_exists():
            self._ec2.delete_key_pair(KeyName=self._key_name)

        # delete the key file
        if os.path.isfile(self.key_path):
            os.unlink(self.key_path)

    def _ec2_key_exists(self):
        res = self._ec2.describe_key_pairs(Filters=[{'Name': 'key-name', 'Values': [self._key_name]}])
        if 'KeyPairs' not in res:
            return False

        if len(res['KeyPairs']) > 1:
            raise ValueError('Several keys with the name "%s" found.' % self._key_name)

        return bool(res['KeyPairs'])
