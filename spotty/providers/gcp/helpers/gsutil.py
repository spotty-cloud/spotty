import json
import logging
import shlex
from shutil import which
import subprocess
import re
# from awscli.customizations.s3.fileinfo import FileInfo
# from awscli.customizations.s3.filters import Filter
import os


class GsutilCommandError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class GSUtil(object):

    def __init__(self):
        pass

    def rsync(self, from_path: str, to_path: str, delete=False, filters=None, capture_output=True,
              dry_run=False) -> str:
        if from_path.startswith('gs://') or not to_path.startswith('gs://'):
            raise NotImplementedError

        args = ['rsync', '-r']
        args += self.get_rsync_arguments(filters, delete=delete, dry_run=dry_run)
        args += [from_path, to_path]

        return self._run(args, False, capture_output=capture_output)

    @staticmethod
    def get_rsync_arguments(filters: list = None, delete: bool = False, quote: bool = False, dry_run: bool = False):
        args = []

        if dry_run:
            args.append('-n')

        if delete:
            args.append('-d')

        # file_infos = []
        # for file_path in glob.iglob(os.path.join('**', '*'), recursive=True):
        #     file_infos.append(FileInfo(file_path, src_type='local'))

        # filters = self.create_filter(filters, from_path)
        # included_file_infos = list(filters.call(file_infos))
        # exclude_files = [file_info.src for file_info in file_infos if file_info not in included_file_infos]
        # args += ['-x', '^(%s)$' % '|'.join(exclude_files)]

        if filters:
            if len(filters) > 1 or ('include' in filters[0]):
                raise ValueError('At the moment GCP provider supports only one list of exclude filters.')

            sync_filter = filters[0]
            if ('exclude' in sync_filter and 'include' in sync_filter) \
                    or ('exclude' not in sync_filter and 'include' not in sync_filter):
                raise ValueError('GCP sync filter has a wrong format.')

            path_regs = []
            for path in sync_filter['exclude']:
                path = path.replace('/', os.sep)  # fix for Windows machines
                path_regs.append(GSUtil.fnmatch_translate(path))

            filter_regex = '^(%s)$' % '|'.join(path_regs)
            args += ['-x', shlex.quote(filter_regex) if quote else filter_regex]

        return args

    def _run(self, args: list, json_format=True, capture_output=True):
        gsutil_cmd = 'gsutil'
        if which(gsutil_cmd) is None:
            raise ValueError('gsutil is not installed.')

        command_args = [gsutil_cmd, '-m'] + args

        logging.debug('gsutil command: ' + subprocess.list2cmdline(command_args))

        if capture_output:
            res = subprocess.run(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = res.stdout.decode('utf-8')

            logging.debug('gsutil command output: ' + output)

            if res.returncode:
                raise GsutilCommandError(output)

            if json_format:
                output = json.loads(output)
        else:
            res = subprocess.run(command_args)
            output = None

            if res.returncode:
                raise GsutilCommandError('"gsutil" command failed.')

        return output

    @staticmethod
    def fnmatch_translate(pat):
        """This is a copy-paste of the fnmatch.translate() function
        to prevent wrapping of a regular expression to a group.

        Translate a shell PATTERN to a regular expression.

        There is no way to quote meta-characters.
        """
        i, n = 0, len(pat)
        res = ''
        while i < n:
            c = pat[i]
            i = i + 1
            if c == '*':
                res = res + '.*'
            elif c == '?':
                res = res + '.'
            elif c == '[':
                j = i
                if j < n and pat[j] == '!':
                    j = j + 1
                if j < n and pat[j] == ']':
                    j = j + 1
                while j < n and pat[j] != ']':
                    j = j + 1
                if j >= n:
                    res = res + '\\['
                else:
                    stuff = pat[i:j].replace('\\', '\\\\')
                    i = j + 1
                    if stuff[0] == '!':
                        stuff = '^' + stuff[1:]
                    elif stuff[0] == '^':
                        stuff = '\\' + stuff
                    res = '%s[%s]' % (res, stuff)
            else:
                res = res + re.escape(c)

        return res

    # @staticmethod
    # def create_filter(filters: list, base_dir: str):
    #     if filters:
    #         filter_list = []
    #         for sync_filter in filters:
    #             if (len(sync_filter) != 1) or not ('exclude' in sync_filter or 'include' in sync_filter):
    #                 raise ValueError('GCP synchronization filters have wrong format.')
    #
    #             for filter_type in ['exclude', 'include']:
    #                 if filter_type in sync_filter:
    #                     for filter_pattern in sync_filter[filter_type]:
    #                         filter_list.append((filter_type, filter_pattern))
    #
    #         return Filter(filter_list, base_dir, base_dir)
    #     else:
    #         return Filter([], None, None)
