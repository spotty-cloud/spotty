from argparse import ArgumentParser
import boto3
from spotty.commands.abstract import AbstractCommand
from spotty.helpers.resources import is_valid_instance_type
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.helpers.spot_prices import get_spot_prices


class SpotPricesCommand(AbstractCommand):

    @staticmethod
    def get_name() -> str:
        return 'spot-prices'

    @staticmethod
    def get_description():
        return 'Get spot instance prices for particular instance type across all regions'

    @staticmethod
    def configure(parser: ArgumentParser):
        parser.add_argument('--instance-type', '-i', type=str, required=True, help='Instance type')

    def run(self, output: AbstractOutputWriter):
        # get all regions
        ec2 = boto3.client('ec2')
        res = ec2.describe_regions()
        regions = [row['RegionName'] for row in res['Regions']]

        instance_type = self._args.instance_type
        if not is_valid_instance_type(instance_type):
            raise ValueError('Instance type "%s" doesn\'t exist.' % instance_type)

        output.write('Getting spot instance prices for "%s"...\n' % instance_type)

        prices = []
        for region in regions:
            ec2 = boto3.client('ec2', region_name=region)
            res = get_spot_prices(ec2, instance_type)
            prices += [(price, zone) for zone, price in res.items()]

        # sort availability zones by price
        prices.sort(key=lambda x: x[0])

        if prices:
            output.write('Price  Zone')
            for price, zone in prices:
                output.write('%.04f %s' % (price, zone))
        else:
            output.write('Spot instances of this type are not available.')
