import os
import boto3
from spotty.configuration import get_spotty_keys_dir


class KeyPairResource(object):

    def __init__(self, project_name: str, region: str, provider_name: str):
        self._ec2 = boto3.client('ec2', region_name=region)
        self._region = region
        self._key_name = 'spotty-key-%s-%s' % (project_name.lower(), region)
        self._new_key_path = os.path.join(get_spotty_keys_dir(), provider_name, self._key_name)
        # TODO: remove from future versions of Spotty
        self._old_key_path = os.path.join(get_spotty_keys_dir(), self._key_name)

    @property
    def key_path(self):
        if os.path.isfile(self._old_key_path) and not os.path.isfile(self._new_key_path):
            key_path = self._old_key_path
        else:
            key_path = self._new_key_path

        return key_path

    def get_or_create_key(self, dry_run=False):
        if dry_run:
            return self._key_name

        key_path = self.key_path
        key_file_exists = os.path.isfile(key_path)
        ec2_key_exists = self._ec2_key_exists()

        if not ec2_key_exists or not key_file_exists:
            # remove key from AWS (key file not found)
            if ec2_key_exists:
                self._ec2.delete_key_pair(KeyName=self._key_name)

            # remove the key file (in case it was the old path)
            if key_file_exists:
                os.unlink(key_path)

            # create new key
            res = self._ec2.create_key_pair(KeyName=self._key_name)

            # create a provider subdirectory
            keys_dir = os.path.dirname(self._new_key_path)
            if not os.path.isdir(keys_dir):
                os.makedirs(keys_dir, mode=0o755, exist_ok=True)

            # save the key to the new path
            with open(self._new_key_path, 'w') as f:
                f.write(res['KeyMaterial'])

            os.chmod(key_path, 0o600)

        return self._key_name

    def delete_key(self):
        # delete EC2 Key Pair
        if self._ec2_key_exists():
            self._ec2.delete_key_pair(KeyName=self._key_name)

        # delete the key file
        if os.path.isfile(self._new_key_path):
            os.unlink(self._new_key_path)

        if os.path.isfile(self._old_key_path):
            os.unlink(self._old_key_path)

    def _ec2_key_exists(self):
        res = self._ec2.describe_key_pairs(Filters=[{'Name': 'key-name', 'Values': [self._key_name]}])
        if 'KeyPairs' not in res:
            return False

        if len(res['KeyPairs']) > 1:
            raise ValueError('Several keys with the name "%s" found.' % self._key_name)

        return bool(res['KeyPairs'])
