import logging
import os
import platform

from dataclasses import asdict
import getpass as gt

from dotenv import load_dotenv

from web.mongo_handler.mongo_utils import insert_cache_object
from web.mongo_handler.mongo_objects import GKECacheObject, GKEMachineTypeObject, GKEMachinesCacheObject

from google.cloud.compute import ZonesClient
from google.oauth2 import service_account
from googleapiclient import discovery

from web.variables.variables import GKE

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('Caching.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

project_folder = os.path.expanduser(os.getcwd())
load_dotenv(os.path.join(project_folder, '.env'))
logger.info(f'project_folder is: {project_folder}')

LOCAL_USER = gt.getuser()

if 'Darwin' in platform.system():
    CREDENTIALS_PATH = f'/Users/{LOCAL_USER}/.gcp/gcp_credentials.json'
else:
    GCP_CREDENTIALS_DEFAULT_DIRECTORY = "/home/app/.gcp"
    CREDENTIALS_PATH = f'/{GCP_CREDENTIALS_DEFAULT_DIRECTORY}/gcp_credentials.json'

GCP_PROJECT_ID = 'trolley-361905'

credentials = service_account.Credentials.from_service_account_file(
    CREDENTIALS_PATH)
service = discovery.build('container', 'v1', credentials=credentials)


def fetch_zones() -> list:
    logger.info(f'A request to fetch zones has arrived')
    compute_zones_client = ZonesClient(credentials=credentials)
    zones_object = compute_zones_client.list(project=GCP_PROJECT_ID)
    zones_list = []
    for zone in zones_object:
        zones_list.append(zone.name)
    return zones_list


def fetch_regions() -> list:
    logger.info(f'A request to fetch regions has arrived')
    compute_zones_client = ZonesClient(credentials=credentials)
    zones_object = compute_zones_client.list(project=GCP_PROJECT_ID)
    regions_list = []
    for zone_object in zones_object:
        zone_object_url = zone_object.region
        region_name = zone_object_url.split('/')[-1]
        if region_name not in regions_list:
            regions_list.append(region_name)
    return regions_list


def fetch_versions(zones_list):
    for zone in zones_list:
        name = f'projects/{GCP_PROJECT_ID}/locations/{zone}'
        request = service.projects().locations().getServerConfig(name=name)
        response = request.execute()
        available_gke_versions = []
        for stable_gke_version in response['channels'][2]['validVersions']:
            available_gke_versions.append(stable_gke_version)
        return available_gke_versions


def fetch_gke_image_types(zones_list):
    for zone in zones_list:
        name = f'projects/{GCP_PROJECT_ID}/locations/{zone}'
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


def fetch_machine_types(zones_list) -> dict:
    logger.info(f'A request to fetch machine types has arrived')
    service = discovery.build('compute', 'beta', credentials=credentials)
    machine_types_list = []
    machines_for_zone_dict = {}
    for zone in zones_list:
        request = service.machineTypes().list(project=GCP_PROJECT_ID, zone=zone)
        response = request.execute()
        for machine in response['items']:
            machine_type_object = GKEMachineTypeObject(machine_type=machine['name'], vCPU=machine['guestCpus'],
                                                       memory=machine['memoryMb'])
            machine_types_list.append(machine_type_object)
        machines_for_zone_dict[zone] = machine_types_list
    return machines_for_zone_dict

def fetch_vcpus_for_machine_types(machine_types_list, requested_machine_type):
    for machine in machine_types_list:
        if machine.machine_type == requested_machine_type:
            return machine.vCPU


def main():
    zones_list = fetch_zones()
    regions_list = fetch_regions()
    gke_image_types = fetch_gke_image_types(zones_list=zones_list)
    versions_list = fetch_versions(zones_list=zones_list)
    zones_regions_dict = create_regions_and_zones_dict(regions_list=regions_list, zones_list=zones_list)
    machine_types_all_regions = fetch_machine_types(zones_list)
    for machine_types_region in machine_types_all_regions:
        gke_machines_caching_object = GKEMachinesCacheObject(
            region=machine_types_region,
            machines_list=machine_types_all_regions[machine_types_region]
        )
        insert_cache_object(caching_object=asdict(gke_machines_caching_object), provider=GKE, machine_types=True)
    gke_caching_object = GKECacheObject(
        zones_list=zones_list,
        versions_list=versions_list,
        regions_list=regions_list,
        gke_image_types=gke_image_types,
        regions_zones_dict=zones_regions_dict)
    insert_cache_object(caching_object=asdict(gke_caching_object), provider=GKE)



if __name__ == '__main__':
    main()
