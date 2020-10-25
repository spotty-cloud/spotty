#!/usr/bin/env bash

set -e

if {{{is_created_cmd}}}; then
  printf 'Removing the container... '
  {{{remove_cmd}}}
  echo 'DONE'
else
  echo 'Container is not running.'
fi
