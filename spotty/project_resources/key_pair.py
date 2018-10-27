import os
from botocore.exceptions import ClientError
from spotty.configuration import get_spotty_keys_dir


class KeyPairResource(object):

    def __init__(self, ec2, project_name: str, region: str):
        self._ec2 = ec2
        self._region = region
        self._key_name = 'spotty-%s-%s' % (project_name, region)

    @property
    def key_path(self):
        return os.path.join(get_spotty_keys_dir(), self._key_name)

    def create_key(self):
        key_path = self.key_path
        key_file_exists = os.path.isfile(key_path)
        aws_key_exists = self._key_exists()

        if not aws_key_exists or not key_file_exists:
            # remove key from AWS (key file not found)
            if aws_key_exists:
                self._ec2.delete_key_pair(KeyName=self._key_name)

            # create new key
            res = self._ec2.create_key_pair(KeyName=self._key_name)

            # save the key to spotty directory
            with open(key_path, 'w') as f:
                f.write(res['KeyMaterial'])

            os.chmod(key_path, 0o600)

        return self._key_name

    def delete_key(self):
        if self._key_exists():
            self._ec2.delete_key_pair(KeyName=self._key_name)

        key_path = self.key_path
        if os.path.isfile(key_path):
            os.unlink(key_path)

    def _key_exists(self):
        key_exists = True
        try:
            self._ec2.describe_key_pairs(KeyNames=[self._key_name])
        except ClientError:
            key_exists = False

        return key_exists
