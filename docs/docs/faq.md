---
layout: default
title: FAQ
nav_order: 6
permalink: /docs/faq/
---

## How does Spotty choose the availability zone where to run the instance?

1. If the AZ is specified in the configuration file, this AZ will be used to run the instance.
2. If the instance already has some EBS volumes created, Spotty will pick up the volumes' AZ.
3. Otherwise Spotty will let AWS choose an AZ. Automatically chosen AZ might not have the 
lowest Spot price, but in practice, it usually does.

Spotty will raise an error if the AZ in the configuration file doesn't match AZs of the volumes 
or AZs of the volumes are different.


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
instances:
  - name: my-instance
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

Use the "__container__" command. This alias is available for the "ubuntu" and "root" users.
