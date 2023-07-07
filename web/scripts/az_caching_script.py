import json
from dataclasses import asdict
import logging
from subprocess import PIPE, run

from web.mongo_handler.mongo_utils import insert_cache_object
from web.mongo_handler.mongo_objects import AZMachineTypeObject, \
    AZMachinesCacheObject, AZResourceGroupObject, AZLocationsCacheObject, AKSKubernetesVersionsCacheObject, \
    AZSeriesAndMachineTypesObject, AZZonesAndMachineSeriesObject
from web.variables.variables import AKS

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

handler = logging.FileHandler('aws_caching_script.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


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
    machine_types_list = []
    machines_for_zone_dict = {}
    for location_name in CURRENTLY_ALLOWED_LOCATIONS_LIST:
        command = f'{AZ_VM_SIZES_COMMAND} {location_name}'
        logger.info(f'Running a {command} command')
        result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
        if result.returncode == 0:
            machine_types_response = json.loads(result.stdout)
            for machine in machine_types_response:
                machine_series = machine['name'].split('_')[1][0]
                machine_type_object = AZMachineTypeObject(location_name=location_name,
                                                          machine_series=machine_series,
                                                          machine_type=machine['name'],
                                                          vCPU=machine['numberOfCores'],
                                                          memory=machine['memoryInMb'])
                machine_types_list.append(machine_type_object)
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
        logger.info(f'result of the command run is: {result.stdout}, {result.stderr}')
        available_kubernetes_versions_response = json.loads(result.stdout)
        if available_kubernetes_versions_response:
            available_kubernetes_versions_list = []
            for kubernetes_version in available_kubernetes_versions_response['orchestrators']:
                available_kubernetes_versions_list.append(kubernetes_version['orchestratorVersion'])
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
    for location_name in machine_types_all_locations:
        az_machines_caching_object = AZMachinesCacheObject(
            location_name=location_name,
            machines_list=machine_types_all_locations[location_name]
        )
        insert_cache_object(caching_object=asdict(az_machines_caching_object), provider=AKS, machine_types=True)

    # Inserting a AZ Zones and Machine Series Object
    series_list = []
    for location_name in machine_types_all_locations:
        for machine_type in machine_types_all_locations[location_name]:
            if not machine_type.machine_series in series_list:
                series_list.append(machine_type.machine_series)

        az_zones_and_machine_series_object = AZZonesAndMachineSeriesObject(
            location_name=location_name,
            series_list=series_list
        )
        insert_cache_object(caching_object=asdict(az_zones_and_machine_series_object), provider=AKS,
                            az_locations_and_series=True)

    # Inserting a AZ Machine Series and Machine Types Object
    machines_series_list = []
    for location_name in machine_types_all_locations:
        for machine_type in machine_types_all_locations[location_name]:
            if machine_type.machine_series not in machines_series_list:
                machines_series_list.append(machine_type.machine_series)

    series_and_machine_types_dict = {}
    for location_name in machine_types_all_locations:
        for machine_series in machines_series_list:
            for machine_type in machine_types_all_locations[location_name]:
                if machine_series not in series_and_machine_types_dict.keys():
                    if machine_type.machine_series == machine_series:
                        series_and_machine_types_dict[machine_series] = [machine_type.machine_type]
                else:
                    if machine_type.machine_series == machine_series:
                        if machine_type.machine_type not in series_and_machine_types_dict[machine_series]:
                            series_and_machine_types_dict[machine_series].append(machine_type.machine_type)
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
