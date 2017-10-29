import os
from cloud_training import utils
from cloud_training.aws import Aws
from cloud_training.project_command import ProjectCommand


class SyncSessionCommand(ProjectCommand):

    def run(self):
        local_training_path = os.path.join(self._project_dir, 'training', self._model)
        s3_training_path = '/'.join([self._s3_project_dir, 'training', self._model])
        aws = Aws(self._settings['region'])

        if self._args.session == 0:
            print('Session was not specified. Getting the last session ID...')

            # sync the last_session file
            aws.s3_sync(s3_training_path, local_training_path, ['*'], ['last_session'])

            # read the last session ID
            with open(os.path.join(local_training_path, 'last_session'), 'r') as f:
                session_id = int(f.read())
        else:
            session_id = self._args.session

        print('Syncing the session #' + str(session_id) + '...')

        # sync the session directory (excluding checkpoints' files)
        session_dir = 'session_' + str(session_id)
        aws.s3_sync(s3_training_path + '/' + session_dir, os.path.join(local_training_path, session_dir),
                    ['checkpoints/*'], ['checkpoints/checkpoint'])

        # get the last checkpoint name
        local_checkpoints_path = os.path.join(local_training_path, session_dir, 'checkpoints')
        s3_checkpoints_path = s3_training_path + '/' + session_dir + '/checkpoints'
        last_model_name = utils.get_last_checkpoint_name(os.path.join(local_checkpoints_path, 'checkpoint'))
        if not last_model_name:
            print('Checkpoint was not found')
            return True

        print('Getting the checkpoint "%s"...' % last_model_name)

        # get the last checkpoint's files
        aws.s3_sync(s3_checkpoints_path, local_checkpoints_path, [s3_checkpoints_path + '/*'], [last_model_name + '*'])

        print('Done')

        return True
