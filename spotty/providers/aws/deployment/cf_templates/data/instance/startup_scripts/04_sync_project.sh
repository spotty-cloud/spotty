#!/bin/bash -xe

cfn-signal -e 0 --stack ${AWS::StackName} --region ${AWS::Region} --resource SyncingProjectSignal

aws s3 sync ${ProjectS3Path} ${HostProjectDirectory} ${SyncCommandArgs}
