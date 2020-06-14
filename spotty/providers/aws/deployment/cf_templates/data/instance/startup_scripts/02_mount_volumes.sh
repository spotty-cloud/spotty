#!/bin/bash -xe

cfn-signal -e 0 --stack ${AWS::StackName} --region ${AWS::Region} --resource MountingVolumesSignal

# mount volumes
DEVICE_LETTERS=(f g h i j k l m n o p)
MOUNT_DIRS=(${VolumeMountDirectories})

for i in ${!!MOUNT_DIRS[*]}
do
  DEVICE=/dev/xvd${!DEVICE_LETTERS[$i]}
  MOUNT_DIR=${!MOUNT_DIRS[$i]}

  blkid -o value -s TYPE $DEVICE || mkfs -t ext4 $DEVICE
  mkdir -p $MOUNT_DIR
  mount $DEVICE $MOUNT_DIR
  resize2fs $DEVICE
done
