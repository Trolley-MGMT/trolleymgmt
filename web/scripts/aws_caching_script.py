import os
import platform
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from dataclasses import asdict
import logging

import getpass as gt

DOCKER_ENV = os.getenv('DOCKER_ENV', False)

log_file_name = 'server.log'
if DOCKER_ENV:
    log_file_path = f'{os.getcwd()}/web/{log_file_name}'
else:
    log_file_path = f'{os.getcwd()}/{log_file_name}'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(log_file_path)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info(f'App runs in the DOCKER_ENV: {DOCKER_ENV}')

if DOCKER_ENV:
    from mongo_handler.mongo_utils import insert_cache_object
    from mongo_handler.mongo_objects import AWSCacheObject, AWSMachineTypeObject, AWSMachinesCacheObject, \
        AWSRegionsAndMachineSeriesObject, AWSSeriesAndMachineTypesObject
    from variables.variables import EKS
else:
    from web.mongo_handler.mongo_utils import insert_cache_object
    from web.mongo_handler.mongo_objects import AWSCacheObject, AWSMachineTypeObject, AWSMachinesCacheObject, \
        AWSRegionsAndMachineSeriesObject, AWSSeriesAndMachineTypesObject
    from web.variables.variables import EKS

import boto3

try:
    ec2 = boto3.client('ec2')
except Exception as e:
    logger.error(f'Trouble connecting to AWS: {e}')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LOCAL_USER = gt.getuser()

if 'Darwin' in platform.system():
    CREDENTIALS_PATH = f'/Users/{LOCAL_USER}/.aws/credentials'
    FETCHED_CREDENTIALS_DIR_PATH = f'/Users/{LOCAL_USER}/.aws/fetched_credentials'
    FETCHED_CREDENTIALS_FILE_PATH = f'{FETCHED_CREDENTIALS_DIR_PATH}/credentials'
else:
    AWS_CREDENTIALS_DEFAULT_DIRECTORY = "home/app/.aws"
    CREDENTIALS_PATH = f'/{AWS_CREDENTIALS_DEFAULT_DIRECTORY}/credentials'
    FETCHED_CREDENTIALS_DIR_PATH = f'/app/.aws'
    FETCHED_CREDENTIALS_FILE_PATH = f'{FETCHED_CREDENTIALS_DIR_PATH}/credentials'


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


def fetch_machine_types_per_region(regions_list: list) -> dict:
    machines_for_zone_dict = {}
    for region in regions_list:
        machine_types_list = []
        machine_types_list_ = []
        ec2 = boto3.client('ec2', region_name=region)
        machine_types_response = ec2.describe_instance_type_offerings(
            LocationType='availability-zone'
        )
        for instance_response in machine_types_response['InstanceTypeOfferings']:
            machine_types_list_.append(instance_response['InstanceType'])
        for machine in machine_types_list_:
            print(f'Adding a machine number: {len(machine_types_list)} out of {len(machine_types_list_)} in {region} region')
            try:
                machine_type_response = ec2.describe_instance_types(
                    InstanceTypes=[
                        machine
                    ]
                )
            except:
                pass
            machine_type_object = AWSMachineTypeObject(region=region,
                                                       machine_type=machine,
                                                       machine_series=machine.split('.')[0],
                                                       vCPU=machine_type_response['InstanceTypes'][0]['VCpuInfo'][
                                                           'DefaultVCpus'],
                                                       memory=machine_type_response['InstanceTypes'][0]['MemoryInfo'][
                                                           'SizeInMiB'])
            machine_types_list.append(machine_type_object)
        machines_for_zone_dict[region] = machine_types_list
    return machines_for_zone_dict


def main(aws_access_key_id, aws_secret_access_key):
    if aws_access_key_id and aws_secret_access_key:
        if not os.path.exists(FETCHED_CREDENTIALS_DIR_PATH):
            os.makedirs(FETCHED_CREDENTIALS_DIR_PATH)
        f = open(FETCHED_CREDENTIALS_FILE_PATH, 'a')
        f.write(
            f'[default]\naws_access_key_id = {aws_access_key_id}\naws_secret_access_key = {aws_secret_access_key}\n')
        f.close()
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = FETCHED_CREDENTIALS_FILE_PATH
    else:
        sys.exit(0)
    # add kubernetes versions
    try:
        logger.info('printing all env variables')
        logger.info(os.environ)
        logger.info('Attempting to fetch regions_list')
        regions_list = fetch_regions()
        logger.info('Attempting to fetch_machine_types')
        # All machine types for all regions
        # regions_list = ['ap-south-1', 'eu-north-1']
        machine_types_all_regions = fetch_machine_types_per_region(regions_list=regions_list)
        for region in machine_types_all_regions:
            aws_machines_caching_object = AWSMachinesCacheObject(
                region=region,
                machines_list=machine_types_all_regions[region]
            )
            insert_cache_object(caching_object=asdict(aws_machines_caching_object), provider=EKS, machine_types=True)

        logger.info('Attempt to fetch zones_list')
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
        logger.info('Attempting to fetch subnets_dict')
        aws_caching_object = AWSCacheObject(
            zones_list=zones_list,
            regions_list=regions_list,
            subnets_dict=subnets_dict,
            regions_zones_dict=regions_zones_dict
        )
        logger.info('Attempting to insert an EKS cache_object')
        insert_cache_object(caching_object=asdict(aws_caching_object), provider=EKS)

        # Inserting AWS Regions and Machine Series Object
        series_list = []
        for region in machine_types_all_regions:
            for machine_type in machine_types_all_regions[region]:
                if not machine_type.machine_series in series_list:
                    series_list.append(machine_type.machine_series)

            aws_regions_and_machine_series_object = AWSRegionsAndMachineSeriesObject(
                region=region,
                series_list=series_list
            )
            insert_cache_object(caching_object=asdict(aws_regions_and_machine_series_object), provider=EKS,
                                aws_regions_and_series=True)

        # Inserting a AWS Machine Series and Machine Types Object
        machines_series_list = []
        for region in machine_types_all_regions:
            for machine_type in machine_types_all_regions[region]:
                if machine_type.machine_series not in machines_series_list:
                    machines_series_list.append(machine_type.machine_series)

        series_and_machine_types_dict = {}
        for region in machine_types_all_regions:
            for machine_series in machines_series_list:
                for machine_type in machine_types_all_regions[region]:
                    if machine_series not in series_and_machine_types_dict.keys():
                        if machine_type.machine_series == machine_series:
                            series_and_machine_types_dict[machine_series] = [machine_type.machine_type]
                    else:
                        if machine_type.machine_series == machine_series:
                            if machine_type.machine_type not in series_and_machine_types_dict[machine_series]:
                                series_and_machine_types_dict[machine_series].append(machine_type.machine_type)
        for machine_series in series_and_machine_types_dict:
            aws_series_and_machine_types_object = AWSSeriesAndMachineTypesObject(
                machine_series=machine_series,
                machines_list=series_and_machine_types_dict[machine_series]
            )
            insert_cache_object(caching_object=asdict(aws_series_and_machine_types_object), provider=EKS,
                                aws_series_and_machine_types=True)
    except Exception as e:
        logger.info(f'Trouble connecting to AWS {e}')


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--aws-access-key-id', type=str, help='AWS Access Key ID')
    parser.add_argument('--aws-secret-access-key', type=str, help='AWS Secret Access Key')
    args = parser.parse_args()
    main(args.aws_access_key_id, args.aws_secret_access_key)
