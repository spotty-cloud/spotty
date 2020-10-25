import base64
import os
import shlex
import time
from spotty.deployment.utils.cli import shlex_join


def get_bash_command() -> str:
    return '/usr/bin/env bash'


def get_script_command(script_name: str, script_content: str, script_args: list = None,
                       logging: bool = False) -> str:
    """Encodes a multi-line script into base64 and returns a one-line command
    that unpacks the script to a temporary file and runs it."""

    # encode the script content to base64
    script_base64 = base64.b64encode(script_content.encode('utf-8')).decode('utf-8')

    # command to decode the script, save it to a temporary file and run inside the container
    script_args = shlex_join(script_args) if script_args else ''

    script_cmd = ' && '.join([
        'TMPDIR=${TMPDIR%/}',
        'TMP_SCRIPT_PATH=$(mktemp ${TMPDIR:-/tmp}/spotty-%s.XXXXXXXX)' % script_name,
        'chmod +x $TMP_SCRIPT_PATH',
        'echo %s | base64 -d > $TMP_SCRIPT_PATH' % script_base64,
        '$TMP_SCRIPT_PATH ' + script_args,
    ])

    # log the command output to a file
    if logging:
        log_file_path = '/var/log/spotty/run/%s-%d.log' % (script_name, time.time())
        script_cmd = get_log_command(script_cmd, log_file_path)

    # execute the command with bash
    script_cmd = '%s -c %s' % (get_bash_command(), shlex.quote(script_cmd))

    return script_cmd


def get_log_command(command: str, log_file_path: str) -> str:
    # log the command outputs to a file on the host OS
    log_dir = os.path.dirname(log_file_path)
    log_cmd = '; '.join([
        'set -o pipefail',
        ' && '.join([
            'mkdir -pm 777 ' + shlex.quote(log_dir),
            '(%s) 2>&1 | tee %s' % (command, shlex.quote(log_file_path)),
        ]),
    ])

    return log_cmd


def get_tmux_session_command(command: str, session_name: str, window_name: str = None, default_command: str = None,
                             keep_pane: bool = False) -> str:
    session_cmd = 'tmux new -A -s ' + session_name
    if window_name:
        session_cmd += ' -n ' + window_name

    if command:
        # keep the pane alive when the script is finished
        keep_pane_cmd = 'tmux set -w remain-on-exit on; ' if keep_pane else ''

        # set the default command (to automatically run bash inside the container when a new window is created)
        default_command_cmd = ('tmux set default-command %s; ' % shlex.quote(default_command)) \
            if default_command else ''

        # keep the pane alive if the script is failed
        tmux_cmd = '%s%s(%s) || tmux set -w remain-on-exit on' % (keep_pane_cmd, default_command_cmd, command)

        # run the command inside the tmux session
        session_cmd += ' ' + shlex.quote(tmux_cmd)

    # use tmux only if it's installed
    session_cmd = 'if command -v tmux &> /dev/null; then %s; else %s; fi' % (session_cmd, command)

    return session_cmd


def get_ssh_command(host: str, port: int, user: str, key_path: str, command: str, env_vars: dict = None,
                    tty: bool = True, quiet: bool = False) -> str:

    ssh_command = 'ssh -i %s -o StrictHostKeyChecking=no -o ConnectTimeout=10' % shlex.quote(key_path)

    if tty:
        ssh_command += ' -t'

    if port != 22:
        ssh_command += ' -p %d' % port

    if quiet:
        ssh_command += ' -q'

    # export environmental variables
    if env_vars:
        export_cmd = '; '.join(['export %s=%s' % (name, shlex.quote(val)) for name, val in env_vars.items()])
        command = '%s; %s' % (export_cmd, command)

    # final SSH command
    ssh_command += ' %s@%s %s' % (user, host, shlex.quote(command))

    return ssh_command
