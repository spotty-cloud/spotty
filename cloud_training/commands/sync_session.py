import logging
import os
from cloud_training.abstract_command import AbstractCommand
from cloud_training.aws import Aws


class SyncSessionCommand(AbstractCommand):
    def check(self):
        if not self._args.model:
            logging.error('The model is not specified')
            return False

        return True

    def run(self):
        s3_project_dir = self._config['aws_s3_path']
        training_dir = 'training/' + self._args.model

        aws = Aws(self._region)

        if self._args.session == 0:
            logging.info('Session was not specified. Getting the last session ID...')

            # sync the last_session file
            res = aws.s3_sync(s3_project_dir + '/' + training_dir, os.path.join(self._project_dir, training_dir),
                              ['*'], ['last_session'])
            logging.debug('S3 output: ' + res)

            # read the last session ID
            with open(os.path.join(self._project_dir, training_dir, 'last_session'), 'r') as f:
                session_id = int(f.readline())
        else:
            session_id = self._args.session

        logging.info('Syncing the session #' + str(session_id) + '...')

        # sync the session directory (excluding checkpoints' files)
        session_dir = training_dir + '/session_' + str(session_id)
        res = aws.s3_sync(s3_project_dir + '/' + session_dir, os.path.join(self._project_dir, session_dir),
                          ['checkpoints/*'], ['checkpoints/checkpoint'])
        logging.debug('S3 output: ' + res)

        # get the last checkpoint name
        checkpoints_dir = session_dir + '/checkpoints'
        with open(os.path.join(self._project_dir, checkpoints_dir, 'checkpoint'), 'r') as f:
            last_model_str = f.readline()

        last_model_name = os.path.basename(last_model_str[24:-2])

        logging.info('Getting the checkpoint "%s"...' % last_model_name)

        # get the last checkpoint's files
        res = aws.s3_sync(s3_project_dir + '/' + checkpoints_dir, os.path.join(self._project_dir, checkpoints_dir),
                          ['*'], [last_model_name + '*'])
        logging.debug('S3 output: ' + res)

        logging.info('Done')
