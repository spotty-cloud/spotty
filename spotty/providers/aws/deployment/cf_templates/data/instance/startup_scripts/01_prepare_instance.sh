#!/bin/bash -xe

cfn-signal -e 0 --stack ${AWS::StackName} --region ${AWS::Region} --resource PreparingInstanceSignal

# install AWS CLI
update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
apt-get update && apt-get install -y python3-pip
pip3 install -U awscli
aws configure set default.region ${AWS::Region}

# install jq
apt-get install -y jq

# create a directory for Docker scripts
mkdir -p {{HOST_CONTAINER_RUN_SCRIPTS_DIR}}
chmod -R 755 {{INSTANCE_SPOTTY_TMP_DIR}}
chown -R ubuntu:ubuntu {{INSTANCE_SPOTTY_TMP_DIR}}

# create an alias to connect to the docker container
CONTAINER_BASH_ALIAS=container
echo "alias $CONTAINER_BASH_ALIAS=\"{{CONTAINER_BASH_SCRIPT_PATH}}\"" >> /home/ubuntu/.bashrc
echo "alias $CONTAINER_BASH_ALIAS=\"{{CONTAINER_BASH_SCRIPT_PATH}}\"" >> /root/.bashrc
