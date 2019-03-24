import os
import boto3
from spotty.configuration import get_spotty_keys_dir


class KeyPairResource(object):

    def __init__(self, project_name: str, region: str):
        self._ec2 = boto3.client('ec2', region_name=region)
        self._region = region
        self._key_name = 'spotty-key-%s-%s' % (project_name.lower(), region)

    @property
    def key_path(self):
        return os.path.join(get_spotty_keys_dir(), self._key_name)

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

            # create new key
            res = self._ec2.create_key_pair(KeyName=self._key_name)

            # save the key to spotty directory
            with open(key_path, 'w') as f:
                f.write(res['KeyMaterial'])

            os.chmod(key_path, 0o600)

        return self._key_name

    def delete_key(self):
        # delete EC2 Key Pair
        if self._ec2_key_exists():
            self._ec2.delete_key_pair(KeyName=self._key_name)

        # delete the key file
        key_path = self.key_path
        if os.path.isfile(key_path):
            os.unlink(key_path)

    def _ec2_key_exists(self):
        res = self._ec2.describe_key_pairs(Filters=[{'Name': 'key-name', 'Values': [self._key_name]}])
        if 'KeyPairs' not in res:
            return False

        if len(res['KeyPairs']) > 1:
            raise ValueError('Several keys with the name "%s" found.' % self._key_name)

        return bool(res['KeyPairs'])
