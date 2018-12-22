---
layout: default
title: Instance Parameters
parent: AWS
nav_order: 2
permalink: /docs/aws/instance-parameters/
---

# Instance Parameters

- __`region`__ - AWS region where to run an instance (you can use command `spotty spot-prices` to find the 
cheapest region).
- __`availabilityZone`__ _(optional)_ - AWS availability zone where to run an instance. If zone is not specified, it 
will be chosen automatically.
- __`subnetId`__ _(optional)_ - AWS subnet ID. If this parameter is set, the "availabilityZone" parameter should be set as well. If it's not specified, a default subnet will be used.
- __`instanceType`__ - type of the instance to run. You can find more information about 
types of GPU instances here: 
[Recommended GPU Instances](https://docs.aws.amazon.com/dlami/latest/devguide/gpu.html).
- __`onDemandInstance`__ _(optional)_ - run On-demand instance instead of a Spot instance. Available values: "true", "false" (default value is "false").
- __`amiName`__ _(optional)_ - name of the AMI with NVIDIA Docker (default value is "SpottyAMI"). Use 
`spotty create-ami` command to create it. This AMI will be used to run your application inside the Docker container.
- __`maxPrice`__ _(optional)_ - the maximum price per hour that you are willing to pay for a Spot Instance. By default, it's 
On-Demand price for chosen instance type. Read more here: 
[Spot Instances](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-spot-instances.html).
- __`rootVolumeSize`__ _(optional)_ - size of the root volume in GB. The root volume will be destroyed once 
the instance is terminated. Use attached volumes to store the data you need to keep (see "volumes" parameter below).
- __`volumes`__ _(optional)_ - the list of volumes to attach to the instance:
    - __`name`__ _(optional)_ - name of the volume. This parameter is optional only if the `deletionPolicy` parameter 
    is set to "delete".
    
        When you're starting an instance, Spotty is looking for a volume 
        with this name. If the volume exists, it will be attached to the instance, if not - Spotty will be looking for a 
        snapshot with this name. If the snapshot exists, the volume will be restored from the found snapshot. If neither 
        snapshot, nor volume with this name exists, new empty volume will be created. 

    - __`directory`__ - directory where the volume will be mounted,
    - __`size`__ _(optional)_ - size of the volume in GB. Size of the volume cannot be less then the size of existing 
    snapshot, but can be increased.
    - __`deletionPolicy`__ _(optional)_ - what to do with the volume once the instance is terminated using the 
    `spotty stop` command. Possible values include: "__create_snapshot__" _(value by default)_, "__update_snapshot__", 
    "__retain__" and  "__delete__".

        For "__create_snapshot__" (by default), Spotty will create new snapshot every time you're stopping an instance, the old snapshot will be 
        renamed. AWS uses incremental snapshots, so each new snapshot keeps only the data that was changed since the 
        last snapshot made (see: 
        [How Incremental Snapshots Work](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSSnapshots.html#how_snapshots_work)).

        For "__update_snapshot__", new snapshot will be created and the old one will be deleted.
        
        For "__retain__", the volume will not be deleted and snapshot will not be 
        taken.
        
        For  "__delete__", the volume will be deleted without creating a snapshot.

        __Note:__ Deletion policy works only for volumes that were created from scratch or from snapshots during the 
        `spotty start` command. So if the volume already existed and was just attached to the instance, it will 
        retain after the instance deletion, even if you had a different value in the DeletionPolicy.

- __`docker`__ - Docker configuration:
    - __`dataRoot`__ _(optional)_ - directory where Docker will store all downloaded and built images. You could cache 
    images on your attached volume to avoid downloading them from internet or building your custom image from scratch 
    every time when you start an instance.

- __`localSshPort`__ _(optional)_ - if the local SSH port is specified, the commands `spotty ssh`, `spotty run` and `spotty sync` will do SSH connections to the instance using the IP address __127.0.0.1__ and the specified port. It can be useful in case when the instance doesn't have a public IP address and SSH access is provided through a tunnel to a local port.
