#!/bin/bash -xe

/bin/bash -xe {{INSTANCE_SCRIPTS_DIR}}/run_container.sh \
  --container-name="${ContainerName}" \
  --image-name="${DockerImage}" \
  --dockerfile-path="${DockerfilePath}" \
  --docker-context-path="${DockerBuildContextPath}" \
  --docker-runtime-params="${DockerRuntimeParameters}" \
  --working-dir="${DockerWorkingDirectory}" \
  --startup-script-path={{CONTAINER_SCRIPTS_DIR}}/container_startup_commands.sh \
  --send-resource-signals=TRUE
