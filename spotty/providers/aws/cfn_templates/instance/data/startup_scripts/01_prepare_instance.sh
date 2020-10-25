#!/bin/bash -xe

cfn-signal -e 0 --stack ${AWS::StackName} --region ${AWS::Region} --resource PreparingInstanceSignal

# install AWS CLI
update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
apt-get update && apt-get install -y python3-pip
pip3 install -U awscli
aws configure set default.region ${AWS::Region}

# install jq
apt-get install -y jq

# create an alias to connect to the docker container
CONTAINER_BASH_ALIAS=container
echo "alias $CONTAINER_BASH_ALIAS=\"{{CONTAINER_BASH_SCRIPT_PATH}}\"" >> /home/ubuntu/.bashrc
echo "alias $CONTAINER_BASH_ALIAS=\"{{CONTAINER_BASH_SCRIPT_PATH}}\"" >> /root/.bashrc

# create common temporary directories
mkdir -pm 777 '{{SPOTTY_TMP_DIR}}'
mkdir -pm 777 '{{CONTAINERS_TMP_DIR}}'
