---
layout: default
title: Instance Parameters
parent: GCP Provider (beta)
nav_order: 2
permalink: /docs/gcp-provider/instance-parameters/
---

# GCP Instance Parameters

Instance parameters are part of the [configuration file]({{ site.baseurl }}/docs/configuration-file/), but 
for each provider they are different. Here you can find parameters for a GCP instance:

- __`zone`__ - GCP zone where to run an instance.

- __`machineType`__ - a type of the instance to run. You can find a list of predefined machine types
here: [Machine Types](https://cloud.google.com/compute/docs/machine-types){:target="_blank"}. If you in doubt what to use,
just go for `n1-standard-1`. To attach GPUs to the selected machine type, use the `gpu` parameter (see 
the details below).

- __`gpu`__ _(optional)_ - _a dictionary with keys `type` and `count`_:
    - __`type`__ - a type of GPU to attach to the instance. Read more about GPUs and their availabily
    in different zones here: [GPUs on Compute Engine](https://cloud.google.com/compute/docs/gpus/){:target="_blank"}.
    - __`count`__ _(optional)_ - a number of GPUs that should be attached to the instance. The default
    value is 1. See here a number of GPUs that you can attach to different machine types: 
    [Valid numbers of GPUs for each machine type](https://cloud.google.com/ml-engine/docs/tensorflow/using-gpus#gpu-compatibility-table){:target="_blank"}.

- __`onDemandInstance`__ _(optional)_ - run an on-demand instance instead of a preemptible one (available values are 
"true" or "false"). By default, this value is "false", so Spotty will be running a preemptible instance. __Note:__ be 
aware that GCP terminates preemptible instances in 24 hours. Read more about Preemptible VMs 
[here](https://cloud.google.com/compute/docs/instances/preemptible){:target="_blank"}.

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
Read more: [How to cache a Docker image]({{ site.baseurl }}/docs/faq/#how-to-cache-a-docker-image).

- __`volumes`__ _(optional)_ - the list of volumes to attach to the instance:
    - __`name`__ - a name of the volume. This name should match one of the container's `volumeMounts` to have this 
    volume attached to the container's filesystem.

    - __`parameters`__ _(optional)_ - parameters of the volume:
        - __`size`__ _(optional)_ - size of the disk in GB. Size of the disk cannot be less than the size of 
        the existing snapshot but can be increased.

        - __`deletionPolicy`__ _(optional)_ - what to do with the disk once the instance is terminated using the 
        `spotty stop` command. Possible values include: "__create_snapshot__" _(value by default)_, "__update_snapshot__", 
        "__retain__" and  "__delete__". Read more: 
        [Disks and Deletion Policies]({{ site.baseurl }}/docs/gcp-provider/disks-and-deletion-policies/).
        
            __(!) Note:__ Deletion Policies are not implemented yet, so your disks will always retain.

        - __`diskName`__ _(optional)_ - name of the disk. The default name is 
        "{project_name}-{instance_name}-{volume_name}".

        - __`mountDir`__ _(optional)_ - directory where the disk will be mounted on the instance. The default 
        directory is "/mnt/{disk_name}".

- __`localSshPort`__ _(optional)_ - if the local SSH port is specified, the commands `spotty sh`, `spotty run` 
and `spotty sync` will do SSH connections to the instance using the IP address __127.0.0.1__ and the specified port. 
It can be useful in case when the instance doesn't have a public IP address and SSH access is provided through a 
tunnel to a local port.

- __`commands`__ _(optional)_ - commands that should be run on the host OS before a container is started.
