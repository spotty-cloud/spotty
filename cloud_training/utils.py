import configparser
import logging
import os
import zipfile

import errno


def data_dir(path: str = ''):
    res_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if path:
        res_path = os.path.join(res_path, path)

    return res_path


def zip_dir(path: str):
    zip_files_list = []
    for root, dirs, filenames in os.walk(path):
        for filename in filenames:
            # skip zip files
            _, ext = os.path.splitext(filename)
            if ext == '.zip':
                continue

            # skip already archived files
            file_path = os.path.join(root, filename)
            zip_file_path = file_path + '.zip'
            if os.path.exists(zip_file_path):
                continue

            zip_files_list.append((file_path, filename, zip_file_path))

    if not zip_files_list:
        logging.debug('No files to zip')
        return

    logging.debug('Zipping files...')

    for (file_path, filename, zip_file_path) in zip_files_list:
        logging.debug('File: ' + file_path)
        zip_file = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)
        zip_file.write(file_path, filename)
        zip_file.close()

    logging.debug('Done')


def get_last_checkpoint_name(checkpoint_path):
    if not os.path.exists(checkpoint_path):
        return False

    with open(checkpoint_path, 'r') as f:
        last_model_str = f.readline()

    # todo: fix the absolute path which I'm getting from the EC2 instance
    return os.path.basename(last_model_str[24:-2])


def check_path(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
