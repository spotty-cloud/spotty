#!/bin/bash -xe

# change docker data root directory
if [ -n "{{DOCKER_DATA_ROOT_DIR}}" ]; then
  jq '. + { "data-root": "{{DOCKER_DATA_ROOT_DIR}}" }' /etc/docker/daemon.json > /tmp/docker_daemon.json \
    && mv /tmp/docker_daemon.json /etc/docker/daemon.json
  service docker restart
fi
