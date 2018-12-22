---
layout: default
title: Commands
nav_order: 3
permalink: /docs/commands/
---

# Commands

Available commands:

  - `$ spotty start`
  
    Runs a Spot Instance, synchronizes the project with that instance and starts a Docker container.

  - `$ spotty stop`

    Terminates the running instance and creates snapshots of the attached volumes.

  - `$ spotty run <SCRIPT_NAME> [--session-name <SESSION_NAME>]`

    Runs a custom script inside the Docker container (see "scripts" section in [Available Parameters](#Available-Parameters)).
    
    Use __`Crtl + b`__, then __`d`__ combination of keys to be detached from SSH session. The script will keep running. 
    Call `$ spotty run <SCRIPT_NAME>` again to be reattached to the running script. 
    Read more about tmux here: [tmux Wiki](https://github.com/tmux/tmux/wiki).
    
    If you need to run the same script several times in parallel, use the `--session-name` parameter to
    specify different names for tmux sessions.

  - `$ spotty ssh [--host-os]`

    Connects to the running Docker container or to the instance itself. Use the `--host-os` parameter to connect to the host OS instead of the Docker container.

  - `$ spotty sync`

    Synchronizes the project with the running instance. First time it happens automatically once you start an instance, but you always can use this command to update the project if an instance is already running.

  - `$ spotty create-ami`
    
    Creates AMI with NVIDIA Docker. You need to call this command only one time when you start using Spotty, then you can reuse created AMI for all your projects.
  
  - `$ spotty delete-ami`
    
    Deletes an AMI that was created using the command above.
  
  - `$ spotty spot-prices [--instance-type <INSTANCE_TYPE>]`

    Returns Spot Instance prices for particular instance type across all AWS regions. Results will be sorted by price.

All the commands have parameter `--config` that can be used to specify a path to configuration file. By default it's looking for a file `spotty.yaml` in the current working directory.
