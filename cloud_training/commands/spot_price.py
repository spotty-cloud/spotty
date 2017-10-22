from cloud_training.aws import Aws
from cloud_training.abstract_command import AbstractCommand


class SpotPriceCommand(AbstractCommand):

    def run(self):
        regions = ['us-east-2', 'us-east-1', 'us-west-1', 'us-west-2', 'ap-south-1', 'ap-northeast-2', 'ap-southeast-1',
                   'ap-southeast-2', 'ap-northeast-1', 'ca-central-1', 'eu-central-1', 'eu-west-1', 'eu-west-2',
                   'sa-east-1']

        if not self._args.all:
            regions = [self._region]

        prices = {}
        for region in regions:
            res = Aws(region).spot_price('p2.xlarge')
            if res and res['SpotPriceHistory']:
                prices[region] = {}
                for zone in res['SpotPriceHistory']:
                    prices[region][zone['AvailabilityZone']] = zone['SpotPrice']

                print(prices[region])
