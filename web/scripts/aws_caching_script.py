import concurrent.futures

from datetime import timedelta
import os
import platform
import sys
import time

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from dataclasses import asdict
import logging

import boto3
import getpass as gt

DOCKER_ENV = os.getenv('DOCKER_ENV', False)

log_file_name = 'server.log'
if DOCKER_ENV:
    log_file_path = f'{os.getcwd()}/web/{log_file_name}'
else:
    log_file_path = f'{os.getcwd()}/{log_file_name}'

logger = logging.getLogger(__name__)

file_handler = logging.FileHandler(filename=log_file_path)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers
)

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


def fetch_regions(ec2) -> list:
    logger.info(f'A request to fetch regions has arrived')
    response = ec2.describe_regions()
    regions_list = []
    for region_response in response['Regions']:
        regions_list.append(region_response['RegionName'])
    return regions_list


def fetch_zones(ec2, aws_access_key_id: str = '', aws_secret_access_key: str = '') -> list:
    logger.info(f'A request to fetch zones has arrived')
    aws_regions = ec2.describe_regions()
    zones_list = []
    for region in aws_regions['Regions']:
        my_region_name = region['RegionName']
        logger.info(f'Adding a {my_region_name} region')
        ec2_region = boto3.client('ec2', region_name=my_region_name, aws_access_key_id=aws_access_key_id,
                                  aws_secret_access_key=aws_secret_access_key)
        my_region = [{'Name': 'region-name', 'Values': [my_region_name]}]
        aws_azs = ec2_region.describe_availability_zones(Filters=my_region)
        for az in aws_azs['AvailabilityZones']:
            zone = az['ZoneName']
            logger.info(f'Adding a {zone} zone')
            zones_list.append(zone)
    return zones_list


def fetch_subnets(zones_list: list, ec2) -> dict:
    logger.info(f'A request to fetch subnets has arrived')
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


def fetch_machine_types_per_region(region: str, ec2) -> list:
    logger.info(f'A request to fetch machine_types per region has arrived')
    machine_types_list = []
    machine_types_list_ = []
    machine_types_response = ec2.describe_instance_type_offerings(
        LocationType='availability-zone'
    )
    for instance_response in machine_types_response['InstanceTypeOfferings']:
        machine_types_list_.append(instance_response['InstanceType'])
    for machine in machine_types_list_:
        logger.info(
            f'Adding a machine number: {len(machine_types_list)} out of {len(machine_types_list_)} in {region} region')
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
    return machine_types_list


def main(aws_access_key_id, aws_secret_access_key):
    start_time = time.monotonic()
    logger.info(f'aws_access_key_id is: {aws_access_key_id}')
    logger.info(f'aws_secret_access_key is: {aws_secret_access_key}')
    if aws_access_key_id and aws_secret_access_key:
        if not os.path.exists(FETCHED_CREDENTIALS_DIR_PATH):
            os.makedirs(FETCHED_CREDENTIALS_DIR_PATH)
        if os.path.exists(FETCHED_CREDENTIALS_FILE_PATH):
            os.remove(FETCHED_CREDENTIALS_FILE_PATH)
        f = open(FETCHED_CREDENTIALS_FILE_PATH, 'a')
        f.write(
            f'[default]\naws_access_key_id = {aws_access_key_id}\naws_secret_access_key = {aws_secret_access_key}\n')
        f.close()
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = FETCHED_CREDENTIALS_FILE_PATH
        logger.info(f'Trying to connect to ec2 using {FETCHED_CREDENTIALS_FILE_PATH} credentials')
        try:
            ec2 = boto3.client('ec2', region_name='us-east-1',
                               aws_access_key_id=aws_access_key_id,
                               aws_secret_access_key=aws_secret_access_key)
            logger.info('Success connecting to AWS')
        except Exception as e:
            logger.error(f'Trouble connecting to AWS: {e}')
    else:
        logger.error('AWS Credentials were not passed correctly')
        sys.exit(0)

    # add kubernetes versions
    try:

        logger.info('Attempting to fetch regions_list')
        machine_types_all_regions = []
        machines_for_zone_dict = {}
        # regions_list = ['us-east-1', 'us-east-2']
        regions_list = fetch_regions(ec2)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit the tasks to the executor
            future_results = [executor.submit(fetch_machine_types_per_region, region, ec2) for region in regions_list]
            for future in concurrent.futures.as_completed(future_results):
                try:
                    result = future.result()
                    machines_for_zone_dict[result[0].region] = result
                except Exception as e:
                    logger.error(f"An error occurred: {e}")

        for region in machines_for_zone_dict:
            aws_machines_caching_object = AWSMachinesCacheObject(
                region=region,
                machines_list=machines_for_zone_dict[region]
            )
            insert_cache_object(caching_object=asdict(aws_machines_caching_object), provider=EKS, machine_types=True)

        # Fetching Zones
        logger.info('Attempt to fetch zones_list')
        zones_list = fetch_zones(ec2=ec2, aws_access_key_id=aws_access_key_id,
                                 aws_secret_access_key=aws_secret_access_key)
        regions_zones_dict = {}
        for region in regions_list:
            for zone in zones_list:
                if region in zone:
                    if region in regions_zones_dict.keys():
                        regions_zones_dict[region].insert(0, zone)
                    else:
                        regions_zones_dict[region] = [zone]
        subnets_dict = fetch_subnets(zones_list, ec2=ec2)
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
        for region in machines_for_zone_dict:
            for machine_type in machines_for_zone_dict[region]:
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
        for region in machines_for_zone_dict:
            for machine_type in machines_for_zone_dict[region]:
                if machine_type.machine_series not in machines_series_list:
                    machines_series_list.append(machine_type.machine_series)

        series_and_machine_types_dict = {}
        for region in machines_for_zone_dict:
            for machine_series in machines_series_list:
                for machine_type in machines_for_zone_dict[region]:
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
        end_time = time.monotonic()
        logger.info(timedelta(seconds=end_time - start_time))
    except Exception as e:
        logger.error(f'Trouble connecting to AWS {e}')


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--aws-access-key-id', type=str, help='AWS Access Key ID')
    parser.add_argument('--aws-secret-access-key', type=str, help='AWS Secret Access Key')
    args = parser.parse_args()
    main(args.aws_access_key_id, args.aws_secret_access_key)
