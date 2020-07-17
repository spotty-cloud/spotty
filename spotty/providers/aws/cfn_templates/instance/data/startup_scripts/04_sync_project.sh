#!/bin/bash -xe

cfn-signal -e 0 --stack ${AWS::StackName} --region ${AWS::Region} --resource SyncingProjectSignal

# create a project directory
if [ -n "${HostProjectDirectory}" ]; then
  mkdir -pm 777 ${HostProjectDirectory}
fi

# sync project files from S3 bucket to the instance
{{{SYNC_PROJECT_CMD}}}
