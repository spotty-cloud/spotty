---
layout: default
title: Volumes and Deletion Policies
parent: AWS
nav_order: 3
permalink: /docs/aws/volumes-and-deletion-policies/
---

# Volumes and Deletion Policies

The name of the EBS volume can be specified using the `volumeName` parameter. By default, the name of the EBS
volume is a concatenation of the project name, the instance name and the volume name: 
"{project_name}-{instance_name}-{volume_name}".

When you're starting an instance:
1. Spotty is looking for the EBS volume with this name. If the volume exists, it will be attached to the instance.
2. If not - Spotty will be looking for a snapshot with this name. If the snapshot exists, the volume will be restored 
from the found snapshot.
3. If neither snapshot, nor volume with this name exists, new empty volume will be created. 

When you're stopping the instance Spotty applies deletion policies for the volumes. There are 4 deletion policies that 
can be specified using the `deletionPolicy` parameter:

- __create_snapshot__: this is the default deletion policy. Spotty will create new snapshot every time you're 
stopping an instance, the old snapshot will be renamed. AWS uses incremental snapshots, so each new snapshot keeps 
only the data that was changed since the last snapshot made (see: 
[How Incremental Snapshots Work](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSSnapshots.html#how_snapshots_work){:target="_blank"}).

- __update_snapshot__: new snapshot will be created and the old one will be deleted.

- __retain__: the volume will not be deleted and the snapshot will not be created.

- __delete__: the volume will be deleted without creating a snapshot. All data on this volume will be lost.
