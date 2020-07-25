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

{{#pull_image_cmd}}
i=0
until [ "$i" -ge 3 ]
do
  if [ "$i" -ne 0 ]; then
    echo "Retrying to pull the image $i..."
  fi

  PULL_EXIT_CODE=0
  {{{pull_image_cmd}}} || PULL_EXIT_CODE=$?

  if [ "$PULL_EXIT_CODE" -ne 125 ]; then
    break
  fi

  i=$((i+1))
  sleep 10
done

if [ "$PULL_EXIT_CODE" -ne 0 ]; then
  exit $PULL_EXIT_CODE
fi
{{/pull_image_cmd}}

printf 'Starting container... '
{{{start_container_cmd}}}
echo 'DONE'

{{> before_startup_commands}}

{{#docker_exec_startup_script_cmd}}
echo 'Running startup commands...'
{{{docker_exec_startup_script_cmd}}}
{{/docker_exec_startup_script_cmd}}
