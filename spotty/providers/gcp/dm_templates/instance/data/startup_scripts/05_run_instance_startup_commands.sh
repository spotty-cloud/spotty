#!/bin/bash -xe

mkdir -p "{{INSTANCE_STARTUP_SCRIPTS_DIR}}"
cat > "{{INSTANCE_STARTUP_SCRIPTS_DIR}}/instance_startup_commands.sh" <<'EOF2'
{{{INSTANCE_STARTUP_COMMANDS}}}
EOF2

/bin/bash -xe "{{INSTANCE_STARTUP_SCRIPTS_DIR}}/instance_startup_commands.sh"
