import os
import unittest
from tests.helpers.cli import touch_file
from tests.helpers.spotty_cli import SpottyCli


class TestInstanceDownload(unittest.TestCase):

    spotty = SpottyCli('aws-1')

    @classmethod
    def setUpClass(cls):
        # set local project directory
        project_dir = os.path.join(os.path.dirname(__file__), 'data', 'test-project')
        os.chdir(project_dir)

        # make sure the instance is running
        assert cls.spotty.is_instance_running()

        # make sure all files are synced
        local_files = sorted([
            'ignored-dir/included-file',
            'local-file',
            'spotty.yaml',
        ])

        remote_files = cls.spotty.list_remote_files()
        assert set(local_files).issubset(set(remote_files))

    def test_download_file(self):
        # touch the remote file
        self.spotty.touch_file('local-file')

        # download the file
        uploaded_files, downloaded_files = self.spotty.download('local-file')

        # only 1 file should be uploaded and downloaded
        self.assertEqual(len(uploaded_files), 1)
        self.assertEqual(len(downloaded_files), 1)

        # the updated file uploaded
        self.assertIn('local-file', uploaded_files)
        self.assertIn('local-file', downloaded_files)

        # download the file again
        uploaded_files, downloaded_files = self.spotty.download('local-file')

        # no files should be uploaded or downloaded
        self.assertFalse(uploaded_files)
        self.assertFalse(downloaded_files)

        # touch the remote file, then touch the local file
        self.spotty.touch_file('local-file')
        touch_file('local-file')

        # download the remote file again
        uploaded_files, downloaded_files = self.spotty.download('local-file')

        # the file should be uploaded, but not downloaded as the local file is newer than the remote one
        self.assertEqual(len(uploaded_files), 1)
        self.assertFalse(downloaded_files)
        self.assertIn('local-file', uploaded_files)

    def test_wildcard(self):
        # touch remote files
        self.spotty.touch_file('ignored-dir/ignored-file')
        self.spotty.touch_file('ignored-dir/included-file')

        # download the files
        uploaded_files, downloaded_files = self.spotty.download('ignored-dir/*')

        # 2 files should be uploaded and downloaded
        self.assertEqual(len(uploaded_files), 2)
        self.assertEqual(len(downloaded_files), 2)
        self.assertIn('ignored-dir/ignored-file', uploaded_files)
        self.assertIn('ignored-dir/ignored-file', downloaded_files)
        self.assertIn('ignored-dir/included-file', uploaded_files)
        self.assertIn('ignored-dir/included-file', downloaded_files)

        # touch one of the remote files
        self.spotty.touch_file('ignored-dir/ignored-file')

        # download the files
        uploaded_files, downloaded_files = self.spotty.download('ignored-dir/*')

        # 1 file should be uploaded and downloaded
        self.assertEqual(len(uploaded_files), 1)
        self.assertEqual(len(downloaded_files), 1)
        self.assertIn('ignored-dir/ignored-file', uploaded_files)
        self.assertIn('ignored-dir/ignored-file', downloaded_files)


if __name__ == '__main__':
    unittest.main()
