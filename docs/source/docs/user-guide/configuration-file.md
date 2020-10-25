# Spotty Configuration File

By default, Spotty is looking for a `spotty.yaml` file in the root directory of the project. This file describes 
parameters of a remote instance and an environment for the project. Here is a basic example of such file for AWS:

```yaml
project:
  name: my-project-name
  syncFilters:
    - exclude:
      - .git/*
      - .idea/*
      - '*/__pycache__/*'

containers:
  - projectDir: /workspace/project
    image: tensorflow/tensorflow:latest-gpu-py3-jupyter
    env:
      PYTHONPATH: /workspace/project
    ports:
      # TensorBoard
      - containerPort: 6006
        hostPort: 6006
      # Jupyter
      - containerPort: 8888
        hostPort: 8888
    volumeMounts:
      - name: workspace
        mountPath: /workspace

instances:
  - name: aws-1
    provider: aws
    parameters:
      region: eu-west-1
      instanceType: p2.xlarge
      ports: [6006, 8888]
      volumes:
        - name: workspace
          parameters:
            size: 50

scripts:
  tensorboard: |
    tensorboard --bind_all --port 6006 --logdir /workspace/project/training
  jupyter: |
    jupyter notebook --allow-root --ip 0.0.0.0 --notebook-dir=/workspace/project
```

Instance parameters are different for each provider:

- [Local Provider Instance Parameters]
- [Remote Provider Instance Parameters]
- [AWS Provider Instance Parameters]
- [GCP Provider Instance Parameters]


## Available Parameters

Configuration file consists of 4 sections: `project`, `containers`, `instances` and `scripts`.

### __`project`__ section

The `project` section contains the following parameters:

- __`name`__ - the name of your project. It will be used to create an S3 bucket and a CloudFormation stack to run 
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
    here: [Use of Exclude and Include Filter](https://docs.aws.amazon.com/cli/latest/reference/s3/index.html#use-of-exclude-and-include-filters). 

### __`containers`__ section

The `containers` section contains a list of containers where each container is described 
with the following parameters:

- __`name`__ - a name of the container. You can associate containers with the instances using the `containerName`
parameter in the instance configuration. Default value: `default`.

- __`projectDir`__ - a directory inside the container where the local project will be copied. If
it's a subdirectory of a container volume, the project will be located on that volume, 
otherwise, the data will be lost once the instance is terminated.

- __`image`__ _(optional)_ - the name of the Docker image that contains the environment for your project. For example, 
you could use [TensorFlow image for GPU](https://hub.docker.com/r/tensorflow/tensorflow/) 
(`tensorflow/tensorflow:latest-gpu-py3-jupyter`). It already contains NumPy, SciPy, scikit-learn, pandas, Jupyter Notebook and 
TensorFlow itself. If you need to use your own image, you can specify the path to your Dockerfile in the 
__`file`__ parameter (see below), or push your image to the [Docker Hub](https://hub.docker.com/).

- __`file`__ _(optional)_ - relative path to your custom Dockerfile.
    
    __Note:__ Spotty uses the directory with the Dockerfile as its build context, so make sure it doesn't contain 
    gigabytes of irrelevant data (keep the Dockerfile in a separate directory or use the `.dockerignore` file). 
    Otherwise, you may get an out-of-space error because Docker copies the entire build context to the Docker daemon 
    during the build. Read more here: ["docker build" command](https://docs.docker.com/engine/reference/commandline/build/).

    __Example:__ if you use TensorFlow and need to download your dataset from S3, you could install 
    [AWS CLI](https://github.com/aws/aws-cli) on top of the original TensorFlow image. Just create a 
    `Dockerfile` in the `docker/` directory of your project:
    ```dockerfile
    FROM tensorflow/tensorflow:latest-gpu-py3-jupyter

    RUN pip install awscli
    ```

    Then set the `file` parameter to `docker/Dockerfile`.

- __`runAsHostUser`__ _(optional)_ - if set to `true`, the container will be run with the host user ID and group ID,

- __`volumeMounts`__ _(optional)_ - where to mount instance volumes into the container's filesystem. Each element 
of a list has the following parameters:
    - __`name`__ - this must match the name of an instance volume.
    - __`mountPath`__ - a path within the container at which the volume should be mounted.

- __`workingDir`__ _(optional)_ - working directory for your custom scripts (see "scripts" section below),

- __`env`__ _(optional)_ - a dictionary with environmental variables that will be available in the container,

- __`hostNetwork`__ _(optional)_ - if set to `true`, the Docker container will be run with the host network,

- __`ports`__ _(optional)_ - container ports that should be published to the host. Each element of a list 
contains the following parameters:
    - __`containerPort`__ - a container port,
    - __`hostPort`__ _(optional)_ - a host port. By default, the container port will be published on a random 
    host port.

- __`commands`__ _(optional)_ - commands which should be performed once your container is started. For example, you 
could download your datasets from an S3 bucket to the project directory (see "project" section):
    ```yaml
    commands: |
      aws s3 sync s3://my-bucket/datasets/my-dataset /workspace/project/data
    ```

- __`runtimeParameters`__ _(optional)_ - a list of additional parameters for the container runtime. For example:
    ```yaml
    runtimeParameters: ['--privileged', '--shm-size', '2G']
    ```

### __`instances`__ section

The `instances` section contains a list of instances where each instance is described 
with the following parameters:

- __`name`__ - a name of the instance. Use this name to manage the instance with the commands like 
"spotty start" or "spotty stop". Also Spotty uses this name in the names of AWS and GCP resources.

- __`provider`__ - a provider for the instance. At the moment Spotty supports 4 providers:
    - "__local__" - runs containers using the Docker installed on the local machine,
    - "__remote__" - runs containers on a remote machine through SSH,
    - "__aws__" - Amazon Web Services EC2 instances,
    - "__gcp__" - Google Cloud Platform VMs.

- __`parameters`__ - parameters of the instance. These parameters are different for each provider:
    - [Local Provider Instance Parameters]
    - [Remote Provider Instance Parameters]
    - [AWS Provider Instance Parameters]
    - [GCP Provider Instance Parameters]

### __`scripts`__ section

The `scripts` section contains custom scripts which can be run with the `spotty run <SCRIPT_NAME>` 
command. The following example defines 2 scripts: `jupyter` - to run Jupyter server and `train` - 
to start training a model:

```yaml
scripts:
  jupyter: |
    jupyter notebook --allow-root --ip 0.0.0.0 --notebook-dir=/workspace/project

  train: |
    if [ -n "{{MODEL}}" ]; then
      python /workspace/project/model/train.py --model-name {{MODEL}}
    else
      echo "The MODEL parameter is required."
    fi
```

To start Jupyter simply run:
```bash
spotty run jupyter
```

It will start Jupyter server on the remote instance inside a tmux session. Jupyter will be available on the port
specified in the container configuration (see the example on top of the page).

Copy an authentication token from the command output and use the __`Ctrl + b`__, then __`d`__ combination of keys 
to detach the tmux session - Jupyter will keep running.

You also can write parametrized scripts. For example, the `train` script contains the `MODEL` parameter. So you
could run your training script with different model names:

```bash
spotty run train -p MODEL=my-model
```

Use the __`Ctrl + b`__, then __`d`__ combination of keys to detached tmux session - the script will keep running. 

You can come back to the running script the following ways:
- either use the same command again - you will be reattached to the existing tmux session,
- or connect to the instance using the `spotty sh` command and then use the __`Ctrl + b`__, 
then __`s`__ combination of keys to switch into the right tmux session.

__Note:__ don't forget to use the "|" character for multi-line scripts, otherwise the YAML parser
will merge multiple lines together.


[Local Provider Instance Parameters]: </docs/providers/local/instance-parameters>
[Remote Provider Instance Parameters]: </docs/providers/remote/instance-parameters>
[AWS Provider Instance Parameters]: </docs/providers/aws/instance-parameters>
[GCP Provider Instance Parameters]: </docs/providers/gcp/instance-parameters>
