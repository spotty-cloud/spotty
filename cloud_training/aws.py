import base64
import datetime
import json
import logging
import subprocess
from tempfile import NamedTemporaryFile
from cloud_training import utils


class Aws(object):
    def __init__(self, region):
        self._region = region

    def run(self, args: list, json_format=True):
        command_args = ['aws', '--region', self._region] + args
        if json_format:
            command_args += ['--output', 'json']

        logging.debug('AWS command: ' + subprocess.list2cmdline(command_args))

        res = subprocess.run(command_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = res.stdout.decode('utf-8')

        logging.debug('AWS command output: ' + output)

        if res.returncode:
            logging.error('AWS command error: ' + output)
            return None

        if json_format:
            output = json.loads(output)

        return output

    def s3_sync(self, from_path: str, to_path: str, exclusions=None, inclusions=None) -> str:
        args = ['s3', 'sync', from_path, to_path]

        if exclusions:
            for path in exclusions:
                args += ['--exclude', path]

        if inclusions:
            for path in inclusions:
                args += ['--include', path]

        return self.run(args, False)

    def spot_price(self, instance_type: str) -> dict:
        tomorrow_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        args = ['ec2', 'describe-spot-price-history', '--instance-types', instance_type, '--start-time', tomorrow_date,
                '--filters', 'Name=product-description,Values="Linux/UNIX"']

        res = self.run(args)

        prices = {}
        if res and res['SpotPriceHistory']:
            for zone in res['SpotPriceHistory']:
                prices[zone['AvailabilityZone']] = zone['SpotPrice']

        return prices

    def create_spot_request(self, instance_type: str, image_id: str, root_snapshot_id: str, root_vol_size: int,
                            training_vol_size: int, user_data: str, key_name: str, spot_price: float):
        # read the default config
        with open(utils.data_dir('launch-specification.json')) as f:
            config = json.load(f)

        # update some parameters
        config['InstanceType'] = instance_type
        config['ImageId'] = image_id
        config['KeyName'] = key_name
        config['UserData'] = base64.b64encode(user_data.encode()).decode()
        config['BlockDeviceMappings'][0]['Ebs']['SnapshotId'] = root_snapshot_id
        config['BlockDeviceMappings'][0]['Ebs']['VolumeSize'] = root_vol_size
        config['BlockDeviceMappings'][1]['Ebs']['VolumeSize'] = training_vol_size

        # same new config to temporary file
        tmp_file = NamedTemporaryFile(mode='w', delete=False)
        json.dump(config, tmp_file)
        tmp_file.close()

        # run a spot instance
        args = ['ec2', 'request-spot-instances', '--spot-price', ('%.3f' % spot_price), '--type', 'one-time',
                '--launch-specification', 'file://' + tmp_file.name]
        res = self.run(args)

        if not res or not res['SpotInstanceRequests']:
            return None

        # remove the temporary file
        # os.unlink(tmp_file.name)

        return res['SpotInstanceRequests'][0]

    def get_spot_request(self, request_id):
        args = ['ec2', 'describe-spot-instance-requests', '--spot-instance-request-ids', request_id]
        res = self.run(args)
        if not res or not res['SpotInstanceRequests']:
            return None

        return res['SpotInstanceRequests'][0]

    def get_instance_by_id(self, instance_id):
        args = ['ec2', 'describe-instances', '--instance-ids', instance_id]

        res = self.run(args)
        if not res or not res['Reservations']:
            return None

        return res['Reservations'][0]['Instances'][0]

    def get_instances_by_tag(self, tag, value):
        args = ['ec2', 'describe-instances', '--filters', 'Name=tag:%s,Values=%s' % (tag, value), '--filters',
                'Name=instance-state-name,Values=running']

        res = self.run(args)
        if not res or not res['Reservations']:
            return None

        instances = []
        for reservation in res['Reservations']:
            instances += reservation['Instances']

        return instances

    def terminate_instances(self, instances_ids):
        args = ['ec2', 'terminate-instances', '--instance-ids', *instances_ids]

        res = self.run(args)
        if not res or not res['TerminatingInstances']:
            return False

        for instance in res['TerminatingInstances']:
            if instance['CurrentState']['Name'] != 'shutting-down':
                return False

        if len(instances_ids) != len(res['TerminatingInstances']):
            return False

        return True

    def create_tag(self, resources_ids: list, tag: str, value: str):
        args = ['ec2', 'create-tags', '--resources', *resources_ids, '--tags', 'Key=%s,Value=%s' % (tag, value)]
        return self.run(args, False)
