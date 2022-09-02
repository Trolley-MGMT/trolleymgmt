import json
from dataclasses import asdict
import logging
from subprocess import PIPE, run


from web.mongo_handler.mongo_utils import insert_cache_object
from web.mongo_handler.mongo_objects import AKSCacheObject
from web.variables.variables import AKS

AKS_LOCATIONS_COMMAND = 'az account list-locations'
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

handler = logging.FileHandler('eks_caching_script.log')
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


def main():
    locations_dict = fetch_locations()
    aks_caching_object = AKSCacheObject(
        locations_dict=locations_dict
    )
    insert_cache_object(caching_object=asdict(aks_caching_object), provider=AKS)


if __name__ == '__main__':
    main()
