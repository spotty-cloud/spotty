#!/bin/bash -xe

/bin/bash -xe {{RUN_CONTAINER_SCRIPT_PATH}} \
  --container-name="${ContainerName}" \
  --image-name="${DockerImage}" \
  --dockerfile-path="${DockerfilePath}" \
  --docker-context-path="${DockerBuildContextPath}" \
  --docker-runtime-params="${DockerRuntimeParameters}" \
  --working-dir="${DockerWorkingDirectory}" \
  --startup-script-path={{CONTAINER_STARTUP_SCRIPT_PATH}} \
  --send-resource-signals=TRUE
