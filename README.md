<img src="https://spotty.cloud/_static/images/logo_740x240.png" width="370" height="120" />

[![Documentation](https://img.shields.io/badge/documentation-reference-brightgreen.svg)](https://spotty.cloud)
[![PyPI](https://img.shields.io/pypi/v/spotty.svg)](https://pypi.org/project/spotty/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/spotty.svg)
![PyPI - License](https://img.shields.io/pypi/l/spotty.svg)

Spotty drastically simplifies training of deep learning models on [AWS](https://aws.amazon.com/) 
and [GCP](https://cloud.google.com/):

- it makes training on GPU instances as simple as training on your local machine
- it automatically manages all necessary cloud resources including images, volumes, snapshots and SSH keys
- it makes your model trainable in the cloud by everyone with a couple of commands
- it uses [tmux](https://en.wikipedia.org/wiki/Tmux) to easily detach remote processes from their terminals
- it saves you up to 70% of the costs by using [AWS Spot Instances](https://aws.amazon.com/ec2/spot/) 
and [GCP Preemtible VMs](https://cloud.google.com/preemptible-vms/)

## Documentation

- See the [documentation page](https://spotty.cloud).
- Read [this](https://medium.com/@apls/how-to-train-deep-learning-models-on-aws-spot-instances-using-spotty-8d9e0543d365) 
article on Medium for a real-world example.

## Installation

Requirements:
  * Python >=3.6
  * AWS CLI (see [Installing the AWS Command Line Interface](http://docs.aws.amazon.com/cli/latest/userguide/installing.html)) 
  if you're using AWS
  * Google Cloud SDK (see [Installing Google Cloud SDK](https://cloud.google.com/sdk/install)) 
  if you're using GCP

Use [pip](http://www.pip-installer.org/en/latest/) to install or upgrade Spotty:

    $ pip install -U spotty

## Get Started

1. Prepare a `spotty.yaml` file and put it to the root directory of your project:

   - See the file specification [here](https://spotty.cloud/docs/configuration-file/).
   - Read [this](https://medium.com/@apls/how-to-train-deep-learning-models-on-aws-spot-instances-using-spotty-8d9e0543d365) 
   article for a real-world example.

2. Start an instance:

    ```bash
    $ spotty start
    ```

    It will run a Spot Instance, restore snapshots if any, synchronize the project with the running instance 
    and start the Docker container with the environment.

3. Train a model or run notebooks.

    To connect to the running container via SSH, use the following command:

    ```bash
    $ spotty sh
    ```

    It runs a [tmux](https://github.com/tmux/tmux/wiki) session, so you can always detach this session using
    __`Ctrl + b`__, then __`d`__ combination of keys. To be attached to that session later, just use the
    `spotty sh` command again.

    Also, you can run your custom scripts inside the Docker container using the `spotty run <SCRIPT_NAME>` command. Read more
    about custom scripts in the documentation: 
    [Configuration: "scripts" section](https://spotty.cloud/docs/configuration-file/#scripts-section-optional).

## Contributions

Any feedback or contributions are welcome! Please check out the [guidelines](CONTRIBUTING.md).

## License

[MIT License](LICENSE)
