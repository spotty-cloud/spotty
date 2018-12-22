---
layout: default
title: FAQ
parent: AWS
nav_order: 3
---

## How does Spotty choose the availability zone where to run the instance?

1. If the AZ is specified in the configuration file, this AZ will be used to run the instance.
2. If the instance already has some EBS volumes created, Spotty will pick up the volumes' AZ.
3. Otherwise Spotty will let AWS to choose the AZ. Automatically chosen AZ might not have the 
lowest Spot price, but in practice it's usually does.

Spotty will raise an error if the AZ in the configuration file doesn't match AZs of the volumes 
or AZs of the volumes are different.


## How to cache a built Docker image?

Configuration file has the "__dockerDataRoot__" parameter. It's a directory on
the host OS where the Docker daemon will save all the downloaded and built images.

Specify the `moundDir` directory for one of the instance volumes and set the `dockerDataRoot` parameter
to the same value or to a subdirectory of the `moundDir` directory. Also consider to change a deletion policy
of that volume to "__retain__". Then the volume with your image will not be deleted and next time it just will be attached
to the instance.

## How to connect to the running container from the host OS?

Use the "__container__" command. This alias is available for the "ubuntu" and "root" users.
