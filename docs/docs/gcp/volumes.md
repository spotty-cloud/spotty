---
layout: default
title: Disks and Deletion Policies
parent: GCP Provider (beta)
nav_order: 4
permalink: /docs/gcp-provider/disks-and-deletion-policies/
---

# Disks and Deletion Policies

By default, disks have names in the following format: `<PROJECT_NAME>-<INSTANCE_NAME>-<VOLUME_NAME>`.
But you can specify a custom name using the `diskName` parameter. 

When you're starting an instance:
1. Spotty is looking for existing disks using their names. If a disk exists, it will be attached to the 
instance.
2. If not - Spotty will be looking for a snapshot with the same name. If the snapshot exists, the disk will be 
restored from that snapshot.
3. If neither snapshot nor disk with this name exists, a new disk will be created. 

### __(!) Note:__ Deletion Policies are not implemented yet, so your disks will always retain. Below you can see how it's supposed to work.

When you're stopping the instance Spotty applies deletion policies for the disks. There are 4 deletion policies that 
can be specified using the `deletionPolicy` parameter:

- __create_snapshot__: this is the default deletion policy. Spotty will create a new snapshot every time you're 
stopping an instance, the old snapshot will be renamed. GCP uses incremental snapshots, so each new snapshot keeps 
only the data that was changed since the last snapshot made (see: 
[Creating persistent disk snapshots](https://cloud.google.com/compute/docs/disks/create-snapshots){:target="_blank"}).

- __update_snapshot__: a new snapshot will be created and the old one will be deleted.

- __retain__: the disk won't be deleted and a snapshot won't be created.

- __delete__: the disk will be deleted without creating a snapshot. All data on this disk will be lost.
