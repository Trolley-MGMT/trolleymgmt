from dataclasses import asdict
import logging
from web.mongo_handler.mongo_utils import insert_cache_object
from web.mongo_handler.mongo_objects import AWSCacheObject
from web.variables.variables import EKS

import boto3

ec2 = boto3.client('ec2')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('aws_caching_script.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def fetch_regions() -> list:
    logger.info(f'A request to fetch regions has arrived')
    response = ec2.describe_regions()
    regions_list = []
    for region_response in response['Regions']:
        regions_list.append(region_response['RegionName'])
    return regions_list


def fetch_zones() -> list:
    logger.info(f'A request to fetch zones has arrived')
    aws_regions = ec2.describe_regions()
    zones_list = []
    for region in aws_regions['Regions']:
        my_region_name = region['RegionName']
        ec2_region = boto3.client('ec2', region_name=my_region_name)
        my_region = [{'Name': 'region-name', 'Values': [my_region_name]}]
        aws_azs = ec2_region.describe_availability_zones(Filters=my_region)
        for az in aws_azs['AvailabilityZones']:
            zone = az['ZoneName']
            zones_list.append(zone)
    return zones_list


def fetch_subnets(zones_list: list) -> dict:
    subnets_dict = {}
    for zone_name in zones_list:
        response = ec2.describe_subnets(
            Filters=[
                {
                    'Name': 'availability-zone',
                    'Values': [
                        zone_name,
                    ]
                },
            ]
        )
        subnets_list = []
        for subnet in response['Subnets']:
            subnets_list.append(subnet['SubnetId'])
        subnets_dict[zone_name] = subnets_list
    return subnets_dict


def main():
    # add kubernetes versions
    regions_list = fetch_regions()
    zones_list = fetch_zones()
    regions_zones_dict = {}
    for region in regions_list:
        for zone in zones_list:
            if region in zone:
                if region in regions_zones_dict.keys():
                    regions_zones_dict[region].insert(0, zone)
                else:
                    regions_zones_dict[region] = [zone]
    subnets_dict = fetch_subnets(zones_list)
    aws_caching_object = AWSCacheObject(
        zones_list=zones_list,
        regions_list=regions_list,
        subnets_dict=subnets_dict,
        regions_zones_dict=regions_zones_dict
    )
    insert_cache_object(caching_object=asdict(aws_caching_object), provider=EKS)


if __name__ == '__main__':
    main()
