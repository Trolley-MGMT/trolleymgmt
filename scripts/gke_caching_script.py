import configparser
import logging
import os
import platform
import json
from dataclasses import asdict
from subprocess import PIPE, run

from mongo_handler.mongo_utils import insert_gke_cache
from mongo_handler.mongo_objects import GKECacheObject

CUR_DIR = os.getcwd()
PROJECT_ROOT = "/".join(CUR_DIR.split('/')[:-1])
config = configparser.ConfigParser()
config.read(f'{CUR_DIR}/config.ini')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('Caching.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

if 'Darwin' in platform.system():
    HELM_COMMAND = '/opt/homebrew/bin/helm'
    GKE_VERSIONS_COMMAND = 'gcloud container get-server-config --zone='
    GKE_ZONES_COMMAND = 'gcloud compute zones list --format json'
    GKE_REGIONS_COMMAND = 'gcloud compute regions list --format json'

else:
    HELM_COMMAND = 'helm'
    GKE_VERSIONS_COMMAND = 'gcloud container get-server-config --zone='
    GKE_ZONES_COMMAND = 'gcloud compute zones list --format json'
    GKE_REGIONS_COMMAND = 'gcloud compute regions list --format json'


def fetch_zones():
    logger.info(f'A request to fetch zones has arrived')
    command = GKE_ZONES_COMMAND
    logger.info(f'Running a {command} command')
    print(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    zones_list = []
    full_zones_list = json.loads(result.stdout)
    for zone in full_zones_list:
        zone_name = zone['name']
        # region_name = zone['region'].split('/')[-1]
        zones_list.append(zone_name)
    return zones_list


def fetch_regions():
    logger.info(f'A request to fetch zones has arrived')
    command = GKE_REGIONS_COMMAND
    logger.info(f'Running a {command} command')
    print(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    regions_list = []
    regions = json.loads(result.stdout)
    for region in regions:
        region_name = region['name']
        regions_list.append(region_name)
    return regions_list


def fetch_versions(zones_list):
    for zone in zones_list:
        command = f'{GKE_VERSIONS_COMMAND}{zone} --format json'
    logger.info(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    gke_versions = json.loads(result.stdout)
    stable_gke_versions = gke_versions['channels'][2]['validVersions']
    return stable_gke_versions


def fetch_gke_image_types(zones_list):
    for zone in zones_list:
        command = f'{GKE_VERSIONS_COMMAND}{zone} --format json'
    logger.info(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    result_jsond = json.loads(result.stdout)
    image_types = result_jsond['validImageTypes']
    available_images = []
    for image in image_types:
        if 'WINDOWS' not in image:  # There's a technical issue at the moment supporting Windows based nodes
            available_images.append(image)
    return available_images


def fetch_helm_installs():
    logger.info(f'A request to fetch helm installs')
    helm_installs_list = []
    command = HELM_COMMAND + ' search repo stable -o json'
    logger.info(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    installs = json.loads(result.stdout)
    for install in installs:
        helm_installs_list.append(install['name'])
    return helm_installs_list


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


def main():
    zones_list = fetch_zones()
    regions_list = fetch_regions()
    helm_installs_list = fetch_helm_installs()
    gke_image_types = fetch_gke_image_types(zones_list=zones_list)
    versions_list = fetch_versions(zones_list=zones_list)
    zones_regions_dict = create_regions_and_zones_dict(regions_list=regions_list, zones_list=zones_list)
    print(regions_list)
    print(helm_installs_list)
    print(versions_list)
    print(gke_image_types)
    print(zones_regions_dict)

    gke_caching_object = GKECacheObject(
        zones_list=zones_list,
        versions_list=versions_list,
        regions_list=regions_list,
        gke_image_types=gke_image_types,
        helm_installs_list=helm_installs_list,
        regions_zones_dict=zones_regions_dict)
    insert_gke_cache(gke_caching_object=asdict(gke_caching_object))


if __name__ == '__main__':
    main()
