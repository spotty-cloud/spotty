#!/bin/bash -xe

cfn-signal -e 0 --stack ${AWS::StackName} --region ${AWS::Region} --resource SettingDockerRootSignal

# change docker data root directory
if [ -n "${DockerDataRootDirectory}" ]; then
  jq '. + { "data-root": "${DockerDataRootDirectory}" }' /etc/docker/daemon.json > /tmp/docker_daemon.json \
    && mv /tmp/docker_daemon.json /etc/docker/daemon.json
  service docker restart
fi
