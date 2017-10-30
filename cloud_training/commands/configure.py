from cloud_training import configure
from cloud_training.abstract_command import AbstractCommand


class ConfigureCommand(AbstractCommand):

    def run(self):
        profile = self._args.profile

        # read saved AWS credentials
        aws_credentials = configure.get_aws_credentials_settings(profile)

        # ask the user to update AWS credentials
        inputs = {
            'aws_access_key_id': 'AWS Access Key ID [%s]: ',
            'aws_secret_access_key': 'AWS Secret Access Key [%s]: ',
        }

        for key in inputs:
            display_value = aws_credentials[key]
            if aws_credentials[key]:
                display_value = '****************%s' % aws_credentials[key][-4:]

            aws_credentials[key] = self.get_input(inputs[key] % str(display_value), aws_credentials[key])

        # read saved AWS config
        aws_config = configure.get_aws_config_settings(profile)

        # ask the user to update AWS config
        inputs = {
            'region': 'Region name [%s]: ',
        }

        for key in inputs:
            aws_config[key] = self.get_input(inputs[key] % str(aws_config[key]), aws_config[key])

        # read saved CloudTraining config
        settings = configure.get_ct_settings(profile)

        # ask the user to update CloudTraining config
        inputs = {
            's3_bucket': 'S3 bucket name [%s]: ',
            'image_id': 'Image ID [%s]: ',
            'root_snapshot_id': 'Root EBS volume snapshot ID [%s]: ',
            'root_volume_size': 'Root EBS volume size (GB) [%s]: ',
            'training_volume_size': 'Training EBS volume size (GB) [%s]: ',
            'key_name': 'EC2 key pair name [%s]: ',
            'instance_type': 'Default instance type [%s]: ',
        }

        for key in inputs:
            settings[key] = self.get_input(inputs[key] % str(settings[key]), settings[key])

        # save all config files
        aws_profile = configure.get_aws_profile_name(profile)
        configure.save_profile_settings(configure.get_aws_credentials_file_path(), aws_profile, aws_credentials)
        configure.save_profile_settings(configure.get_aws_config_file_path(), 'profile ' + aws_profile, aws_config)
        configure.save_profile_settings(configure.get_ct_config_file_path(), profile, settings)

        return True

    def get_input(self, message: str, default_value=None):
        value = input(message)
        if not value:
            if default_value is not None:
                value = default_value
            else:
                self._print('Value is required')
                value = self.get_input(message)

        return value
