import shlex
import subprocess


def run(command: str, capture_output: bool = False, assert_zero_code: bool = True) -> (int, str):
    # run the command
    stdout = subprocess.PIPE if capture_output else None
    res = subprocess.run(command, stdout=stdout, shell=True)

    # make sure the command is succeed
    if assert_zero_code:
        assert res.returncode == 0, 'Command "%s" is failed' % command

    # decode output
    output = res.stdout.decode('utf-8') if capture_output else None

    return res.returncode, output


def touch_file(file_path: str):
    run('touch ' + shlex.quote(file_path))
