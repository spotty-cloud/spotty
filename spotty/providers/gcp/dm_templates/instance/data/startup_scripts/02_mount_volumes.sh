#!/bin/bash -xe

DEVICE_NAMES=({{{DISK_DEVICE_NAMES}}})
MOUNT_DIRS=({{{DISK_MOUNT_DIRS}}})

for i in ${!DEVICE_NAMES[*]}
do
  DEVICE=/dev/disk/by-id/google-${DEVICE_NAMES[$i]}
  MOUNT_DIR=${MOUNT_DIRS[$i]}

  blkid -o value -s TYPE $DEVICE || mkfs -t ext4 $DEVICE
  mkdir -p $MOUNT_DIR
  mount $DEVICE $MOUNT_DIR
  chmod 777 $MOUNT_DIR
  resize2fs $DEVICE
done

# create directories for temporary container volumes
{{#TMP_VOLUME_DIRS}}
mkdir -p {{PATH}}
chmod 777 {{PATH}}
{{/TMP_VOLUME_DIRS}}
