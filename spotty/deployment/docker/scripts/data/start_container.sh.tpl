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

i=0
until [ "$i" -ge 3 ]
do
  if [ "$i" -eq 0 ]; then
    printf 'Starting container... '
  else
    echo "Retrying to start the container $i..."
  fi

  RUN_EXIT_CODE=0
  {{{start_container_cmd}}} || RUN_EXIT_CODE=$?

  if [ "$RUN_EXIT_CODE" -ne 125 ]; then
    break
  fi

  i=$((i+1))
  sleep 10
done

if [ "$RUN_EXIT_CODE" -ne 0 ]; then
  exit $RUN_EXIT_CODE
fi

echo 'DONE'

{{> before_startup_commands}}

{{#docker_exec_startup_script_cmd}}
echo 'Running startup commands...'
{{{docker_exec_startup_script_cmd}}}
{{/docker_exec_startup_script_cmd}}
