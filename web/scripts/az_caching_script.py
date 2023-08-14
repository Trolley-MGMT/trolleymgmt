import json
import os
from dataclasses import asdict
import logging
from subprocess import PIPE, run

import requests

INFRACOST_TOKEN = os.getenv('INFRACOST_TOKEN', False)
INFRACOST_URL = os.getenv('INFRACOST_URL', 'http://localhost:4000')

POSTGRES_DBNAME = os.getenv('POSTGRES_DBNAME', 'cloud_pricing')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', 5432)

from web.postgresql_handler.postgresql_utils import Postgresql
from web.mongo_handler.mongo_utils import insert_cache_object
from web.mongo_handler.mongo_objects import AZMachineTypeObject, \
    AZMachinesCacheObject, AZResourceGroupObject, AZLocationsCacheObject, AKSKubernetesVersionsCacheObject, \
    AZSeriesAndMachineTypesObject, AZZonesAndMachineSeriesObject
from web.variables.variables import AKS, AZ

AZ_LOCATIONS_COMMAND = 'az account list-locations'
AZ_RESOURCE_GROUPS_COMMAND = 'az group list --query'
AZ_VM_SIZES_COMMAND = 'az vm list-sizes -l'
AKS_KUBERNETES_VERSIONS_COMMAND = 'az aks get-versions -l'
CURRENTLY_ALLOWED_LOCATIONS = 'australiacentral,australiacentral2,australiaeast,australiasoutheast,brazilsouth,' \
                              'brazilsoutheast,canadacentral,canadaeast,centralindia,centralus,eastasia,eastus,' \
                              'eastus2,francecentral,francesouth,germanynorth,germanywestcentral,japaneast,japanwest,' \
                              'jioindiacentral,jioindiawest,koreacentral,koreasouth,northcentralus,northeurope,' \
                              'norwayeast,norwaywest,qatarcentral,southafricanorth,southcentralus,southeastasia,' \
                              'southindia,swedencentral,switzerlandnorth,switzerlandwest,uaecentral,uaenorth,uksouth,' \
                              'ukwest,westcentralus,westeurope,westus,westus2,westus3'
CURRENTLY_ALLOWED_LOCATIONS_LIST = CURRENTLY_ALLOWED_LOCATIONS.split(',')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('trolley_server.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def fetch_pricing_for_az_vm(machine_type: str, region: str) -> float:
    # logger.info(f'machine_type is: {machine_type}')
    url = f'{INFRACOST_URL}/graphql'
    headers = {
        'X-Api-Key': f'{INFRACOST_TOKEN}',
        'Content-Type': 'application/json'
    }

    query = '''
        query ($region: String!, $machineType: String!) {
          products(
            filter: {
              vendorName: "azure",
              service: "Virtual Machines",
              productFamily: "Compute",
              region: $region,
              attributeFilters: [
                { key: "armSkuName", value: $machineType }
              ]
            },
          ) {
            prices(
              filter: {
                purchaseOption: "Consumption",
                unit: "1 Hour"
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
        if len(response.json()['data']['products']) > 0:
            logger.info(response.json()['data']['products'])
            price_points = []
            for item in response.json()['data']['products']:
                if len(item['prices']) > 0:
                    price_points.append(item)
            prices = [float(item['prices'][0]['USD']) for item in price_points]
            return max(prices)
    except Exception as e:
        logger.error(
            f'There was a problem fetching the unit price for in region: {region} with machine_type: {machine_type}'
            f' with error: {e}')
        return 0


def fetch_locations() -> dict:
    logger.info(f'A request to fetch regions has arrived')
    logger.info(f'Running a {AZ_LOCATIONS_COMMAND} command')
    result = run(AZ_LOCATIONS_COMMAND, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    regions_list_response = json.loads(result.stdout)
    regions_dict = {}
    for region in regions_list_response:
        if region['name'] in CURRENTLY_ALLOWED_LOCATIONS_LIST:
            regions_dict[region['displayName']] = region['name']
    return regions_dict


def fetch_resource_groups() -> dict:
    logger.info(f'A request to fetch resource groups has arrived')
    resource_groups_dict = {}
    for location_name in CURRENTLY_ALLOWED_LOCATIONS_LIST:
        command = f'{AZ_RESOURCE_GROUPS_COMMAND} \"[?location==\'{location_name}\']\"'
        logger.info(f'Running a {command} command')
        result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
        resource_groups_response = json.loads(result.stdout)
        if resource_groups_response:
            resource_groups_per_location_list = []
            for resource_group in resource_groups_response:
                resource_groups_per_location_list.append(resource_group['name'])
                resource_groups_dict[location_name] = resource_groups_per_location_list
    return resource_groups_dict


def fetch_machine_types_per_location() -> dict:
    machines_for_zone_dict = {}
    for location_name in CURRENTLY_ALLOWED_LOCATIONS_LIST:
        machine_types_list = []
        command = f'{AZ_VM_SIZES_COMMAND} {location_name}'
        logger.info(f'Running a {command} command')
        result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
        if result.returncode == 0:
            machine_types_response = json.loads(result.stdout)
            for machine in machine_types_response:
                if machine['numberOfCores'] >= 2 and machine['memoryInMb'] >= 1024:
                    machine_series = machine['name'].split('_')[1][0]
                    machine_type_object = AZMachineTypeObject(location_name=location_name,
                                                              machine_series=machine_series,
                                                              machine_type=machine['name'],
                                                              vCPU=machine['numberOfCores'],
                                                              memory=machine['memoryInMb'],
                                                              unit_price=0,
                                                              aks_price=0)
                    machine_types_list.append(asdict(machine_type_object))
            machines_for_zone_dict[location_name] = machine_types_list
        else:
            logger.info(f'{location_name} is not enabled')
    return machines_for_zone_dict


def fetch_kubernetes_versions() -> dict:
    logger.info(f'A request to fetch kubernetes versions has arrived')
    kubernetes_versions_dict = {}
    for location_name in CURRENTLY_ALLOWED_LOCATIONS_LIST:
        command = f'{AKS_KUBERNETES_VERSIONS_COMMAND} {location_name}'
        logger.info(f'Running a {command} command')
        result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
        available_kubernetes_versions_response = json.loads(result.stdout)
        if available_kubernetes_versions_response:
            available_kubernetes_versions_list = []
            for kubernetes_version in available_kubernetes_versions_response['values']:
                available_kubernetes_versions_list.append(kubernetes_version['version'])
                kubernetes_versions_dict[location_name] = available_kubernetes_versions_list
    return kubernetes_versions_dict


def main():
    kubernetes_versions_all_locations = fetch_kubernetes_versions()
    for location_name in kubernetes_versions_all_locations:
        aks_kubernetes_versions_caching_object = AKSKubernetesVersionsCacheObject(
            location_name=location_name,
            kubernetes_versions_list=kubernetes_versions_all_locations[location_name]
        )
        insert_cache_object(caching_object=asdict(aks_kubernetes_versions_caching_object), provider=AKS,
                            aks_kubernetes_versions=True)
    machine_types_all_locations = fetch_machine_types_per_location()
    machines_for_zone_dict_clean = {}
    for location in machine_types_all_locations:
        for machine in machine_types_all_locations[location]:
            machine_type = machine['machine_type']
            if POSTGRES_USER:
                postgres_object = Postgresql(postgres_dbname=POSTGRES_DBNAME, postgres_host=POSTGRES_HOST,
                                             postgres_user=POSTGRES_USER, postgres_password=POSTGRES_PASSWORD,
                                             provider_name=AZ, region_name=location)
                aks_price = postgres_object.fetch_kubernetes_pricing()
            else:
                aks_price = 0
            machine['aks_price'] = aks_price
            unit_price = fetch_pricing_for_az_vm(machine_type, location)
            if unit_price != 0:
                machine['unit_price'] = unit_price
                if location not in machines_for_zone_dict_clean.keys():
                    machines_for_zone_dict_clean[location] = [machine]
                else:
                    machines_for_zone_dict_clean[location].insert(0, machine)
        az_machines_caching_object = AZMachinesCacheObject(
            location_name=location,
            machines_list=machines_for_zone_dict_clean[location]
        )
        insert_cache_object(caching_object=asdict(az_machines_caching_object), provider=AKS, machine_types=True)

    # Inserting a AZ Zones and Machine Series Object
    series_list = []
    for location in machine_types_all_locations:
        for machine in machine_types_all_locations[location]:
            if not machine['machine_series'] in series_list:
                series_list.append(machine['machine_series'])

        az_zones_and_machine_series_object = AZZonesAndMachineSeriesObject(
            location_name=location,
            series_list=series_list
        )
        insert_cache_object(caching_object=asdict(az_zones_and_machine_series_object), provider=AKS,
                            az_locations_and_series=True)

    # Inserting a AZ Machine Series and Machine Types Object
    machines_series_list = []
    for location_name in machine_types_all_locations:
        for machine in machine_types_all_locations[location_name]:
            if machine['machine_series'] not in machines_series_list:
                machines_series_list.append(machine['machine_series'])

    series_and_machine_types_dict = {}
    for location_name in machine_types_all_locations:
        for machine_series in machines_series_list:
            for machine in machine_types_all_locations[location_name]:
                if machine_series not in series_and_machine_types_dict.keys():
                    if machine['machine_series'] == machine_series:
                        series_and_machine_types_dict[machine_series] = [machine['machine_series']]
                else:
                    try:
                        if machine['machine_series'] == machine_series:
                            if machine['machine_series'] not in series_and_machine_types_dict[machine_series]:
                                series_and_machine_types_dict[machine_series].append(machine['machine_type'])
                    except Exception as e:
                        logger.error(f'Something went wrong {e}')
    for machine_series in series_and_machine_types_dict:
        az_series_and_machine_types_object = AZSeriesAndMachineTypesObject(
            machine_series=machine_series,
            machines_list=series_and_machine_types_dict[machine_series]
        )
        insert_cache_object(caching_object=asdict(az_series_and_machine_types_object), provider=AKS,
                            az_series_and_machine_types=True)

    resource_groups_dict = fetch_resource_groups()
    for resource_group_location in resource_groups_dict:
        az_resource_groups_object = AZResourceGroupObject(
            location_name=resource_group_location,
            resource_groups_list=resource_groups_dict[resource_group_location]
        )
        insert_cache_object(caching_object=asdict(az_resource_groups_object), provider=AKS, az_resource_groups=True)

    locations_dict = fetch_locations()
    az_locations_cache_object = AZLocationsCacheObject(
        locations_dict=locations_dict
    )
    insert_cache_object(caching_object=asdict(az_locations_cache_object), provider=AKS, az_locations=True)


if __name__ == '__main__':
    main()
