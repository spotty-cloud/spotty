# EBS Volumes and Deletion Policies

By default, EBS volumes have names in the following format: `<PROJECT_NAME>-<INSTANCE_NAME>-<VOLUME_NAME>`.
But you can specify a custom name using the `volumeName` parameter. 

When you're starting an instance:
1. Spotty is looking for existing EBS volumes using their names. If a volume exists, it will be attached to the 
instance.
2. If not - Spotty will be looking for a snapshot with the same name. If the snapshot exists, the volume will be 
restored from that snapshot.
3. If neither snapshot nor volume with this name exists, new EBS volume will be created. 

When you're stopping the instance Spotty applies deletion policies for the volumes. There are 4 deletion policies that 
can be specified using the `deletionPolicy` parameter:

- __Retain__: this is the default deletion policy. The volume will retain, a snapshot won't be created.

- __CreateSnapshot__: Spotty will create a new snapshot every time you're stopping an instance, the old snapshot 
will be renamed. AWS uses incremental snapshots, so each new snapshot keeps only the data that was changed since 
the last snapshot made (see: 
[How Incremental Snapshots Work](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSSnapshots.html#how_snapshots_work)).

- __UpdateSnapshot__: a new snapshot will be created and the old one will be deleted.

- __Delete__: the volume will be deleted without creating a snapshot. All data on this volume will be lost.
