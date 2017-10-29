import base64
import os
import time
from cloud_training import utils
from cloud_training.aws import Aws
from cloud_training.project_command import ProjectCommand


class TrainCommand(ProjectCommand):
    def run(self):
        aws = Aws(self._settings['region'])
        instance_type = self._args.instance_type if self._args.instance_type else self._settings['instance_type']

        # get a spot price for requested instance type
        prices = aws.spot_price(instance_type)
        if not prices:
            print('Can\'t get spot instance prices')
            return False

        min_price = float(min(prices.values()))
        max_price = min_price * 1.25

        # ask the user the max price
        print('Spot instance price for "%s" is %.03f' % (instance_type, min_price))
        user_price = input('Set your max price [default: %.03f]: ' % max_price)
        if user_price:
            max_price = float(user_price)

        # zip files in the data directory
        print('Compressing files in the data directory...')
        data_dir = os.path.join(self._project_dir, 'data')
        utils.zip_dir(data_dir)

        # sync the project
        print('Syncing the project with S3...')
        last_session_file = os.path.join(self._project_dir, 'training', self._model, 'last_session')
        exclude = [os.path.join(self._project_dir, '*')]
        include = [os.path.join(data_dir, '*.zip'),
                   os.path.join(self._project_dir, self._project_config['package_name'], '*'),
                   last_session_file]
        aws.s3_sync(self._project_dir, self._s3_project_dir, exclude, include)

        if self._args.session:
            # sync the session directory if it was specified
            session_id = self._args.session

            print('Syncing the session #' + str(session_id) + '...')

            # sync the session directory (excluding checkpoints' files)
            session_dir = 'session_' + str(session_id)
            local_session_dir = os.path.join(self._project_dir, 'training', self._model, session_dir)
            s3_session_dir = self._s3_project_dir + '/training/' + self._model + '/' + session_dir
            aws.s3_sync(local_session_dir, s3_session_dir, [os.path.join('checkpoints', '*')],
                        [os.path.join('checkpoints', 'checkpoint')])

            # get the last checkpoint name
            local_checkpoints_dir = os.path.join(local_session_dir, 'checkpoints')
            last_model_name = utils.get_last_checkpoint_name(os.path.join(local_checkpoints_dir, 'checkpoint'))

            # send the last checkpoint's files to S3
            s3_checkpoint_dir = s3_session_dir + '/checkpoints'
            aws.s3_sync(local_checkpoints_dir, s3_checkpoint_dir, [os.path.join(local_checkpoints_dir, '*')],
                        [last_model_name + '*'])
        else:
            # increment the session ID locally (in case of a new local training, to prevent an overriding)
            if os.path.exists(last_session_file):
                with open(last_session_file, mode='r') as f:
                    new_session_id = int(f.read()) + 1
                with open(last_session_file, mode='w') as f:
                    f.write(str(new_session_id))
            else:
                with open(last_session_file, mode='w') as f:
                    f.write('1')

        # prepare "User Data" for an instance
        with open(utils.data_dir('user_data.sh')) as f:
            user_data = f.read()

        with open(utils.data_dir('unzip.py')) as f:
            unzip_script_base64 = base64.b64encode(f.read().encode()).decode()

        user_data_replacements = {
            'aws_access_key_id': self._settings['aws_access_key_id'],
            'aws_secret_access_key': self._settings['aws_secret_access_key'],
            'aws_region': self._settings['region'],
            'project_name': self._project_config['project_name'],
            'package_name': self._project_config['package_name'],
            's3_project_dir': self._s3_project_dir,
            'model_name': self._model,
            'session_id': str(self._args.session),
            'conda_env': self._args.conda_env if self._args.conda_env else '',
            'unzip_script_base64': unzip_script_base64
        }

        for key in user_data_replacements:
            user_data = user_data.replace('{{' + key + '}}', user_data_replacements[key])

        # run a spot instance
        request = aws.create_spot_request(instance_type, self._settings['image_id'], self._settings['root_snapshot_id'],
                                          int(self._settings['root_volume_size']),
                                          int(self._settings['training_volume_size']), user_data,
                                          self._settings['key_name'], max_price)
        if not request:
            print('Can\'t create a spot instance request')
            return False

        request_id = request['SpotInstanceRequestId']
        request_status = request['Status']['Code']

        if request_status != 'pending-evaluation':
            print('Request is failed (status=%s). Message: %s' % (request_status, request['Status']['Message']))
            return False

        print('Waiting for the "active" status for the request...')

        # waiting for the "active" status
        waiting_statuses = {'pending-evaluation', 'pending-fulfillment'}
        while request_status in waiting_statuses:
            request = aws.get_spot_request(request_id)
            request_status = request['Status']['Code']
            time.sleep(3)

        if request_status != 'fulfilled':
            print('Request is failed (status=%s). Message: %s' % (request_status, request['Status']['Message']))
            return False

        # tag the instance
        aws.create_tag([request['InstanceId'], request_id], 'model',
                       '%s-%s' % (self._project_config['project_name'], self._model))

        # get the IP address
        instance = aws.get_instance_by_id(request['InstanceId'])
        print('IP address of the instance: ' + instance['PublicIpAddress'])

        print('Done')

        return True
