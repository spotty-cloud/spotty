import json
import os
from argparse import Namespace
from cloud_training.abstract_command import AbstractCommand


class ProjectCommand(AbstractCommand):

    def __init__(self, args: Namespace):
        super().__init__(args)

        # check CloudTraining settings
        for key in self._settings:
            if self._settings[key] is None:
                raise ValueError('Use the "cloud-training configure" command to configure the tool.')

        # get a project dir
        self._project_dir = self._args.project_dir
        if not os.path.isabs(self._project_dir):
            self._project_dir = os.path.abspath(os.path.join(os.getcwd(), self._project_dir))

        # read a project config
        self._project_config = self._get_project_config()
        if not self._project_config:
            raise ValueError('"cloud_training.json" was not found in the project directory.')

        # set default values
        self._project_config = {**{
            'project_name': None,
            'package_name': None,
        }, **self._project_config}

        if not self._project_config['project_name']:
            raise ValueError('"project_name" is not defined in the config file.')

        if not self._project_config['package_name']:
            raise ValueError('"package_name" is not defined in the config file.')

        # update the path to the project on S3
        self._s3_project_dir = 's3://' + self._settings['s3_bucket'] \
                               + '/projects/' + self._project_config['project_name']

        if self._args.model is None:
            raise ValueError('The model is not specified.')

        self._model = self._args.model

    def _get_project_config(self):
        config = None
        config_file = os.path.join(self._project_dir, 'cloud_training.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                # set the config
                config = json.load(f)

        return config
