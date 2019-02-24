import os
import random
import string
import errno


def package_dir(path: str = ''):
    """Returns an absolute path to the "spotty" package directory.

    Args:
        path: A relative path to add to the package path.

    """
    res_path = os.path.dirname(os.path.abspath(__file__))
    if path:
        res_path = os.path.join(res_path, path)

    return res_path


def check_path(path):
    """Creates a directory if it doesn't exist."""
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise


def random_string(length: int, chars: str = string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))


def filter_list(list_of_dicts, key_name, value):
    return [row for row in list_of_dicts if row[key_name] == value]


def render_table(table: list, separate_title=False):
    column_lengths = [max([len(str(row[i])) for row in table]) for i in range(len(table[0]))]
    row_separator = '+-%s-+' % '-+-'.join(['-' * col_length for col_length in column_lengths])
    title_separator = '+=%s=+' % '=+='.join(['=' * col_length for col_length in column_lengths])

    lines = [row_separator]
    for i, row in enumerate(table):
        line = '| %s |' % ' | '.join([str(val).ljust(col_length) for val, col_length in zip(row, column_lengths)])
        lines.append(line)
        lines.append(title_separator if separate_title and not i else row_separator)

    return '\n'.join(lines)
