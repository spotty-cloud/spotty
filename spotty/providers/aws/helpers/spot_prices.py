import datetime


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
            raise ValueError('Spot price for the "%s" availability zone not found.')

        current_price = spot_prices[availability_zone]
    else:
        current_price = min(spot_prices.values())

    return current_price
