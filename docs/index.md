---
layout: default
title: Getting Started
nav_order: 1
permalink: /
---


# An Open-source Tool for Training<br />Deep Learning Models in the Cloud
{: .fs-9 }

Spotty makes training of deep learning models on 
[AWS Spot Instances](https://aws.amazon.com/ec2/spot/){:target="_blank"}
and on [GCP Preemtible VMs](https://cloud.google.com/preemptible-vms/){:target="_blank"}
as simple as training on your local machine.
{: .fs-6 .fw-300 }

[Get started now](#getting-started){: .btn .btn-purple .fs-5 .mb-4 .mb-md-0 .mr-2 } 
[View it on GitHub](https://github.com/apls777/spotty){:target="_blank"}{: .btn .fs-5 }

---


## Getting Started

### __Installation__

Requirements:
  * Python >=3.5
  * AWS CLI (see [Installing the AWS Command Line Interface](http://docs.aws.amazon.com/cli/latest/userguide/installing.html){:target="_blank"})
  if you're using AWS
  * Google Cloud SDK (see [Installing Google Cloud SDK](https://cloud.google.com/sdk/install){:target="_blank"}) 
  if you're using GCP

Use [pip](http://www.pip-installer.org/en/latest/){:target="_blank"} to install or upgrade Spotty:

```bash
pip install -U spotty
```

### __Prepare a configuration file__

Prepare a `spotty.yaml` file and put it to the root directory of your project:

   - See the file specification [here]({{ site.baseurl }}/docs/configuration-file/).
   - Read [this](https://medium.com/@apls/how-to-train-deep-learning-models-on-aws-spot-instances-using-spotty-8d9e0543d365){:target="_blank"} 
   article for a real-world example.

### __Start an instance__

Use the following command to launch an instance with the Docker container:
    
```bash
spotty start
```

It will start a Spot instance, restore snapshots if any, synchronize the project with the running instance 
and start the Docker container with the project environment.

### __Train your models or run notebooks__

To connect to the running container via SSH, use the following command:

```bash
spotty ssh
```

It runs a [tmux](https://github.com/tmux/tmux/wiki){:target="_blank"} session, so you can always detach this session using
__`Ctrl + b`__, then __`d`__ combination of keys. To be attached to that session later, just use the
`spotty ssh` command again.

Also, you can run custom scripts inside the Docker container using the `spotty run <SCRIPT_NAME>` command. Read more
about custom scripts in the documentation: 
[Configuration File: "scripts" section]({{ site.baseurl }}/docs/configuration-file/#scripts-section-optional).
