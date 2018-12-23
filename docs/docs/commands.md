---
layout: default
title: Commands
nav_order: 3
permalink: /docs/commands/
---

# Commands

Available commands:

  - `$ spotty start [INSTANCE_NAME] [--dry-run]`
  
    Runs an instance, synchronizes the project with that instance and starts the Docker container.

    Use the `--dry-run` flag to display the steps that will be performed without actually running them.

  - `$ spotty stop [INSTANCE_NAME]`

    Terminates the running instance and applies deletion policies for the volumes.

  - `$ spotty ssh [INSTANCE_NAME] [-H]`

    Connects to the running Docker container or to the instance itself. Use the `-H` flag to connect to the host OS 
    instead of the Docker container.

  - `$ spotty sync [INSTANCE_NAME]`

    Synchronizes the project with the running instance. It happens 
    automatically the first time when you start an instance.

  - `$ spotty run [INSTANCE_NAME] SCRIPT_NAME [-S] [-r] [-s SESSION_NAME] [-p PARAMETER=VALUE [PARAMETER=VALUE [...]]]`

    Runs a custom script inside the Docker container (see "scripts" section in [Configuration](/docs/configuration/#scripts-section-optional)).

    Use __`Crtl + b`__, then __`x`__ combination of keys to kill tmux window with the process.

    Use __`Crtl + b`__, then __`d`__ combination of keys to be detached from the SSH session. The script will keep running. 
    Call the `spotty run` command again to be reattached to the running script. 
    Read more about tmux here: [tmux Wiki](https://github.com/tmux/tmux/wiki){:target="_blank"}.

    If you need to run the same script several times in parallel, use the `-s` parameter to
    specify a different name for a tmux session.

    To restart a running script, use the `-r` flag.

    To synchronize the project with the instance before running a script, use the `-S` flag.
    
    Scripts can be parametrized. Parameters in a script are indicated by double braces. For example, 
    `echo {{msg1}} {{msg2}}`. Use the `-p` parameter to replace script parameters with real values: 
    `-p msg1=deep msg2=learning`. If some script parameters were not provided, they will be replaced with
    empty strings.

All the commands have the `-c` parameter to specify a path to the configuration file. By default Spotty is looking for 
the `spotty.yaml` file in the current working directory.
