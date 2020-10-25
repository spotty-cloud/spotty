#!/bin/bash -xe

cfn-signal -e 0 --stack ${AWS::StackName} --region ${AWS::Region} --resource SyncingProjectSignal

# create a project directory
if [ -n "${HostProjectDirectory}" ]; then
  mkdir -p 777 ${HostProjectDirectory}
  chmod 777 ${HostProjectDirectory}

  if [ -d '${HostProjectDirectory}/lost+found' ]; then
    chmod 777 '${HostProjectDirectory}/lost+found'
  fi
fi

# sync project files from S3 bucket to the instance
{{{SYNC_PROJECT_CMD}}}
