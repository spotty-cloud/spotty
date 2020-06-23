#!/bin/bash -xe

/bin/bash -xe {{RUN_CONTAINER_SCRIPT_PATH}} \
  --container-name="${ContainerName}" \
  --image-name="${DockerImage}" \
  --dockerfile-path="${DockerfilePath}" \
  --docker-context-path="${DockerBuildContextPath}" \
  --docker-runtime-params="${DockerRuntimeParameters}" \
  --working-dir="${DockerWorkingDirectory}" \
  --startup-script-base64={{CONTAINER_STARTUP_SCRIPT_BASE64}} \
  --send-resource-signals=TRUE
