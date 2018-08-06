from argparse import ArgumentParser
import boto3
import datetime
from spotty.commands.abstract import AbstractCommand
from spotty.commands.helpers.resources import is_valid_instance_type
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


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

            tomorrow_date = datetime.datetime.today() + datetime.timedelta(days=1)
            res = ec2.describe_spot_price_history(
                InstanceTypes=[instance_type],
                StartTime=tomorrow_date,
                ProductDescriptions=['Linux/UNIX'])

            for row in res['SpotPriceHistory']:
                prices.append((row['SpotPrice'], row['AvailabilityZone']))

        # sort availability zones by price
        prices.sort(key=lambda x: x[0])

        if prices:
            for price, zone in prices:
                output.write('%s   %s' % (price, zone))
        else:
            output.write('Spot instances of this type are not available.')
