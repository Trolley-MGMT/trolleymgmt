import json
from dataclasses import asdict
import logging
from subprocess import PIPE, run


from web.mongo_handler.mongo_utils import insert_cache_object
from web.mongo_handler.mongo_objects import AKSLocationsCacheObject, AKSResourceGroupObject
from web.variables.variables import AKS

AKS_LOCATIONS_COMMAND = 'az account list-locations'
AKS_RESOURCE_GROUPS_COMMAND = 'az group list --query'
CURRENTLY_ALLOWED_LOCATIONS = 'australiacentral,australiacentral2,australiaeast,australiasoutheast,brazilsouth,' \
                              'brazilsoutheast,canadacentral,canadaeast,centralindia,centralus,eastasia,eastus,' \
                              'eastus2,francecentral,francesouth,germanynorth,germanywestcentral,japaneast,japanwest,' \
                              'jioindiacentral,jioindiawest,koreacentral,koreasouth,northcentralus,northeurope,' \
                              'norwayeast,norwaywest,qatarcentral,southafricanorth,southcentralus,southeastasia,' \
                              'southindia,swedencentral,switzerlandnorth,switzerlandwest,uaecentral,uaenorth,uksouth,' \
                              'ukwest,westcentralus,westeurope,westus,westus2,westus3'
CURRENTLY_ALLOWED_LOCATIONS = CURRENTLY_ALLOWED_LOCATIONS.split(',')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('aws_caching_script.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def fetch_locations() -> dict:
    logger.info(f'A request to fetch regions has arrived')
    command = AKS_LOCATIONS_COMMAND
    logger.info(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    regions_list_response = json.loads(result.stdout)
    regions_dict = {}
    for region in regions_list_response:
        if region['name'] in CURRENTLY_ALLOWED_LOCATIONS:
            regions_dict[region['displayName']] = region['name']
    return regions_dict


def fetch_resource_groups() -> dict:
    logger.info(f'A request to fetch resource groups has arrived')
    resource_groups_dict = {}
    for location in CURRENTLY_ALLOWED_LOCATIONS:
        command = f'{AKS_RESOURCE_GROUPS_COMMAND} \"[?location==\'{location}\']\"'
        logger.info(f'Running a {command} command')
        result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
        resource_groups_response = json.loads(result.stdout)
        if resource_groups_response:
            resource_groups_per_location_list = []
            for resource_group in resource_groups_response:
                resource_groups_per_location_list.append(resource_group['name'])
                resource_groups_dict[location] = resource_groups_per_location_list
    return resource_groups_dict

def main():
    resource_groups_dict = fetch_resource_groups()
    for resource_group_location in resource_groups_dict:
        aks_resource_groups_object = AKSResourceGroupObject(
            location=resource_group_location,
            resource_groups_list=resource_groups_dict[resource_group_location]
        )
        insert_cache_object(caching_object=asdict(aks_resource_groups_object), provider=AKS, aks_resource_groups=True)

    locations_dict = fetch_locations()
    aks_locations_cache_object = AKSLocationsCacheObject(
        locations_dict=locations_dict
    )
    insert_cache_object(caching_object=asdict(aks_locations_cache_object), provider=AKS, aks_locations=True)


if __name__ == '__main__':
    main()
