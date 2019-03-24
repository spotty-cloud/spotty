<img src="logo.png" width="370" height="120" />

[![Documentation](https://img.shields.io/badge/documentation-reference-brightgreen.svg)](https://apls777.github.io/spotty)
[![PyPI](https://img.shields.io/pypi/v/spotty.svg)](https://pypi.org/project/spotty/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/spotty.svg)
![PyPI - License](https://img.shields.io/pypi/l/spotty.svg)

Spotty drastically simplifies training of deep learning models on AWS:

- it makes training on AWS GPU instances as simple as training on your local computer
- it automatically manages all necessary AWS resources including AMIs, volumes, snapshots and SSH keys
- it makes your model trainable on AWS by everyone with a couple of commands
- it uses [tmux](https://en.wikipedia.org/wiki/Tmux) to easily detach remote processes from their terminals
- it saves you up to 70% of the costs by using [Spot Instances](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-spot-instances.html)

## Documentation

- See the [documentation page](https://apls777.github.io/spotty).
- Read [this](https://medium.com/@apls/how-to-train-deep-learning-models-on-aws-spot-instances-using-spotty-8d9e0543d365) 
article on Medium for a real-world example.

## Installation

Requirements:
  * Python >=3.5
  * AWS CLI (see [Installing the AWS Command Line Interface](http://docs.aws.amazon.com/cli/latest/userguide/installing.html))

Use [pip](http://www.pip-installer.org/en/latest/) to install or upgrade Spotty:

    $ pip install -U spotty

## Get Started

1. Prepare a `spotty.yaml` file and put it to the root directory of your project:

   - See the file specification [here](https://apls777.github.io/spotty/docs/configuration/).
   - Read [this](https://medium.com/@apls/how-to-train-deep-learning-models-on-aws-spot-instances-using-spotty-8d9e0543d365) 
   article for a real-world example.

2. Create an AMI. Run the following command from the root directory of your project:

    ```bash
    $ spotty aws create-ami
    ```

    In several minutes you will have an AMI with NVIDIA Docker that Spotty will use 
    for all your projects within the AWS region.

3. Start an instance:

    ```bash
    $ spotty start
    ```

    It will run a Spot Instance, restore snapshots if any, synchronize the project with the running instance 
    and start the Docker container with the environment.

4. Train a model or run notebooks.

    You can run custom scripts inside the Docker container using the `spotty run <SCRIPT_NAME>` command. Read more
    about custom scripts in the documentation: 
    [Configuration: "scripts" section](https://apls777.github.io/spotty/docs/configuration/#scripts-section-optional).

    To connect to the running container via SSH, use the following command:

    ```bash
    $ spotty ssh
    ```

    It runs a [tmux](https://github.com/tmux/tmux/wiki) session, so you can always detach this session using
    __`Ctrl + b`__, then __`d`__ combination of keys. To be attached to that session later, just use the
    `spotty ssh` command again.

## Contributions

Any feedback or contributions are welcome! Please check out the [guidelines](CONTRIBUTING.md).

## License

[MIT License](LICENSE)
