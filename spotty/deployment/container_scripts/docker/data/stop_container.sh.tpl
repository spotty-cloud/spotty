#!/usr/bin/env bash

set -e

if [[ $(docker ps -aq --filter "name={{container_name}}" | wc -c) -ne 0 ]]; then
  printf 'Removing running container... '
  docker rm -f "{{container_name}}" > /dev/null
  echo 'DONE'
else
  echo 'Container is not running.'
fi
