import concurrent.futures

import getpass as gt
import os
import platform
import sys

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from dataclasses import asdict
import logging

import boto3
import requests

DOCKER_ENV = os.getenv('DOCKER_ENV', False)
GITHUB_ACTIONS_ENV = os.getenv('GITHUB_ACTIONS_ENV')
INFRACOST_TOKEN = os.getenv('INFRACOST_TOKEN', '')
INFRACOST_URL = os.getenv('INFRACOST_URL', 'http://localhost:4000')

POSTGRES_DBNAME = os.getenv('POSTGRES_DBNAME', 'cloud_pricing')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', 5444)

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
    level=logging.INFO,
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers
)

logger.info(f'App runs in the DOCKER_ENV: {DOCKER_ENV}')

if DOCKER_ENV:
    from mongo_handler.mongo_utils import insert_cache_object
    from mongo_handler.mongo_objects import AWSCacheObject, AWSMachineTypeObject, AWSMachinesCacheObject
    from postgresql_handler.postgresql_utils import Postgresql
    from variables.variables import EKS, AWS
else:
    from web.mongo_handler.mongo_utils import insert_cache_object
    from web.mongo_handler.mongo_objects import AWSCacheObject, AWSMachineTypeObject, AWSMachinesCacheObject
    from web.postgresql_handler.postgresql_utils import Postgresql
    from web.variables.variables import EKS, AWS

LOCAL_USER = gt.getuser()

if 'Darwin' in platform.system():
    CREDENTIALS_PATH = f'/Users/{LOCAL_USER}/.aws/credentials'
    FETCHED_CREDENTIALS_DIR_PATH = f'/Users/{LOCAL_USER}/.aws/fetched_credentials'
    FETCHED_CREDENTIALS_FILE_PATH = f'{FETCHED_CREDENTIALS_DIR_PATH}/credentials'
else:
    if GITHUB_ACTIONS_ENV:
        logger.info(f'checking the github_actions_env path')
        FETCHED_CREDENTIALS_DIR_PATH = '/home/runner/work/.aws'
        FETCHED_CREDENTIALS_FILE_PATH = f'{FETCHED_CREDENTIALS_DIR_PATH}/credentials'
    else:
        AWS_CREDENTIALS_DEFAULT_DIRECTORY = "home/app/.aws"
        CREDENTIALS_PATH = f'/{AWS_CREDENTIALS_DEFAULT_DIRECTORY}/credentials'
        FETCHED_CREDENTIALS_DIR_PATH = f'/app/.aws'
        FETCHED_CREDENTIALS_FILE_PATH = f'{FETCHED_CREDENTIALS_DIR_PATH}/credentials'


def fetch_pricing_for_ec2_instance(machine_type: str, region: str) -> float:
    url = f'{INFRACOST_URL}/graphql'
    headers = {
        'X-Api-Key': f'{INFRACOST_TOKEN}',
        'Content-Type': 'application/json'
    }

    query = '''
        query GetProductPrices($vendor: String!, $service: String!, $region: String!, $instanceType: String!, $operatingSystem: String!, $tenancy: String!, $capacityStatus: String!, $preInstalledSw: String!, $purchaseOption: String!) {
          products(filter: {
            vendorName: $vendor,
            service: $service,
            region: $region,
            attributeFilters: [
              {key: "instanceType", value: $instanceType},
              {key: "operatingSystem", value: $operatingSystem},
              {key: "tenancy", value: $tenancy},
              {key: "capacitystatus", value: $capacityStatus},
              {key: "preInstalledSw", value: $preInstalledSw}
            ]
          }) {
            prices(filter: {purchaseOption: $purchaseOption}) {
              USD
            }
          }
        }
    '''

    variables = {
        'vendor': 'aws',
        'service': 'AmazonEC2',
        'region': region,
        'instanceType': machine_type,
        'operatingSystem': 'Linux',
        'tenancy': 'Shared',
        'capacityStatus': 'Used',
        'preInstalledSw': 'NA',
        'purchaseOption': 'on_demand'
    }

    data = {
        'query': query,
        'variables': variables
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        return float(response.json()['data']['products'][0]['prices'][0]['USD'])
    except Exception as e:
        logger.error(
            f'There was a problem fetching the unit price for in region: {region} with machine_type: {machine_type}'
            f' with error: {e}')
        return 0


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


def fetch_machine_types_per_region(region: str, aws_access_key_id: str = '',
                                   aws_secret_access_key: str = '') -> list:
    logger.info(f'A request to fetch machine_types per region has arrived')
    machine_types_list = []
    machine_types_list_ = []
    ec2_client = boto3.client('ec2', region_name=region, aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key)
    machine_types_response = ec2_client.describe_instance_type_offerings()

    for instance_response in machine_types_response['InstanceTypeOfferings']:
        machine_types_list_.append(instance_response['InstanceType'])
    for machine in machine_types_list_:
        logger.info(
            f'Adding a machine number: {len(machine_types_list)} out of {len(machine_types_list_)} in {region} region')
        try:
            machine_type_response = ec2_client.describe_instance_types(
                InstanceTypes=[
                    machine
                ]
            )
        except Exception as e:
            logger.error(f'Error describing a {machine} type instance with error: {e}')

        machine_type_object = AWSMachineTypeObject(region=region,
                                                   machine_type=machine,
                                                   machine_series=machine.split('.')[0],
                                                   vCPU=machine_type_response['InstanceTypes'][0]['VCpuInfo'][
                                                       'DefaultVCpus'],
                                                   memory=machine_type_response['InstanceTypes'][0]['MemoryInfo'][
                                                       'SizeInMiB'],
                                                   unit_price=0,
                                                   eks_price=0)
        machine_types_list.append(asdict(machine_type_object))
    return machine_types_list


def main(aws_access_key_id, aws_secret_access_key):
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
        machines_for_zone_dict = {}
        # regions_list = ['eu-west-2', 'eu-west-3']
        regions_list = fetch_regions(ec2)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit the tasks to the executor
            future_results = [executor.submit(fetch_machine_types_per_region, region, aws_access_key_id,
                                              aws_secret_access_key) for region in regions_list]
            for future in concurrent.futures.as_completed(future_results):
                try:
                    result = future.result()
                    machines_for_zone_dict[result[0]['region']] = result
                except Exception as e:
                    logger.error(f"An error occurred: {e}")

        machines_for_zone_dict_clean = {}
        for region in machines_for_zone_dict:
            for machine in machines_for_zone_dict[region]:
                postgres_object = Postgresql(postgres_dbname=POSTGRES_DBNAME, postgres_host=POSTGRES_HOST,
                                             postgres_user=POSTGRES_USER, postgres_password=POSTGRES_PASSWORD,
                                             provider_name=AWS, region_name=region)
                eks_price = postgres_object.fetch_kubernetes_pricing()
                machine['eks_price'] = eks_price
                if INFRACOST_TOKEN:
                    try:
                        unit_price = fetch_pricing_for_ec2_instance(machine_type=machine['machine_type'],
                                                                    region=machine['region'])
                    except Exception as e:
                        logger.error(f'Something is wrong: {e}')

                else:
                    machines_for_zone_dict_clean = machines_for_zone_dict
                    break
                if unit_price != 0:
                    try:
                        machine['unit_price'] = unit_price
                    except Exception as e:
                        logger.error(f'Something is wrong: {e}')
                    try:
                        if machine['region'] not in machines_for_zone_dict_clean.keys():
                            machines_for_zone_dict_clean[region] = [machine]
                        else:
                            machines_for_zone_dict_clean[region].insert(0, machine)
                    except Exception as e:
                        logger.error(f'Something is wrong: {e}')

            aws_machines_caching_object = AWSMachinesCacheObject(
                region=region,
                machines_list=machines_for_zone_dict_clean[region]
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

    except Exception as e:
        logger.error(f'Trouble connecting to AWS {e}')


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--aws-access-key-id', type=str, help='AWS Access Key ID')
    parser.add_argument('--aws-secret-access-key', type=str, help='AWS Secret Access Key')
    args = parser.parse_args()
    main(args.aws_access_key_id, args.aws_secret_access_key)
