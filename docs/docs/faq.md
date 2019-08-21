---
layout: default
title: FAQ
nav_order: 6
permalink: /docs/faq/
---

## How to cache a Docker image?

You can cache images that you've built or downloaded from the internet on an EBS volume or in a snapshot.

A configuration file has the "__dockerDataRoot__" parameter. It's a directory on the host OS where the Docker 
daemon will save all the images.

Specify the `moundDir` directory for one of the instance volumes and set the `dockerDataRoot` parameter
to the same value (or to a subdirectory of the `moundDir` directory). Also, consider changing a deletion policy
for that volume to "__retain__", then the volume with the cache will be retained and the next time it just will be 
attached to the instance.

Example:
```yaml
# ...

instances:
  - name: i1
    provider: aws
    parameters:
      # ...
      dockerDataRoot: /docker
      volumes:
        # ...
        - name: docker
          parameters:
            size: 10
            mountDir: /docker
            deletionPolicy: retain
```


## How to connect to the running container from the host OS?

Use the "__container__" command. This alias is available for the "ubuntu" and "root" users. You might want
to use this alias when you're creating a new tmux window using the __`Ctrl + b`__, then __`c`__ combination of keys.


## How does Spotty choose the AWS Availability Zone where to run the instance?

1. If the AZ is specified in the configuration file, this AZ will be used to run the instance.
2. If the instance already has some EBS volumes created, Spotty will pick up the volumes' AZ.
3. Otherwise Spotty will let AWS choose an AZ. Automatically chosen AZ might not have the 
lowest Spot price, but in practice, it usually does.

Spotty will raise an error if the AZ in the configuration file doesn't match AZs of the volumes 
or AZs of the volumes are different.


## Why an instance is launching too long?

Most likely the instance cannot be launched because you're trying to launch a Spot instance
and it cannot be fulfilled. You can try to change the region or availability zone, choose another
type of the instance, or run an On-demand Instance by setting the `onDemandInstance` parameter to `true`.


## The instance is failed to start. Where can I find the logs?

1. If the CloudFormation stack is failed to start during the container creation, then the instance is launched, 
but the container is failed to start. So you can connect to the host OS using the following command:

    ```bash
    spotty ssh -H
    ```
    
    Then you can check the `cfn-init` logs to find out why the container is failed:
    ```bash
    sudo tail /var/log/cfn-init-cmd.log
    ```

2. If the stack is failed when launching an instance, then check the CloudFormation logs in AWS Console.


## How to ssh to a Spotty instance from a different machine?

When you start an instance, Spotty creates an EC2 Key Pair and downloads a private key to the 
`~/.spotty/keys/aws` directory. If you want to have access to the instance from a different machine using 
the `spotty ssh` or the `spotty run` commands, you need to copy the private key to that machine to the same directory.

__Note:__ if you already have an EC2 Key Pair created for the project and the private key was 
saved on the machine A (where from an instance was launched the first time) and then you're running
an instance for the same project from the machine B that doesn't have a private key in the `~/.spotty/keys/aws` 
directory, then the EC2 Key Pair will be recreated and the machine A will not be able to connect to instances 
because its private key doesn't match the EC2 Key Pair anymore.
