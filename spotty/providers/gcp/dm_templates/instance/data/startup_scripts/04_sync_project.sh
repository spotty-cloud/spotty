#!/bin/bash -xe

# create a project directory
if [ -n "{{HOST_PROJECT_DIR}}" ]; then
  mkdir -p "{{HOST_PROJECT_DIR}}"
  chmod 777 "{{HOST_PROJECT_DIR}}"
fi

{{{SYNC_PROJECT_CMD}}}
