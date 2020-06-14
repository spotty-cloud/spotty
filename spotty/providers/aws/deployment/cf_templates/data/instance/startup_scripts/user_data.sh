#!/bin/bash -x

cd /root || exit 1

# install CloudFormation tools if they are not installed yet
if [ ! -e /usr/local/bin/cfn-init ]; then
  apt-get update
  apt-get install -y python-setuptools
  mkdir -p aws-cfn-bootstrap-latest
  curl https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz | tar xz -C aws-cfn-bootstrap-latest --strip-components 1
  python2 -m easy_install aws-cfn-bootstrap-latest
fi

# prepare the instance and run Docker container
cfn-init \
  --stack ${AWS::StackName} \
  --region ${AWS::Region} \
  --resource InstanceLaunchTemplate \
  -c init \
  -v

# send signal that the Docker container is ready or failed
cfn-signal \
  -e $? \
  --stack ${AWS::StackName} \
  --region ${AWS::Region} \
  --resource DockerReadyWaitCondition
