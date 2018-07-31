cloud-training
==============

https://docs.aws.amazon.com/cli/latest/reference/s3/index.html#use-of-exclude-and-include-filters

This package provides a command line interface to help you to train your TensorFlow models on AWS spot instances.

### Installation ###

To install the cloud-training use [pip](http://www.pip-installer.org/en/latest/) package manger:

    $ pip install --upgrade cloud-training

Requirements:
  * Python 3
  * AWS CLI (see [Installing the AWS Command Line Interface](http://docs.aws.amazon.com/cli/latest/userguide/installing.html))

### Available commands ###

  * Configure the tool:
    ~~~
    $ cloud-training configure
    ~~~

  * Get current spot prices for instances:
    ~~~
    $ cloud-training spot-price [--instance-type <instance_type>] [--region <region_name>] [--all-regions]
    ~~~

  * Train the model using AWS spot instance:
    ~~~
    $ cloud-training --model <model_name> [--project-dir <project_dir>] train [--instance-type <instance_type>] [--conda-env <environment_name>] [--session <session_name>]
    ~~~

  * Get the latest trained model from AWS S3:
    ~~~
    $ cloud-training --model <model_name> [--project-dir <project_dir>] sync-session
    ~~~

  * Shutdown the instances and cancel the spot requests:
    ~~~
    $ cloud-training --model <model_name> [--project-dir <project_dir>] shutdown
    ~~~


### Required Project Sctructure ###

In the current version of the tool the project must have the following structure:

    ProjectName/
        data/
            ...
        package_name/
            models/
                my_model_1/
                    train.py
                ...
            ...
        training/
            my_model_1/
                session_name_1/
                    checkpoints/
                    ...
                ...
            ...
        cloud_training.json
        
  * `data/` contains all your training data,
  * `package_name/` contains the project code,
  * `package_name/models/my_model_1/` contains the code of the "my_model_1" model,
  * `package_name/models/my_model_1/train.py` is the script which is being used for training, it must have "--session" parameter,
  * `training/my_model_1/` contains the sessions for the "my_model_1" model,
  * `training/my_model_1/session_name_1/` contains all outputs for a particular session,
  * `training/my_model_1/checkpoints/` contains TensorFlow checkpoint files, see [Saving and Restoring](https://www.tensorflow.org/programmers_guide/saved_model),
  * `cloud_training.json` is the configuration file which must contain the project name and the package name is JSON format:

        {
          "project_name": "ProjectName",
          "package_name": "package_name"
        }


### How it works ###

1. `configure` command:

    Before using the cloud-training you need to configure it. During the configuration you will 
    be asked for the following things:
      * **AWS Access Key ID**
      * **AWS Secret Access Key**
      * **Region name** - AWS region name where you have created a S3 bucket and where you plan to run instances. 
      See [AWS Regions and Endpoints](http://docs.aws.amazon.com/general/latest/gr/rande.html).
      * **S3 bucket name** - Bucket which will be used to synchronize the project with an EC2 instance 
      and where an EC2 instance will save checkpoints. It has format <bucket_name>/<path> without trailing slash. 
      If the bucket will be located in a different region, it may cause the additional charges for the data 
      transferring between S3 and EC2.
      * **Image ID** - AMI with installed TensorFlow, it has the format ami-xxxxxxxx. See below how to create an AMI.
      * **Root EBS volume snapshot ID** - Snapshot which is being used for AMI, it has the format snap-xxxxxxxxxxxxxxxxx.
      * **Root EBS volume size (GB)** - Size of an AMI snapshot in GB.
      * **Training EBS volume size (GB)** - Size of an additional volume used for the project code and the training data.
      * **EC2 key pair name** - Name of an existing key pair to have an access to the running instance.
      * **Default instance type** - Instance type which will be used by default for commands "train" and "spot-price". 
      See [Amazon EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/).

2. `train` command:

    * **During the command:**
        1. All the files in the data directory will be zipped one by one.
        2. The package directory, the zip files from the data directory 
        and the particular session (if it was specified) will be synced with S3. The "aws sync"
        command is being used, so it will transfer the files only once.
        3. Spot instance will be run (you will be asked for the maximum price for the specified instance type).
        4. It returns you the IP address of the instance and the session name which you will use for the "sync-session".

    * **After the command**:
        1. The instance copies the project from S3, unzips the files from the data directory and runs the training.
        2. TensorBoard will be started on 6006 port.
        3. The instance constantly syncs the session directory (checkpoints and other outputs) with S3.

3. `sync-session` command:

    Use this command to get the latest trained model from S3. This command gets the checkpoint file first, 
    finds the name of the last checkpoint and downloads it to your local machine.

4. `shutdown` command:

    This command finds the running instance for the training model and terminates it. 
    The spot request will be cancelled automatically.

5. `spot-price` command:

    This command checks the current prices for spot instances in different regions. It helps you to
    find the region with the lowest price for the desired instance type.


### AMI ###

To create an AMI I used [this](https://medium.com/@rogerxujiang/setting-up-a-gpu-instance-for-deep-learning-on-aws-795343e16e44) 
and [this](http://mortada.net/tips-for-running-tensorflow-with-gpu-support-on-aws.html) article.

You can create your own AMI or use my one: **ami-a396bac6** (us-east-2 region). 

I installed there Anaconda 3 with "nlp" environment which contains TensorFlow 1.4.0-rc0. 
TensorFlow was compiled with the compute capability 3.7 (see [CUDA GPUs](https://developer.nvidia.com/cuda-gpus)), 
so the image can be used for any p2.* instance. If you want to use this image for g3.* instances, 
you can recompile TensorFlow and install it for another environment.

Example of a training command:

    $ cloud-training --model token_classes train --conda-env nlp

This command should be run from the project directory. Or you can use `--project-dir` parameter 
to specify the absolute or the relative path to the project directory.

To continue training of an existing session use `--session` parameter.


### Issues ###

If you're using the MINGW you might get an error:

    bash: /c/Program Files/Anaconda/Scripts/cloud-training: C:/Program: bad interpreter: Permission denied

I simply fixed it by changing the first line of the "cloud-training" script to:

    #!python.exe
