import json
import logging
import os
import platform
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from dataclasses import asdict
import getpass as gt
from dotenv import load_dotenv

from google.cloud.compute import ZonesClient
from google.oauth2 import service_account
from googleapiclient import discovery
import requests

DOCKER_ENV = os.getenv('DOCKER_ENV', False)
GCP_CREDENTIALS = os.getenv('GCP_CREDENTIALS', False)
INFRACOST_URL = os.getenv('INFRACOST_URL', 'http://localhost:4000')
INFRACOST_TOKEN = os.getenv('INFRACOST_TOKEN', False)

POSTGRES_DBNAME = os.getenv('POSTGRES_DBNAME', 'cloud_pricing')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', 5432)

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
    from mongo_handler.mongo_objects import GKECacheObject, GKEMachineTypeObject, GKEMachinesCacheObject, \
        GKEKubernetesVersionsCacheObject
    from postgresql_handler.postgresql_utils import Postgresql
    from variables.variables import GKE, GCP
else:
    from web.mongo_handler.mongo_utils import insert_cache_object
    from web.mongo_handler.mongo_objects import GKECacheObject, GKEMachineTypeObject, GKEMachinesCacheObject, \
        GKEKubernetesVersionsCacheObject
    from web.postgresql_handler.postgresql_utils import Postgresql
    from web.variables.variables import GKE, GCP

project_folder = os.path.expanduser(os.getcwd())
load_dotenv(os.path.join(project_folder, '.env'))

LOCAL_USER = gt.getuser()
GITHUB_ACTIONS_ENV = os.getenv('GITHUB_ACTIONS_ENV')
PLATFORM_SYSTEM = platform.system()
logger.info(f'PLATFORM_SYSTEM is: {PLATFORM_SYSTEM}')

if 'Darwin' in platform.system():
    logger.info(f'platform system is Darwin')
    CREDENTIALS_PATH = f'/Users/{LOCAL_USER}/.gcp/gcp_credentials.json'
    FETCHED_CREDENTIALS_DIR_PATH = f'/Users/{LOCAL_USER}/.gcp/fetched_credentials'
    FETCHED_CREDENTIALS_FILE_PATH = f'{FETCHED_CREDENTIALS_DIR_PATH}/credentials'
else:
    if GITHUB_ACTIONS_ENV:
        logger.info(f'checking the github_actions_env path')
        FETCHED_CREDENTIALS_FILE_PATH = '/home/runner/work/gcp_credentials.json'
        CREDENTIALS_PATH = '/home/runner/work/gcp_credentials.json'
    else:
        logger.info(f'checking the docker_env path')
        GCP_CREDENTIALS_DEFAULT_DIRECTORY = "/home/app/.gcp"
        CREDENTIALS_PATH = f'{GCP_CREDENTIALS_DEFAULT_DIRECTORY}/gcp_credentials.json'
        logger.info(f'CREDENTIALS_PATH is: {CREDENTIALS_PATH}')
        FETCHED_CREDENTIALS_DIR_PATH = f'/app/.gcp'
        FETCHED_CREDENTIALS_FILE_PATH = f'{FETCHED_CREDENTIALS_DIR_PATH}/gcp_credentials.json'


def fetch_pricing_for_gcp_vm(machine_type: str, region: str) -> float:
    url = f'{INFRACOST_URL}/graphql'
    # url = 'https://pricing.api.infracost.io/graphql'
    headers = {
        'X-Api-Key': f'{INFRACOST_TOKEN}',
        'Content-Type': 'application/json'
    }

    query = '''
      query ($region: String!, $machineType: String!) {
        products(
          filter: {
            vendorName: "gcp",
            service: "Compute Engine",
            productFamily: "Compute Instance",
            region: $region,
            attributeFilters: [
              { key: "machineType", value: $machineType }
            ]
          },
        ) {
          prices(
            filter: {
              purchaseOption: "on_demand"
            },
          ) { USD }
        }
      }
    '''

    variables = {
        "region": region,
        "machineType": machine_type
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


def fetch_zones(gcp_project_id: str) -> list:
    logger.info(f'A request to fetch zones has arrived for {gcp_project_id} project_id')
    compute_zones_client = ZonesClient()
    zones_object = compute_zones_client.list(project=gcp_project_id)
    zones_list = []
    for zone in zones_object:
        zones_list.append(zone.name)
    return zones_list


def fetch_regions(gcp_project_id: str) -> list:
    logger.info(f'A request to fetch regions has arrived')
    compute_zones_client = ZonesClient()
    zones_object = compute_zones_client.list(project=gcp_project_id)
    regions_list = []
    for zone_object in zones_object:
        zone_object_url = zone_object.region
        region_name = zone_object_url.split('/')[-1]
        if region_name not in regions_list:
            regions_list.append(region_name)
    return regions_list


def fetch_kubernetes_versions(zones_list: list, gcp_project_id: str, service):
    kubernetes_versions_dict = {}
    for zone in zones_list:
        logger.info(f'Fetching kubernetes versions for {zone} zone')
        name = f'projects/{gcp_project_id}/locations/{zone}'
        request = service.projects().locations().getServerConfig(name=name)
        response = request.execute()
        available_gke_versions = []
        for stable_gke_version in response['channels'][2]['validVersions']:
            available_gke_versions.append(stable_gke_version)
        kubernetes_versions_dict[zone] = available_gke_versions
    return kubernetes_versions_dict


def fetch_gke_image_types(zones_list: list, gcp_project_id: str, service):
    for zone in zones_list:
        name = f'projects/{gcp_project_id}/locations/{zone}'
        request = service.projects().locations().getServerConfig(name=name)
        response = request.execute()
        available_images = []
        for image in response['validImageTypes']:
            if 'WINDOWS' not in image and image != 'COS':  # There's a technical issue at the moment supporting
                # Windows based nodes
                available_images.append(image)
        return available_images


def create_regions_and_zones_dict(regions_list, zones_list):
    zones_regions_dict = {}
    for region in regions_list:
        for zone in zones_list:
            if region in zone:
                if region not in zones_regions_dict.keys():
                    zones_regions_dict[region] = [zone]
                else:
                    zones_regions_dict[region].append(zone)
    return zones_regions_dict


def fetch_machine_types_per_zone(zones_list: list, gcp_project_id: str, credentials) -> dict:
    logger.info(f'A request to fetch machine types has arrived')
    service = discovery.build('compute', 'beta', credentials=credentials)
    machines_for_zone_dict = {}
    # zones_list = ['asia-northeast1-a', 'asia-northeast1-b']
    for zone in zones_list:
        machine_types_list = []
        # logger.info(f'Fetching machine types for {zone} zone')
        request = service.machineTypes().list(project=gcp_project_id, zone=zone)
        response = request.execute()
        for machine in response['items']:
            machine_type_object = GKEMachineTypeObject(zone=zone,
                                                       machine_type=machine['name'],
                                                       machine_series=machine['name'].split('-')[0],
                                                       vCPU=machine['guestCpus'],
                                                       memory=machine['memoryMb'],
                                                       unit_price=0,
                                                       gke_price=0)
            machine_types_list.append(asdict(machine_type_object))
        machines_for_zone_dict[zone] = machine_types_list
    return machines_for_zone_dict


def main(gcp_credentials: str):
    logger.info(f'Starting the caching flow with {gcp_credentials} credentials')
    if gcp_credentials:
        logger.info('gcp_credentials were found')
        if not os.path.exists(FETCHED_CREDENTIALS_DIR_PATH):
            logger.info(f'{FETCHED_CREDENTIALS_DIR_PATH} was not found. Creating a directory')
            os.makedirs(FETCHED_CREDENTIALS_DIR_PATH)
        if os.path.exists(FETCHED_CREDENTIALS_FILE_PATH):
            logger.info(f'{FETCHED_CREDENTIALS_FILE_PATH} exists, removing the file')
            os.remove(FETCHED_CREDENTIALS_FILE_PATH)
        logger.info(f'Opening the {FETCHED_CREDENTIALS_FILE_PATH} file path')
        f = open(FETCHED_CREDENTIALS_FILE_PATH, 'a')
        f.write(gcp_credentials)
        f.close()
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = FETCHED_CREDENTIALS_FILE_PATH
        logger.info(f'FETCHED_CREDENTIALS_FILE_PATH is: {FETCHED_CREDENTIALS_FILE_PATH}')
    else:
        logger.info(f'Setting {CREDENTIALS_PATH} as the credentials_path')
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_PATH
    try:
        try:
            with open(FETCHED_CREDENTIALS_FILE_PATH, "r") as f:
                credentials = f.read()
                gcp_project_id = json.loads(credentials)['project_id']
                logger.info(f'GCP_PROJECT_ID is: {gcp_project_id}')

        except Exception as e:
            logger.error('Problem extracting GCP_PROJECT_ID parameter')
        try:
            credentials = service_account.Credentials.from_service_account_file(
                FETCHED_CREDENTIALS_FILE_PATH)
            service = discovery.build('container', 'v1', credentials=credentials)
        except Exception as e:
            logger.error(f'Credentials were not provided with a file with error: {e}')

        logger.info('Attempting to fetch zones')
        zones_list = fetch_zones(gcp_project_id)
        logger.info('Attempting to fetch regions')
        regions_list = fetch_regions(gcp_project_id)
        logger.info('Attempting to fetch gke_image_types')
        gke_image_types = fetch_gke_image_types(zones_list=zones_list, gcp_project_id=gcp_project_id, service=service)

        logger.info('Attempting to fetch gke_kubernetes_versions_list')
        kubernetes_versions_all_locations = fetch_kubernetes_versions(zones_list=zones_list,
                                                                      gcp_project_id=gcp_project_id, service=service)
        for region_name in kubernetes_versions_all_locations:
            gke_kubernetes_versions_caching_object = GKEKubernetesVersionsCacheObject(
                region_name=region_name,
                kubernetes_versions_list=kubernetes_versions_all_locations[region_name]
            )
            insert_cache_object(caching_object=asdict(gke_kubernetes_versions_caching_object), provider=GKE,
                                gke_kubernetes_versions=True)

        logger.info('Attempting to fetch versions_list')
        zones_regions_dict = create_regions_and_zones_dict(regions_list=regions_list, zones_list=zones_list)
        logger.info('Attempting to fetch machine_types_all_zones')
        machine_types_all_zones = fetch_machine_types_per_zone(zones_list, gcp_project_id=gcp_project_id,
                                                               credentials=credentials)
        machines_for_zone_dict_clean = {}
        for zone in machine_types_all_zones:
            for machine in machine_types_all_zones[zone]:
                machine_type = machine['machine_type']
                region = zone.split('-')[0] + '-' + zone.split('-')[1]
                postgres_object = Postgresql(postgres_dbname=POSTGRES_DBNAME, postgres_host=POSTGRES_HOST,
                                             postgres_user=POSTGRES_USER, postgres_password=POSTGRES_PASSWORD,
                                             provider_name=GCP, region_name=region)
                gke_price = postgres_object.fetch_kubernetes_pricing()
                machine['gke_price'] = gke_price
                if INFRACOST_TOKEN:
                    unit_price = fetch_pricing_for_gcp_vm(machine_type, region)
                else:
                    unit_price = 0
                try:
                    if unit_price != 0:
                        machine['unit_price'] = unit_price
                        if zone not in machines_for_zone_dict_clean.keys():
                            machines_for_zone_dict_clean[zone] = [machine]
                        else:
                            try:
                                machines_for_zone_dict_clean[zone].insert(0, machine)
                            except Exception as e:
                                logger.error(f'Something went wrong: {e}')
                except Exception as e:
                    logger.error(f'Something went wrong: {e}')

        for zone in machine_types_all_zones:
            gke_machines_caching_object = GKEMachinesCacheObject(
                region=zone,
                machines_list=machines_for_zone_dict_clean[zone]
            )
            insert_cache_object(caching_object=asdict(gke_machines_caching_object), provider=GKE, machine_types=True)

        # Inserting a whole GKE Cache Object
        gke_caching_object = GKECacheObject(
            zones_list=zones_list,
            regions_list=regions_list,
            gke_image_types=gke_image_types,
            regions_zones_dict=zones_regions_dict)
        logger.info('Attempting to insert a GKE cache object')
        insert_cache_object(caching_object=asdict(gke_caching_object), provider=GKE, gke_full_cache=True)


    except Exception as e:
        logger.error(f'Trouble connecting to GCP: {e}')


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--credentials', type=str, help='GCP Credentials')
    args = parser.parse_args()
    main(GCP_CREDENTIALS)
    # main(args.credentials)
