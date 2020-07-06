#!/bin/bash -e

if [ -z "$SPOTTY_CONTAINER_NAME" ]; then
  echo -e "\nSPOTTY_CONTAINER_NAME environmental variable is not set.\n"
  exit 1
fi

SPOTTY_CONTAINER_WORKING_DIR=${SPOTTY_CONTAINER_WORKING_DIR:-/}

{{{docker_exec_bash}}}
