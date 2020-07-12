import shlex


def shlex_join(split_command: list):
    """Return a shell-escaped string from *split_command*.
    Copy-pasted from the Python 3.8 code.
    """
    return ' '.join(shlex.quote(arg) for arg in split_command)
