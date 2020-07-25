# Getting Started

## Installation

Use [pip](http://www.pip-installer.org/en/latest/) to install or upgrade Spotty:

```bash
pip install -U spotty
```

Python >=3.6 is required.

Also, depending on the use case, some additional software is needed:

* __Docker__ if you want to run containers locally: [Get Docker](https://docs.docker.com/get-docker/)
* __AWS CLI__ if you're going to use AWS: [Installing the AWS Command Line Interface](http://docs.aws.amazon.com/cli/latest/userguide/installing.html)
* __Google Cloud SDK__ if you're going to use GCP: [Installing Google Cloud SDK](https://cloud.google.com/sdk/install)


## Prepare a configuration file

Prepare a `spotty.yaml` file and put it to the root directory of your project:

   - See the file specification and an example here: [Spotty Configuration File].
   - Read [this](https://medium.com/@apls/how-to-train-deep-learning-models-on-aws-spot-instances-using-spotty-8d9e0543d365) 
   article for a real-world example.

## Start an instance

Use the following command to launch an instance with the Docker container:
    
```bash
spotty start
```

If you're using AWS, it will create EBS volumes if needed, start an instance, upload project files and start 
the Docker container with the environment for your project.

## Train your models or run notebooks

To connect to the running container via SSH, use the following command:

```bash
spotty sh
```

It runs a [tmux](https://github.com/tmux/tmux/wiki) session, so you can always detach this session using
__`Ctrl + b`__, then __`d`__ combination of keys. To be attached to that session later, just use the
`spotty sh` command again.

Also, you can run custom scripts inside the Docker container using the `spotty run <SCRIPT_NAME>` command. Read more
about custom scripts in the documentation: [Configuration File: "scripts" section].


[Spotty Configuration File]: </docs/user-guide/configuration-file>
[Configuration File: "scripts" section]: <docs/user-guide/configuration-file:scripts section>
