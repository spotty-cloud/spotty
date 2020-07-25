#!/usr/bin/env bash

set -x

mkdir -p "{{INSTANCE_STARTUP_SCRIPTS_DIR}}"

# create startup scripts
{{#STARTUP_SCRIPTS}}
cat <<'EOF' > {{INSTANCE_STARTUP_SCRIPTS_DIR}}/{{filename}}
{{{content}}}
EOF
chmod +x {{INSTANCE_STARTUP_SCRIPTS_DIR}}/{{filename}}

{{/STARTUP_SCRIPTS}}

# run startup scripts
{{#STARTUP_SCRIPTS}}
{{INSTANCE_STARTUP_SCRIPTS_DIR}}/{{filename}} && \
{{/STARTUP_SCRIPTS}}
true

# send signal that the Docker container is ready or failed
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  gcloud beta runtime-config configs variables set /success/1 1 --config-name {{MACHINE_NAME}}-docker-status --is-text
else
  gcloud beta runtime-config configs variables set /failure/1 1 --config-name {{MACHINE_NAME}}-docker-status --is-text
  exit $EXIT_CODE
fi
