#!/usr/bin/env bash

{{bash_flags}}

if {{{is_created_cmd}}}; then
  printf 'Removing existing container... '
  {{{remove_cmd}}}
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
