---
layout: default
title: Home
nav_order: 1
permalink: /
---


# An open-source system for training<br />deep learning models in the cloud
{: .fs-9 }

Spotty makes training of deep learning models on 
[AWS Spot Instances](https://aws.amazon.com/ec2/spot/){:target="_blank"} and on 
[GCP Preemtible VMs](https://cloud.google.com/preemptible-vms/){:target="_blank"} (including TPUs) 
as simple as a training on your local machine.
{: .fs-6 .fw-300 }

[Get started now](#getting-started){: .btn .btn-purple .fs-5 .mb-4 .mb-md-0 .mr-2 } [View it on GitHub](https://github.com/apls777/spotty){: .btn .fs-5 }

---


## Getting Started

### Installation

Requirements:
  * Python 3
  * AWS CLI (see [Installing the AWS Command Line Interface](http://docs.aws.amazon.com/cli/latest/userguide/installing.html)){:target="_blank"}

Use [pip](http://www.pip-installer.org/en/latest/){:target="_blank"} to install or upgrade Spotty:

```bash
$ pip install -U spotty
```

### Prepare the configuration file

Prepare the `spotty.yaml` file for your project.

   - See the file specification [here](/docs/configuration/).
   - Read [this](https://medium.com/@apls/how-to-train-deep-learning-models-on-aws-spot-instances-using-spotty-8d9e0543d365){:target="_blank"} 
   article for a real-world example.

### Create an AMI

Run the following command from the root directory of your project (where the `spotty.yaml` file is located)
to create an AMI with NVIDIA Docker:

```bash
$ spotty create-ami
```

In several minutes you will have an AMI that can be used for all your projects within the AWS region.

### Start the instance

Use the following command to launch the instance with the Docker container:
    
```bash
$ spotty start
```

It will start a Spot instance, restore snapshots if any, synchronize the project with the running instance 
and start the Docker container with the environment.

### Train your models or run notebooks

To connect to the running container via SSH, use the following command:

```bash
$ spotty ssh
```

It runs a [tmux](https://github.com/tmux/tmux/wiki){:target="_blank"} session, so you can always detach this session using
__`Crtl + b`__, then __`d`__ combination of keys. To be attached to that session later, just use the
`spotty ssh` command again.

Also you can run custom scripts inside the Docker container using the `spotty run <SCRIPT_NAME>` command. Read more
about custom scripts in the documentation: 
[Configuration File: "scripts" section](/docs/configuration/#scripts-section-optional).
