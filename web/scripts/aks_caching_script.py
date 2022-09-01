import json
from dataclasses import asdict
import logging
from subprocess import PIPE, run

from flask import jsonify

from web.mongo_handler.mongo_utils import insert_cache_object
from web.mongo_handler.mongo_objects import AKSCacheObject
from web.variables.variables import AKS

# from azure.servicemanagement import *

AKS_LOCATIONS_COMMAND = 'az account list-locations'

# subscription_id = ''
# certificate_path = 'mycert.pem'
# sms = ServiceManagementService(subscription_id, certificate_path)

# result = sms.list_locations()
# for location in result:
#     print(location.name)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('eks_caching_script.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def fetch_locations():
    logger.info(f'A request to fetch regions has arrived')
    command = AKS_LOCATIONS_COMMAND
    logger.info(f'Running a {command} command')
    print(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    regions_list_response = json.loads(result.stdout)
    regions_list = []
    for region in regions_list_response:
        regions_list.append(region['displayName'])
    print(f'regions_list is: {regions_list}')
    return regions_list


def main():
    locations_list = fetch_locations()
    aks_caching_object = AKSCacheObject(
        locations_list=locations_list
    )
    insert_cache_object(caching_object=asdict(aks_caching_object), provider=AKS)


if __name__ == '__main__':
    main()
