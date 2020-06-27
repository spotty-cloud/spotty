#!/usr/bin/env bash

{{bash_flags}}

if [[ $(docker ps -aq --filter "name={{container_name}}" | wc -c) -ne 0 ]]; then
  printf 'Removing running container... '
  docker rm -f "{{container_name}}" > /dev/null
  echo 'DONE'
fi

{{> before_image_build}}

{{#build_image_cmd}}
echo 'Building Docker image...'
{{{build_image_cmd}}}
{{/build_image_cmd}}

{{> before_container_run}}

printf 'Starting container... '
{{{start_container_cmd}}}
echo 'DONE'

{{> before_startup_commands}}

{{#docker_exec_startup_script_cmd}}
echo 'Running startup commands...'
{{{docker_exec_startup_script_cmd}}}
{{/docker_exec_startup_script_cmd}}
