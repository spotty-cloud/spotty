import os
import zipfile


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
        print('No files to zip')
        return

    print('Zipping files...')

    for (file_path, filename, zip_file_path) in zip_files_list:
        print('File: ' + file_path)
        zip_file = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)
        zip_file.write(file_path, filename)
        zip_file.close()

    print('Done')


def unzip_dir(path):
    unzip_files_list = []
    for root, dirs, filenames in os.walk(path):
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
        return

    print('Unzipping files...')

    for (zip_file_path, extract_dir) in unzip_files_list:
        print('File: ' + zip_file_path)
        zip_ref = zipfile.ZipFile(zip_file_path, 'r')
        zip_ref.extractall(extract_dir)
        zip_ref.close()

    print('Done')

unzip_dir('../../../ruTextNorm/data')
