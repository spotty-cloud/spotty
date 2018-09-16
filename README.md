# Spotty

Spotty helps you to train deep learning models on [AWS Spot Instances](https://aws.amazon.com/ec2/spot/).

You don't need to spend time on:
- manually starting Spot Instances
- installation of NVIDIA drivers
- managing snapshots and AMIs
- detaching remote processes from your SSH sessions

Just start an instance using the following command:
```bash
$ spotty start
```
It will run a Spot Instance, restore snapshots if any, synchronize the project with the instance 
and start Docker container with the environment.

Then train your model:
```bash
$ spotty run train
```
It runs your custom training command inside the Docker container. The remote connection uses 
[tmux](https://github.com/tmux/tmux/wiki), so you can close the connection and come back to the running process any time later.

Connect to the container if necessary:
```bash
$ spotty ssh
```
It uses [tmux](https://github.com/tmux/tmux/wiki) session, so you can always detach the session using
`Crtl`+`b`, then `d` combination of keys and attach that session later using `$ spotty ssh` command again.

## Installation

To install Spotty use [pip](http://www.pip-installer.org/en/latest/) package manger:

    $ pip install --upgrade spotty

Requirements:
  * Python 3
  * AWS CLI (see [Installing the AWS Command Line Interface](http://docs.aws.amazon.com/cli/latest/userguide/installing.html))

## Configuration

By default, Spotty is looking for `spotty.yaml` file in the root directory of the project.
Here is a basic example of such file:

```yaml
project:
  name: MyProjectName
  remoteDir: /workspace/project
instance:
  region: us-east-2
  instanceType: p2.xlarge
  volumes:
    - snapshotName: MySnapshotName
      directory: /workspace
      size: 10
  docker:
    image: tensorflow/tensorflow:latest-gpu-py3
```

### Available Parameters

__`project`__ section:
- __`name`__ - the name of your project. It will be used to create S3 bucket and CloudFormation stack to run 
an instance.
- __`remoteDir`__ - directory where your project will be stored on the instance. It's usually a directory 
on the attached volume (see "instance" section).
- __`syncFilters`__ _(optional)_ - filters to skip some directories or files during synchronization. By default, all project files 
will be synced with the instance. Example:
    ```yaml
    syncFilters:
      - exclude:
          - .idea/*
          - .git/*
          - data/*
      - include:
          - data/test/*
      - exclude:
          - data/test/config
    ```
    
    It will skip ".idea/", ".git/" and "data/" directories except "data/test/" directory. All files from "data/test/" 
    directory will be synced with the instance except "data/test/config" file.
    
    You can read more about filters 
    here: [Use of Exclude and Include Filter](https://docs.aws.amazon.com/cli/latest/reference/s3/index.html#use-of-exclude-and-include-filters). 

__`instance`__ section:
- __`region`__ - region where your are going to run the instance (you can use command `spotty spot-prices` to find the 
cheapest region),
- __`instanceType`__ - type of the instance to run. You can find more information about 
types of GPU instances here: 
[Recommended GPU Instances](https://docs.aws.amazon.com/dlami/latest/devguide/gpu.html).
- __`amiName`__ _(optional)_ - name of the AMI with NVIDIA Docker (default value is "SpottyAMI"). Use 
`spotty create-ami` command to create it. This AMI will be used to run your application inside the Docker container.
- __`maxPrice`__ _(optional)_ - the maximum price per hour that you are willing to pay for a Spot Instance. By default, it's 
On-Demand price for chosen instance type. Read more here: 
[Spot Instances](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-spot-instances.html).
- __`rootVolumeSize`__ _(optional)_ - size of the root volume in GB. The root volume will be destroyed once 
the instance is terminated. Use attached volumes to store the data you need to keep (see "volumes" parameter below).
- __`volumes`__ _(optional)_ - the list of volumes to attach to the instance:
    - __`name`__ _(optional)_ - name of the volume. When you're starting an instance, Spotty is looking for a volume 
    with this name. If the volume is found, it will be attached to the instance, if not - Spotty will be looking for a 
    snapshot with this name. If the snapshot is found, the volume will be restored from that snapshot, if not - new 
    volume will be created. This parameter is required if deletionPolicy isn't set to "delete".
    - __`directory`__ - directory where the volume will be mounted,
    - __`size`__ _(optional)_ - size of the volume in GB. Size of the volume cannot be less then the size of existing 
    snapshot, but can be increased.
    - __`deletionPolicy`__ _(optional)_ - possible values include: "__create_snapshot__" _(value by default)_, 
    "__update_snapshot__", "__retain__" and  "__delete__". By default, Spotty will create new snapshot every time you're 
    stopping an instance, the old snapshot will be renamed. If this parameter is set to "__update_snapshot__", new 
    snapshot will be created and the old one will be deleted. If the parameter is set to "__retain__", the volume will
    not be deleted and snapshot will not be taken. If the parameter is set to  "__delete__" value, the volume will be 
    deleted without creating a snapshot.
    
        __Note:__ Deletion policy works only for volumes that were created from scratch or from snapshots during the 
        `spotty start` command. So if the volume existed before and was attached to the instance by its name, it will 
        retain after the instance deletion anyway, even if you had a different value in the DeletionPolicy.

- __`docker`__ - Docker configuration:
    - __`image`__ _(optional)_ - the name of the Docker image that contains environment for your project. For example, 
    you could use [TensorFlow image for GPU]((https://hub.docker.com/r/tensorflow/tensorflow/)) 
    (`tensorflow/tensorflow:latest-gpu-py3`). It already contains NumPy, SciPy, scikit-learn, pandas, Jupyter Notebook and 
    TensorFlow itself. If you need to use your own image, you can specify the path to your Dockerfile in the 
    __`file`__ parameter (see below), or push your image to the [Docker Hub](https://hub.docker.com/) and use its name.
    - __`file`__ _(optional)_ - relative path to your custom Dockerfile. For example, you could take TensorFlow image as a 
    base one and add [AWS CLI](https://github.com/aws/aws-cli) there to be able to download your datasets from S3:
        ```dockerfile
        FROM tensorflow/tensorflow:latest-gpu-py3
        
        RUN pip install --upgrade \
          pip \
          awscli
        ```
    - __`workingDir`__ _(optional)_ - working directory for your custom scripts (see "scripts" section below),
    - __`dataRoot`__ _(optional)_ - directory where Docker will store all downloaded and built images. You could cache 
    images on your attached volume to avoid downloading them from internet or building your custom image from scratch 
    every time when you start an instance.
    - __`commands`__ _(optional)_ - commands which should be performed once your container is started. For example, you 
    could download your datasets from S3 bucket to the project directory (see "project" section):
        ```yaml
        commands: |
          aws s3 sync s3://my-bucket/datasets/my-dataset /workspace/project/data
        ```
- __`ports`__ _(optional)_ - list of ports to open. For example:
    ```yaml
    ports: [6006, 8888]
    ```
    It will open ports 6006 for Jupyter Notebook and 8008 for TensorBoard. 

__`scripts`__ section _(optional)_:
- This section contains customs scripts which can be run using `spotty run <SCRIPT_NAME>`
command. The following example defines scripts `train`, `jupyter` and `tensorflow`:
                
    ```yaml
    project:
      ...
    instance:
      ...
    scripts:
      train: |
        PYTHONPATH=/workspace/project
        python /workspace/project/model/train.py --num-layers 3
      jupyter: |
        /run_jupyter.sh --allow-root
      tensorboard: |
        tensorboard --logdir /workspace/outputs
    ```

## Available Commands

  - `$ spotty start`
  
    Runs a Spot Instance, synchronizes the project with that instance and starts a Docker container.

  - `$ spotty stop`

    Terminates the running instance and creates snapshots of the attached volumes.

  - `$ spotty run <SCRIPT_NAME> [--session-name <SESSION_NAME>]`

    Runs a custom script inside the Docker container (see "scripts" section in [Available Parameters](#Available-Parameters)).
    
    Use `Crtl`+`b`, then `d` combination of keys to be detached from SSH session. The script will keep running. 
    Call `$ spotty run <SCRIPT_NAME>` again to be reattached to the running script. 
    Read more about tmux here: [tmux Wiki](https://github.com/tmux/tmux/wiki).
    
    If you need to run the same script several times in parallel, use the `--session-name` parameter to
    specify different names for tmux sessions.

  - `$ spotty ssh [--host-os]`

    Connects to the running Docker container or to the instance itself. Use the `--host-os` parameter to connect to the 
    host OS instead of the Docker container.

  - `$ spotty sync`

    Synchronizes the project with the running instance. First time it happens automatically once you start an instance, 
    but you always can use this command to update the project if an instance is already running.

  - `$ spotty create-ami`
    
    Creates AMI with NVIDIA Docker. You need to call this command only one time when you start using Spotty, then you 
    can reuse created AMI for all your projects.
  
  - `$ spotty delete-ami`
    
    Deletes an AMI that was created using the command above.
  
  - `$ spotty spot-prices [--instance-type <INSTANCE_TYPE>]`

    Returns Spot Instance prices for particular instance type across all AWS regions. Results will be sorted by price.

All the commands have parameter `--config` that can be used to specify a path to configuration file. By default it's 
looking for a file `spotty.yaml` in the current working directory.
