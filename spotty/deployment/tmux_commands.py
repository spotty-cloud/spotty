import subprocess


def get_session_cmd(command: list, session_name: str, window_name: str = None, default_command: str = None,
                    keep_pane: bool = False) -> list:
    window_name_params = ['-n', window_name] if window_name else []
    session_cmd = ['tmux', 'new', '-s', session_name, *window_name_params, '-A']

    if command:
        # keep the pane alive when the script is finished
        keep_pane_cmd = ['tmux', 'set', '-p', 'remain-on-exit', 'on', ';'] if keep_pane else []

        # set the default command (to automatically run bash inside the container when a new window is created)
        default_command_cmd = ['tmux', 'set', 'default-command', default_command, ';'] if default_command else []

        # keep the pane alive only if the script is failed
        keep_pane_on_failure_cmd = ['tmux', 'set', '-p', 'remain-on-exit', 'on']

        tmux_cmd = [
            *keep_pane_cmd, *default_command_cmd,
            *command, '||', *keep_pane_on_failure_cmd,
        ]

        # run the command inside the tmux session
        session_cmd.append(subprocess.list2cmdline(tmux_cmd))

    return session_cmd
