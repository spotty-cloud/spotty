# Spotty

Spotty simplifies training of Deep Learning models on AWS:

- it makes training on AWS GPU instances as simple as a training on your local computer
- it automatically manages all necessary AWS resources including AMIs, volumes and snapshots
- it makes your model trainable on AWS by everyone with a couple of commands
- it detaches remote processes from SSH sessions
- it saves you up to 70% of the costs by using Spot Instances

## Documentation

- See the [wiki section](/apls777/spotty/wiki) for the documentation.
- Read [this](https://medium.com/@apls/how-to-train-deep-learning-models-on-aws-spot-instances-using-spotty-8d9e0543d365) 
article on Medium for a real-world example.

## Installation

Requirements:
  * Python 3
  * AWS CLI (see [Installing the AWS Command Line Interface](http://docs.aws.amazon.com/cli/latest/userguide/installing.html))

Use [pip](http://www.pip-installer.org/en/latest/) to install or upgrade Spotty:

    $ pip install -U spotty

## Get Started

1. Prepare a `spotty.yaml` file for your project.

   - See the file specification [here](https://github.com/apls777/spotty/wiki/Configuration-File).
   - Read [this](https://medium.com/@apls/how-to-train-deep-learning-models-on-aws-spot-instances-using-spotty-8d9e0543d365) 
   article for a real-world example.

2. Create an AMI with NVIDIA Docker. Run the following command from the root directory of your project 
(where the `spotty.yaml` file is located):

    ```bash
    $ spotty create-ami
    ```

    In several minutes you will have an AMI that can be used for all your projects within the AWS region.

3. Start an instance:

    ```bash
    $ spotty start
    ```

    It will run a Spot Instance, restore snapshots if any, synchronize the project with the running instance 
    and start the Docker container with the environment.

4. Train a model or run notebooks.

    You can run custom scripts inside the Docker container using the `spotty run <SCRIPT_NAME>` command. Read more
    about custom scripts in the documentation: 
    [Configuration File: "scripts" section](/apls777/spotty/wiki/Configuration-File#scripts-section-optional).

    To connect to the running container via SSH, use the following command:

    ```bash
    $ spotty ssh
    ```

    It runs a [tmux](https://github.com/tmux/tmux/wiki) session, so you can always detach this session using
    __`Crtl + b`__, then __`d`__ combination of keys. To be attached to that session later, just use the
    `spotty ssh` command again.

## License

[MIT License](LICENSE)
