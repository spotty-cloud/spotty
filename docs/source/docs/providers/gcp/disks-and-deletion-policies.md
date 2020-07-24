# Disks and Deletion Policies

By default, disks have names in the following format: `<PROJECT_NAME>-<INSTANCE_NAME>-<VOLUME_NAME>`.
But you can specify a custom name using the `diskName` parameter. 

When you're starting an instance:
1. Spotty is looking for existing disks using their names. If a disk exists, it will be attached to the 
instance.
2. If not - Spotty will be looking for a snapshot with the same name. If the snapshot exists, the disk will be 
restored from that snapshot.
3. If neither snapshot nor disk with this name exists, a new disk will be created. 

__Note:__ Deletion Policies for the GCP provider are not implemented yet, so, regardless of the `deletionPolicy` 
parameter value, created disks will retain when the instance is terminated.
