---
layout: default
title: Configuration
nav_order: 2
permalink: /docs/configuration/
---

# Configuration

By default, Spotty is looking for a `spotty.yaml` file in the root directory of the project. This file describes 
parameters of a remote instance and an environment for the project. Here is a basic example of such file:

```yaml
project:
  name: my-project-name
  syncFilters:
    - exclude:
      - .git/*
      - .idea/*
      - '*/__pycache__/*'

container:
  projectDir: /workspace/project
  image: tensorflow/tensorflow:latest-gpu-py3
  ports: [6006, 8888]
  volumeMounts:
    - name: workspace
      mountPath: /workspace

instances:
  - name: i1
    provider: aws
    parameters:
      region: eu-west-1
      instanceType: p2.xlarge
      volumes:
        - name: workspace
          parameters:
            size: 10
```

## Available Parameters

Configuration file consists of 4 sections: `project`, `container`, `instances` and `scripts`.

### __`project`__ section:

- __`name`__ - the name of your project. It will be used to create S3 bucket and CloudFormation stack to run 
an instance.

- __`syncFilters`__ _(optional)_ - filters to skip some directories or files during synchronization. By default, all 
project files will be synced with the instance. Example:
    ```yaml
    syncFilters:
      - exclude:
          - .idea/*
          - .git/*
          - data/*
      - include:
          - data/test/*
      - exclude:
          - data/test/dump.json
    ```
    
    It will skip ".idea/", ".git/" and "data/" directories except the "data/test/" directory. All files from 
    the "data/test/" directory will be synced with the instance except the "data/test/dump.json" file.
    
    You can read more about filters 
    here: [Use of Exclude and Include Filter](https://docs.aws.amazon.com/cli/latest/reference/s3/index.html#use-of-exclude-and-include-filters){:target="_blank"}. 

### __`container`__ section:

- __`projectDir`__ - a directory inside the container where the local project will be copied. If
it's a subdirectory of a container volume, the project will be located on that volume,
otherwise the data will be lost once the instance is terminated.

- __`image`__ _(optional)_ - the name of the Docker image that contains environment for your project. For example, 
you could use [TensorFlow image for GPU](https://hub.docker.com/r/tensorflow/tensorflow/){:target="_blank"} 
(`tensorflow/tensorflow:latest-gpu-py3`). It already contains NumPy, SciPy, scikit-learn, pandas, Jupyter Notebook and 
TensorFlow itself. If you need to use your own image, you can specify the path to your Dockerfile in the 
__`file`__ parameter (see below), or push your image to the [Docker Hub](https://hub.docker.com/){:target="_blank"}.

- __`file`__ _(optional)_ - relative path to your custom Dockerfile.
    
    __Note:__ make sure that the build context for the Dockerfile doesn't contain gigabytes of training data or 
    some other heavy data (keep the Dockerfile in a separate directory or use the `.dockerignore` file). Otherwise, you would get an out-of-space error, because Docker copies the entire build
    context to the Docker daemon during the build. Read more here: ["docker build" command](https://docs.docker.com/engine/reference/commandline/build/){:target="_blank"}.

    __Example:__ if you use TensorFlow and need to download your dataset from S3, you could install 
    [AWS CLI](https://github.com/aws/aws-cli){:target="_blank"} on top of the original TensorFlow image. Just create the 
    `Dockerfile` file in the `docker/` directory of your project:
    ```dockerfile
    FROM tensorflow/tensorflow:latest-gpu-py3
    
    RUN pip install --upgrade awscli
    ```

    Then set the `file` parameter to the `docker/Dockerfile` value.

- __`volumeMounts`__ _(optional)_ - where to mount instance volumes into the container's filesystem. Each element 
of a list has the following parameters:
    - __`name`__ - this must match the name of an instance volume.
    - __`mountPath`__ - a path within the container at which the volume should be mounted.

- __`workingDir`__ _(optional)_ - working directory for your custom scripts (see "scripts" section below),

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

### __`instances`__ section:

This section contains a list of instances. Each instance is described with the following parameters:

- __`name`__ - name of the instance. Use this name to manage the instance with the commands like 
"spotty start" or "spotty stop". Also Spotty uses this name in the names of AWS and GCP resources.

- __`provider`__ - a provider for the instance. At the moment Spotty supports "__aws__" (Amazon Web Services) 
and "__gcp__" (Google Cloud Platform).

- __`parameters`__ - parameters of the instance. These parameters are different for different providers:
    - [AWS instance parameters](/docs/aws/instance-parameters/)
    - [GCP instance parameters](/docs/gcp/instance-parameters/)

### __`scripts`__ section _(optional)_:

This section contains customs scripts which can be run using `spotty run <SCRIPT_NAME>`
command. The following example defines scripts `train`, `jupyter` and `tensorflow`:
                
```yaml
train: |
  PYTHONPATH=/workspace/project
  python /workspace/project/model/train.py --num-layers 3
jupyter: |
  jupyter notebook --allow-root --notebook-dir=/workspace/project
tensorboard: |
  tensorboard --logdir /workspace/outputs
```

__Note:__ don't forget to use the "|" character for multi-line scripts, otherwise the YAML parser
will merge multiple lines together.
