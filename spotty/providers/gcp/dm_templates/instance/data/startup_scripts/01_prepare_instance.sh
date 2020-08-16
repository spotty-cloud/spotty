#!/bin/bash -xe

# install jq
apt-get install -y jq

# create tmux config
echo "bind-key x kill-pane" > /home/{{SSH_USERNAME}}/.tmux.conf

# create the "container bash" script
mkdir -p "$(dirname '{{CONTAINER_BASH_SCRIPT_PATH}}')"
cat > "{{CONTAINER_BASH_SCRIPT_PATH}}" <<'EOF2'
{{{CONTAINER_BASH_SCRIPT}}}
EOF2
chmod +x "{{CONTAINER_BASH_SCRIPT_PATH}}"

# create an alias to connect to the docker container
CONTAINER_BASH_ALIAS=container
echo "alias $CONTAINER_BASH_ALIAS=\"{{CONTAINER_BASH_SCRIPT_PATH}}\"" >> /home/{{SSH_USERNAME}}/.bashrc
echo "alias $CONTAINER_BASH_ALIAS=\"{{CONTAINER_BASH_SCRIPT_PATH}}\"" >> /root/.bashrc

{{#IS_GPU_INSTANCE}}
# install NVIDIA driver
if ! command -v nvidia-smi &> /dev/null; then
  DRIVER_INSTALLER_PATH=/opt/deeplearning/install-driver.sh
  if [ -f "$DRIVER_INSTALLER_PATH" ]; then
    $DRIVER_INSTALLER_PATH
  fi
fi
{{/IS_GPU_INSTANCE}}

# create common temporary directories
mkdir -pm 777 '{{SPOTTY_TMP_DIR}}'
mkdir -pm 777 '{{CONTAINERS_TMP_DIR}}'
