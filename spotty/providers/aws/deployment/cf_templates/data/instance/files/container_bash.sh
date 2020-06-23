#!/bin/bash -e

if [ -z "$SPOTTY_CONTAINER_NAME" ]; then
  echo -e "\nSPOTTY_CONTAINER_NAME environmental variable is not set.\n"
  exit 1
fi

if [[ $(docker ps -aq --filter "name=$SPOTTY_CONTAINER_NAME" | wc -c) -eq 0 ]]; then
  echo -e "\nContainer $SPOTTY_CONTAINER_NAME is not running.\n"
  exit 1
fi

SPOTTY_CONTAINER_WORKING_DIR=${SPOTTY_CONTAINER_WORKING_DIR:-/}

{{{ DOCKER_EXEC_BASH }}} "$@"
