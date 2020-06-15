#!/bin/bash -e

while [ $# -gt 0 ]; do
  case "$1" in
    --container-name=*)
      CONTAINER_NAME="${!1#*=}"
      ;;
    --image-name=*)
      IMAGE_NAME="${!1#*=}"
      ;;
    --dockerfile-path=*)
      DOCKERFILE_PATH="${!1#*=}"
      ;;
    --docker-context-path=*)
      DOCKER_CONTEXT_PATH="${!1#*=}"
      ;;
    --docker-runtime-params=*)
      DOCKER_RUNTIME_PARAMS="${!1#*=}"
      ;;
    --working-dir=*)
      WORKING_DIR="${!1#*=}"
      ;;
    --startup-script-path=*)
      STARTUP_SCRIPT_PATH="${!1#*=}"
      ;;
    --send-resource-signals=*)
      SEND_RESOURCE_SIGNALS="${!1#*=}"
      ;;
    *)
      printf "***************************\n"
      printf "* Error: Invalid argument.*\n"
      printf "***************************\n"
      exit 1
  esac
  shift
done

# remove container with this name if it exists
if [[ $(docker ps -aq --filter "name=$CONTAINER_NAME" | wc -c) -ne 0 ]]; then
  echo 'Removing running container...'
  docker rm -f "$CONTAINER_NAME" > /dev/null
fi

# build docker image
if [ -n "$SEND_RESOURCE_SIGNALS" ]; then
  cfn-signal -e 0 --stack ${AWS::StackName} --region ${AWS::Region} --resource BuildingDockerImageSignal
fi

if [ -n "$DOCKERFILE_PATH" ]; then
  echo 'Building Docker image...'
  IMAGE_NAME=$CONTAINER_NAME:$(date +%s)
  docker build -t "$IMAGE_NAME" -f "$DOCKERFILE_PATH" "$DOCKER_CONTEXT_PATH"
fi

# run docker container
if [ -n "$SEND_RESOURCE_SIGNALS" ]; then
  cfn-signal -e 0 --stack ${AWS::StackName} --region ${AWS::Region} --resource StartingContainerSignal
fi

if [ -n "$IMAGE_NAME" ]; then
  echo 'Starting container...'

  NVIDIA_RUNTIME=""
  if nvidia-smi > /dev/null; then
    NVIDIA_RUNTIME="--gpus all"
  fi

  docker run -td --net=host $NVIDIA_RUNTIME $DOCKER_RUNTIME_PARAMS \
    -v /root/.aws:/root/.aws \
    -v {{HOST_SCRIPTS_DIR}}:{{CONTAINER_SCRIPTS_DIR}} \
    --name "$CONTAINER_NAME" "$IMAGE_NAME" /bin/sh \
    > /dev/null
fi

# run custom user commands
if [ -n "$SEND_RESOURCE_SIGNALS" ]; then
  cfn-signal -e 0 --stack ${AWS::StackName} --region ${AWS::Region} --resource RunningContainerStartupCommandsSignal
fi

if [ -n "$IMAGE_NAME" ] && [ -n "$STARTUP_SCRIPT_PATH" ]; then
  echo 'Running startup commands...'
  docker exec ${!WORKING_DIR:+-w "$WORKING_DIR"} "$CONTAINER_NAME" /bin/bash -xe "$STARTUP_SCRIPT_PATH"
fi
