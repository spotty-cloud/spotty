#!/bin/bash

cd ~

# mount the volume
mkfs -t ext4 /dev/xvdba
mkdir -p /data
mount /dev/xvdba /data
chown -R ubuntu:ubuntu /data

# configure awscli
aws configure --profile cloud_training set aws_access_key_id {{aws_access_key_id}}
aws configure --profile cloud_training set aws_secret_access_key {{aws_secret_access_key}}
aws configure --profile cloud_training set region {{aws_region}}

# sync the project
aws --profile cloud_training s3 sync "{{s3_project_dir}}" "/data/{{project_name}}" --exclude "*" --include "{{package_name}}/*" --include "data/*.zip" --include "training/{{model}}/{{session_id}}/*"

# unzip files in the data directory
echo {{unzip_script_base64}} | base64 --decode > unzip.py
python unzip.py /data/{{project_name}}/data

# add the cron which will track new checkpoints and logs
echo '/usr/local/bin/aws --profile cloud_training s3 sync "/data/{{project_name}}/training/{{model_name}}" "{{s3_project_dir}}/training/{{model_name}}"' > sync.sh
chmod +x sync.sh
(crontab -l ; echo "* * * * * ~/sync.sh >> ~/sync.log 2>&1") | crontab - > /dev/null

# todo: temporary solution
source /home/ubuntu/.bashrc

# activate Conda environment
if [ '{{conda_env}}' != '' ]
then
    export PATH="/home/ubuntu/.conda/envs/{{conda_env}}/bin:$PATH"
fi

# start tensorboard
nohup tensorboard --logdir /data/{{project_name}}/training/{{model_name}} > tensorboard.log 2>&1 &

# start training
PYTHONPATH=/data/{{project_name}} nohup python /data/{{project_name}}/{{package_name}}/models/{{model_name}}/train.py --session {{session_id}} > train.log 2>&1 &
