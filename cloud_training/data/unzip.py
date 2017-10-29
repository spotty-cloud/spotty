"""
   This script is being uploaded to the remote server before the training process
   It shouldn't depend on the files from this project
"""

import argparse
import os
import zipfile


parser = argparse.ArgumentParser()
parser.add_argument('path', type=str, help='Path to directory with zipped files')

args = parser.parse_args()

unzip_files_list = []
for root, dirs, filenames in os.walk(args.path):
    for zip_filename in filenames:
        # skip non-zip files
        _, ext = os.path.splitext(zip_filename)
        if ext != '.zip':
            continue

        # skip already unarchived files
        zip_file_path = os.path.join(root, zip_filename)
        file_path = zip_file_path[:-4]
        if os.path.exists(file_path):
            continue

        unzip_files_list.append((zip_file_path, root))

if not unzip_files_list:
    print('No files to unzip')
    exit()

print('Unzipping files...')

for (zip_file_path, extract_dir) in unzip_files_list:
    print('File: ' + zip_file_path)
    zip_ref = zipfile.ZipFile(zip_file_path, 'r')
    zip_ref.extractall(extract_dir)
    zip_ref.close()

print('Done')
