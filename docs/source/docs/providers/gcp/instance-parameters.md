# Instance Parameters

Instance parameters are part of the [configuration file], but for each provider they are different. 
Here you can find parameters for a GCP instance:

- __`containerName`__ _(optional)_ - a name of the container from the `containers` section.
Default value: `default`.

- __`zone`__ - GCP zone where to run an instance.

- __`machineType`__ - a type of the instance to run. You can find a list of predefined machine types
here: [Machine Types](https://cloud.google.com/compute/docs/machine-types). If you in doubt what to use,
just go for `n1-standard-1`. To attach GPUs to the selected machine type, use the `gpu` parameter (see 
the details below).

- __`gpu`__ _(optional)_ - _a dictionary with keys `type` and `count`_:
    - __`type`__ - a type of GPU to attach to the instance. Read more about GPUs and their availabily
    in different zones here: [GPUs on Compute Engine](https://cloud.google.com/compute/docs/gpus/).
    - __`count`__ _(optional)_ - a number of GPUs that should be attached to the instance. The default
    value is 1. See here a number of GPUs that you can attach to different machine types: 
    [Valid numbers of GPUs for each machine type](https://cloud.google.com/ml-engine/docs/tensorflow/using-gpus#gpu-compatibility-table).

- __`preemptibleInstance`__ _(optional)_ - if set to `true`, runs a preemptible instance instead of an on-demand 
instance. __Note:__ be aware that GCP terminates preemptible instances in 24 hours. Read more about Preemptible VMs 
[here](https://cloud.google.com/compute/docs/instances/preemptible).

- __`imageName`__ _(optional)_ - a name of the image with NVIDIA Docker in the current GCP project. You can use 
the `spotty gcp create-image` command to create it. By default, the command will create an image with the name 
"spotty". This image will be used to run your application inside the Docker container. If you didn't create your own 
image, see the behaviour of the `imageUrl` parameter.

- __`imageUrl`__ _(optional)_ - a URL of the image with NVIDIA Docker. You can use this parameter to work with an image
from another GCP project. If this parameter is not specified and you didn't create your own image (see the `imageName` 
parameter), Spotty will be using the `projects/spotty-cloud/global/images/family/spotty` image provided by the Spotty 
project.

- __`bootDiskSize`__ _(optional)_ - size of the root volume in GB. The root volume will be destroyed once 
the instance is terminated. Use attached volumes to store the data that you need to keep (see the `volumes` 
parameter below).

- __`dockerDataRoot`__ _(optional)_ - directory where Docker will store all downloaded and built images. 
Read more: [Caching Docker Image on a Disk].

- __`volumes`__ _(optional)_ - the list of volumes to attach to the instance:
    - __`name`__ - a name of the volume. This name should match one of the container's `volumeMounts` to have this 
    volume attached to the container's filesystem.

    - __`parameters`__ _(optional)_ - parameters of the volume:
        - __`size`__ _(optional)_ - size of the disk in GB. Size of the disk cannot be less than the size of 
        the existing snapshot but can be increased.

        - __`deletionPolicy`__ _(optional)_ - what to do with the disk once the instance is terminated using the 
        `spotty stop` command. Possible values include: "__Retain__" _(value by default)_, "__CreateSnapshot__", 
        "__UpdateSnapshot__" and  "__Delete__". Read more: [Disks and Deletion Policies].
        
            __(!) Note:__ Deletion Policies are not implemented yet, so created disks will always retain.

        - __`diskName`__ _(optional)_ - name of the disk. The default name is 
        "{project_name}-{instance_name}-{volume_name}".

        - __`mountDir`__ _(optional)_ - directory where the disk will be mounted on the instance. The default 
        directory is "/mnt/{disk_name}".

- __`ports`__ _(optional)_ - list of ports to open on the instance. For example:
    ```yaml
    ports: [6006, 8888]
    ```
    It will open ports 6006 for TensorBoard and 8888 for Jupyter Notebook. 

- __`localSshPort`__ _(optional)_ - if this parameter is set, all the Spotty commands will create SSH connections 
with the instance using the IP address __127.0.0.1__ and the specified port. This can be useful in case when an 
instance doesn't have a public IP address and a jump-server is used for tunneling.

- __`commands`__ _(optional)_ - commands that should be run on the host OS before the container is started.


[configuration file]: </docs/user-guide/configuration-file>
[Caching Docker Image on a Disk]: </docs/providers/gcp/caching-docker-image-on-a-disk>
[Disks and Deletion Policies]: </docs/providers/gcp/disks-and-deletion-policies>
