import os
import unittest
from tests.helpers.cli import touch_file
from tests.helpers.spotty_cli import SpottyCli


class TestInstanceSync(unittest.TestCase):

    spotty = SpottyCli('aws-1')

    @classmethod
    def setUpClass(cls):
        # set local project directory
        project_dir = os.path.join(os.path.dirname(__file__), 'data', 'test-project')
        os.chdir(project_dir)

        # start AWS instance
        cls.spotty.start_instance()

        # make sure all files are synced
        local_files = sorted([
            'ignored-dir/included-file',
            'local-file',
            'spotty.yaml',
        ])

        remote_files = cls.spotty.list_remote_files()
        assert set(local_files).issubset(set(remote_files))

    def test_update_local_file(self):
        # touch local file
        touch_file('ignored-dir/included-file')
        touch_file('ignored-dir/ignored-file')

        # sync files with the remote instance
        uploaded_files, downloaded_files = self.spotty.sync()

        # only 1 file should be uploaded and downloaded
        self.assertEqual(len(uploaded_files), 1)
        self.assertEqual(len(downloaded_files), 1)

        # the updated file uploaded
        self.assertIn('ignored-dir/included-file', uploaded_files)
        self.assertIn('ignored-dir/included-file', downloaded_files)

        # the untouched file not uploaded
        self.assertNotIn('local-file', uploaded_files)
        self.assertNotIn('local-file', downloaded_files)

        # the ignored file not uploaded
        self.assertNotIn('ignored-dir/ignored-file', uploaded_files)
        self.assertNotIn('ignored-dir/ignored-file', downloaded_files)

    def test_update_remote_file(self):
        # touch remote files
        self.spotty.touch_file('local-file')
        self.spotty.touch_file('ignored-dir/ignored-file')

        # sync files with the remote instance
        uploaded_files, downloaded_files = self.spotty.sync()

        # local files were not changed, so should not be uploaded
        self.assertFalse(uploaded_files, 'No files should be uploaded')

        # the remote file that is newer still will be overwritten with the older file
        # from the bucket (this is the current "aws s3 sync" behaviour)
        self.assertIn('local-file', downloaded_files)
        self.assertEqual(len(downloaded_files), 1)

        # the ignored file should not be overwritten
        self.assertNotIn('ignored-dir/ignored-file', downloaded_files)

    def test_new_remote_file(self):
        # create new remote file
        self.spotty.touch_file('new-remote-file')

        # make sure file was created
        remote_files = self.spotty.list_remote_files()
        self.assertIn('new-remote-file', remote_files)

        # make sure the file with this name doesn't exist locally
        self.assertFalse(os.path.isfile('new-remote-file'))

        # sync files
        self.spotty.sync()

        # make sure the file wasn't delete on the remote machine
        remote_files = self.spotty.list_remote_files()
        self.assertIn('new-remote-file', remote_files)


if __name__ == '__main__':
    unittest.main()
