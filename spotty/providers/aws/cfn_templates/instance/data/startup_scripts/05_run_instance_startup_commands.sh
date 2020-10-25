#!/bin/bash -xe

cfn-signal -e 0 --stack ${AWS::StackName} --region ${AWS::Region} --resource RunningInstanceStartupCommandsSignal

/bin/bash -xe {{INSTANCE_STARTUP_SCRIPTS_DIR}}/instance_startup_commands.sh
