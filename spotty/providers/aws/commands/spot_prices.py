from argparse import ArgumentParser, Namespace
import boto3
from spotty.commands.abstract_command import AbstractCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.helpers.spot_prices import get_spot_prices
from spotty.providers.aws.config.validation import is_valid_instance_type


class SpotPricesCommand(AbstractCommand):

    name = 'spot-prices'
    description = 'Get spot instance prices for particular instance type across all regions'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-i', '--instance-type', type=str, required=True, help='Instance type')
        parser.add_argument('-r', '--region', type=str, help='AWS region')

    def run(self, args: Namespace, output: AbstractOutputWriter):
        # get all regions
        if not args.region:
            ec2 = boto3.client('ec2')
            res = ec2.describe_regions()
            regions = [row['RegionName'] for row in res['Regions']]
        else:
            regions = [args.region]

        instance_type = args.instance_type
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
