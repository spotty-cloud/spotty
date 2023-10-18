from argparse import ArgumentParser, Namespace
import boto3
from spotty.commands.abstract_command import AbstractCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.helpers.instance_prices import get_spot_prices
from tabulate import tabulate

class SpotPricesCommand(AbstractCommand):

    name = 'spot-prices'
    description = 'Get Spot Instance prices for an instance type across all AWS regions or within a specific region.'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-i', '--instance-type', type=str, required=True, nargs='+', help='Instance types')
        parser.add_argument('-r', '--region', type=str, help='AWS region')


    def run(self, args: Namespace, output: AbstractOutputWriter):
        # get all regions
        if not args.region:
            ec2 = boto3.client('ec2')
            res = ec2.describe_regions()
            regions = [row['RegionName'] for row in res['Regions']]
        else:
            regions = [args.region]

        instance_types = args.instance_type

        for instance_type in instance_types:
            output.write('Getting spot instance prices for "%s"...\n' % instance_type)

            prices = []
            for region in regions:
                ec2 = boto3.client('ec2', region_name=region)
                res = get_spot_prices(ec2, instance_type)
                prices += [(price, zone) for zone, price in res.items()]

            # sort availability zones by price
            prices.sort(key=lambda x: x[0])

            if prices:
                table_data = [['Price', 'Zone']]
                for price, zone in prices:
                    table_data.append(['%.04f' % price, zone])

                # Format the table
                table = tabulate(table_data, headers="firstrow", tablefmt="pretty")
                output.write(table)
            else:
                output.write('Spot instances of type "%s" are not available for any region.' % instance_type)
