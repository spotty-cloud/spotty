import os
from cloud_training import utils
from cloud_training.project_command import ProjectCommand


class SyncSessionCommand(ProjectCommand):

    def run(self):
        local_training_path = os.path.join(self._project_dir, 'training', self._model)
        s3_training_path = '/'.join([self._s3_project_dir, 'training', self._model])
        session_id = self._args.session

        print('Syncing the session "%s"...' % session_id)

        # sync the session directory (excluding checkpoints' files)
        self._aws.s3_sync(s3_training_path + '/' + session_id, os.path.join(local_training_path, session_id),
                          ['checkpoints/*'], ['checkpoints/checkpoint'])

        # get the last checkpoint name
        local_checkpoints_path = os.path.join(local_training_path, session_id, 'checkpoints')
        s3_checkpoints_path = s3_training_path + '/' + session_id + '/checkpoints'
        last_model_name = utils.get_last_checkpoint_name(os.path.join(local_checkpoints_path, 'checkpoint'))
        if not last_model_name:
            print('Checkpoint was not found')
            return True

        print('Getting the checkpoint "%s"...' % last_model_name)

        # get the last checkpoint's files
        self._aws.s3_sync(s3_checkpoints_path, local_checkpoints_path, [s3_checkpoints_path + '/*'], [last_model_name + '*'])

        print('Done')

        return True
