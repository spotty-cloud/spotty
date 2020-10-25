import os
import unittest
from spotty.deployment.utils.commands import get_script_command
from spotty.deployment.utils.user_scripts import render_script
from tests.helpers.spotty_cli import SpottyCli


class TestInstanceRun(unittest.TestCase):

    spotty = SpottyCli('local-1')

    @classmethod
    def setUpClass(cls):
        # set local project directory
        project_dir = os.path.join(os.path.dirname(__file__), 'data', 'test-project')
        os.chdir(project_dir)

        # start AWS instance
        cls.spotty.start_instance()

    def test_script_arguments(self):
        script_name = 'echo'
        script_content = 'echo test $1 $2'

        # no arguments
        script_command = get_script_command(script_name, script_content, script_args=None, logging=False)
        output = self.spotty.exec(script_command)
        self.assertEqual(output.strip(), 'test')

        # custom arguments
        script_command = get_script_command(script_name, script_content, script_args=['arg 1', 'arg 2'], logging=False)
        output = self.spotty.exec(script_command)
        self.assertEqual(output.strip(), 'test arg 1 arg 2')

    def test_script_params(self):

        script_content = 'echo test {{PARAM_1}} {{PARAM_2}}'
        script_params = {
            'PARAM_2': 'param 2',
        }

        script_content = render_script(script_content, script_params)

        self.assertEqual(script_content, '#!/usr/bin/env bash\n\n'
                                         'set -xe\n\n'
                                         'echo test  param 2')

    def test_script_logging(self):
        script_name = 'echo'
        script_content = 'echo test'

        # run the script with logging
        script_command = get_script_command(script_name, script_content, script_args=None, logging=True)
        output = self.spotty.exec(script_command)
        self.assertEqual(output.strip(), 'test')

        # read the latest log file
        output = self.spotty.exec('bash -c \'cat /var/log/spotty/run/$(ls -rt /var/log/spotty/run | tail -n1)\'')
        self.assertEqual(output.splitlines()[0], 'test')


if __name__ == '__main__':
    unittest.main()
