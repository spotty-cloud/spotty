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

STACK_CREATED=$?

# uplooad cfn-init logs to the bucket
if [ $STACK_CREATED -ne 0 ]; then
  STACK_ID=${AWS::StackId}
  STACK_UUID=${!STACK_ID##*/}

  aws s3 cp /var/log/cfn-init-cmd.log ${LogsS3Path}/$STACK_UUID/cfn-init-cmd.log
fi

# send signal that the Docker container is ready or failed
cfn-signal \
  -e $STACK_CREATED \
  --stack ${AWS::StackName} \
  --region ${AWS::Region} \
  --resource DockerReadyWaitCondition
