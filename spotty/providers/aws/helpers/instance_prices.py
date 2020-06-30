import datetime
import json
import logging
import boto3
from pkg_resources import resource_filename


def get_spot_prices(ec2, instance_type: str):
    """Returns current Spot Instance prices for all availability zones for particular instance type and region.
    AWS region specified implicitly in the "ec2" object.
    """
    tomorrow_date = datetime.datetime.today() + datetime.timedelta(days=1)
    res = ec2.describe_spot_price_history(InstanceTypes=[instance_type],
                                          StartTime=tomorrow_date,
                                          ProductDescriptions=['Linux/UNIX'])

    prices_by_zone = {}
    for row in res['SpotPriceHistory']:
        prices_by_zone[row['AvailabilityZone']] = float(row['SpotPrice'])

    return prices_by_zone


def get_current_spot_price(ec2, instance_type, availability_zone=''):
    """Returns the current Spot price for an availability zone.
    If an availability zone is not specified, returns the minimum price for the region.
    """
    spot_prices = get_spot_prices(ec2, instance_type)
    if availability_zone:
        if availability_zone not in spot_prices:
            raise ValueError('Spot price for the "%s" availability zone not found.' % availability_zone)

        current_price = spot_prices[availability_zone]
    else:
        current_price = min(spot_prices.values())

    return current_price


def get_on_demand_price(instance_type: str, region: str):
    client = boto3.client('pricing', region_name='us-east-1')  # the API available only in "us-east-1"

    try:
        response = client.get_products(
            ServiceCode='AmazonEC2',
            Filters=[
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': _get_region_name(region)},
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'shared'},
                {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'},
            ],
        )

        prices = json.loads(response['PriceList'][0])['terms']['OnDemand']
        price = float(list(list(prices.values())[0]['priceDimensions'].values())[0]['pricePerUnit']['USD'])
    except Exception as e:
        logging.debug('Couldn\'t find a price for the instance: ' + str(e))
        price = None

    return price


def _get_region_name(region: str):
    endpoint_file = resource_filename('botocore', 'data/endpoints.json')
    try:
        with open(endpoint_file, 'r') as f:
            data = json.load(f)
            region_name = data['partitions'][0]['regions'][region]['description']
    except Exception as e:
        logging.debug('Couldn\'t obtain the region name: ' + str(e))
        region_name = None

    return region_name


def check_max_spot_price(ec2, instance_type: str, is_spot_instance: bool, max_price: float,
                         availability_zone: str = ''):
    """Checks that the specified maximum Spot price is less than the
    current Spot price.

    Args:
        ec2: EC2 client
        instance_type (str): Instance Type
        is_spot_instance (bool): True if it's a spot instance
        max_price (float): requested maximum price for the instance
        availability_zone (str): Availability zone to check. If it's an empty string,
            checks the cheapest AZ.

    Raises:
        ValueError: Current price for the instance is higher than the
            maximum price in the configuration file.
    """
    if is_spot_instance and max_price:
        current_price = get_current_spot_price(ec2, instance_type, availability_zone)
        if current_price > max_price:
            raise ValueError('Current price for the instance (%.04f) is higher than the maximum price in the '
                             'configuration file (%.04f).' % (current_price, max_price))
