import calendar
import getpass as gt
import json
import logging
import os
import platform
import sys
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path
from subprocess import PIPE, run

from cryptography.fernet import Fernet
from hurry.filesize import size

DOCKER_ENV = os.getenv('DOCKER_ENV', False)
KUBERNETES_SERVICE_HOST = os.getenv('KUBERNETES_SERVICE_HOST', '0.0.0.0')

if DOCKER_ENV:
    from mongo_handler.mongo_utils import retrieve_available_clusters, drop_discovered_clusters, \
        insert_discovered_cluster_object, retrieve_compute_per_machine_type, retrieve_credentials_data_object
    from mongo_handler.variables import AKS
    from variables.variables import GKE, GCP, AZ
else:
    from web.mongo_handler.mongo_utils import retrieve_available_clusters, drop_discovered_clusters, \
        insert_discovered_cluster_object, retrieve_compute_per_machine_type, retrieve_credentials_data_object
    from web.mongo_handler.variables import AKS
    from web.variables.variables import GKE, GCP, AZ

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

if KUBERNETES_SERVICE_HOST != '0.0.0.0':
    logger.info(f'Running in Kubernetes in a {KUBERNETES_SERVICE_HOST} host. No need for discovery here')
else:
    logger.info(
        f'Running in a non Kubernetes environment in a {KUBERNETES_SERVICE_HOST} host. No need for discovery here')

CURRENTLY_ALLOWED_LOCATIONS = 'australiacentral,australiacentral2,australiaeast,australiasoutheast,brazilsouth,' \
                              'brazilsoutheast,canadacentral,canadaeast,centralindia,centralus,eastasia,eastus,' \
                              'eastus2,francecentral,francesouth,germanynorth,germanywestcentral,japaneast,japanwest,' \
                              'jioindiacentral,jioindiawest,koreacentral,koreasouth,northcentralus,northeurope,' \
                              'norwayeast,norwaywest,qatarcentral,southafricanorth,southcentralus,southeastasia,' \
                              'southindia,swedencentral,switzerlandnorth,switzerlandwest,uaecentral,uaenorth,uksouth,' \
                              'ukwest,westcentralus,westeurope,westus,westus2,westus3'
CURRENTLY_ALLOWED_LOCATIONS_LIST = CURRENTLY_ALLOWED_LOCATIONS.split(',')
AZ_LIST_CLUSTERS_COMMAND = 'az aks list --query'
AZ_LIST_GROUPS_COMMAND = 'az group list'
AZ_LIST_GROUPS_AND_CLUSTERS_COMMAND = 'az aks list --query \"[].{Name:name, ResourceGroup:resourceGroup}\"'
AZ_LIST_CLUSTERS_INFO_COMMAND = 'az aks show'
AZ_GENERATE_KUBECONFIG_COMMAND = 'az aks get-credentials'

TS = int(time.time())
TS_IN_20_YEARS = TS + 60 * 60 * 24 * 365 * 20
LOCAL_USER = gt.getuser()

key = os.getenv('SECRET_KEY').encode()
crypter = Fernet(key)

if 'Darwin' in platform.system():
    KUBECONFIG_PATH = f'/Users/{LOCAL_USER}/.kube/config'  # path to the GCP credentials

else:
    KUBECONFIG_PATH = '/root/.kube/config'


def get_credentials(user_email: str) -> tuple:
    """
    This function fetches the credentials needed to authenticate with Azure
    @param user_email:
    @return:
    """
    provider_data = retrieve_credentials_data_object(AZ, user_email)
    logger.info(f"provider_data {provider_data}")
    if provider_data:
        try:
            decrypted_credentials_ = crypter.decrypt(provider_data['azure_credentials']).decode("utf-8")
            decrypted_credentials = json.loads(decrypted_credentials_)
            return decrypted_credentials['clientId'], decrypted_credentials['clientSecret'], decrypted_credentials[
                'tenantId']
        except Exception as e:
            logger.error(f"azure credentials were not found {e}")


def generate_kubeconfig(cluster_name: str, resource_group: str):
    if os.path.exists(KUBECONFIG_PATH):
        os.remove(KUBECONFIG_PATH)
    command = f'{AZ_GENERATE_KUBECONFIG_COMMAND} --name {cluster_name} --resource-group {resource_group}'
    logger.info(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    if f'Merged "{cluster_name}"' in result.stderr:
        os.environ['KUBECONFIG'] = KUBECONFIG_PATH
        file = Path(KUBECONFIG_PATH)
        file.touch(exist_ok=True)
        with open(KUBECONFIG_PATH, "r") as f:
            kubeconfig = f.read()
            logger.info(f'The kubeconfig content is: {kubeconfig}')
            return kubeconfig


def fetch_aks_clusters(azure_client_id: str, azure_client_secret: str, azure_tenant_id: str) -> list:
    logger.info(f'A request to fetch resource groups has arrived')
    logger.info(f'Running a {AZ_LIST_GROUPS_AND_CLUSTERS_COMMAND} command')
    aks_clusters_list = []
    az_login_command = f"az login --service-principal -u {azure_client_id} -p {azure_client_secret} --tenant {azure_tenant_id}"
    result = run(az_login_command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    logger.info(f'result of the az login request: {result.stderr} {result.stdout}')
    result = run(AZ_LIST_GROUPS_AND_CLUSTERS_COMMAND, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    az_resource_groups_and_clusters_response = json.loads(result.stdout)
    for resource_group_and_cluster in az_resource_groups_and_clusters_response:
        cluster_name = resource_group_and_cluster['Name']
        resource_group = resource_group_and_cluster['ResourceGroup']
        command = f'{AZ_LIST_CLUSTERS_INFO_COMMAND} --name {cluster_name} --resource-group {resource_group}'
        logger.info(f'Running a {command} command')
        result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
        cluster = json.loads(result.stdout)
        try:
            cluster_kubeconfig = generate_kubeconfig(cluster_name=cluster['name'], resource_group=resource_group)
        except Exception as e:
            logger.error(f"failed to generate kubeconfig with az cli with error: {e}")
            cluster_kubeconfig = ""
        if cluster['powerState']['code'] == 'Running':
            num_nodes = 0
            for agent in cluster['agentPoolProfiles']:
                if agent['powerState']['code'] == 'Running':
                    machine_type = agent['vmSize']
                    num_nodes += agent['count']
                    vCPU = retrieve_compute_per_machine_type(AKS, machine_type)['vCPU']
                    memory = retrieve_compute_per_machine_type(AKS, machine_type, cluster['location'])[
                        'memory']
            totalvCPU = vCPU * num_nodes
            total_memory = size(memory * num_nodes * 1024 * 1024)
            cluster_object = {'cluster_name': cluster['name'], 'user_name': 'vacant',
                              'cluster_version': cluster['currentKubernetesVersion'],
                              'region_name': cluster['location'],
                              'az_resource_group': cluster['resourceGroup'],
                              'machine_type': machine_type,
                              'num_nodes': num_nodes,
                              'discovered': True,
                              'kubeconfig': cluster_kubeconfig,
                              'vCPU': vCPU,
                              'totalvCPU': totalvCPU,
                              'total_memory': total_memory,
                              'availability': True}
            aks_clusters_list.append(cluster_object)
    return aks_clusters_list


def main(is_fetching_aks_clusters, user_email):
    azure_client_id, azure_client_secret, azure_tenant_id = get_credentials(user_email)
    if is_fetching_aks_clusters:
        discovered_clusters_to_add = []
        trolley_built_clusters = retrieve_available_clusters(AKS)
        aks_discovered_clusters = fetch_aks_clusters(azure_client_id, azure_client_secret, azure_tenant_id)
        for aks_discovered_cluster in aks_discovered_clusters:
            if not trolley_built_clusters:
                discovered_clusters_to_add.append(aks_discovered_cluster)
            for trolley_built_cluster in trolley_built_clusters:
                if aks_discovered_cluster['cluster_name'] != trolley_built_cluster['cluster_name']:
                    discovered_clusters_to_add.append(aks_discovered_cluster)
        logger.info(f'List of discovered AKS clusters: {aks_discovered_clusters}')
        logger.info(f'List of trolley built AKS clusters: {trolley_built_clusters}')
        logger.info(f'List of discovered clusters to add: {discovered_clusters_to_add}')
        if not aks_discovered_clusters:
            drop_discovered_clusters(cluster_type=AKS)
        for discovered_cluster_to_add in discovered_clusters_to_add:
            insert_discovered_cluster_object(discovered_cluster_to_add, cluster_type=AKS)


if __name__ == '__main__':
    if KUBERNETES_SERVICE_HOST != '0.0.0.0':
        logger.info(f'Running in Kubernetes in a {KUBERNETES_SERVICE_HOST} host. No need for discovery here')
        sys.exit('Running in Kubernetes. No need for discovery here')
    else:
        logger.info(
            f'Running in a non Kubernetes environment in a {KUBERNETES_SERVICE_HOST} host')
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--fetch-aks-clusters', action='store_true', default=True, help='Fetch AKS clusters or not')
    parser.add_argument('--user-email', default='zagalsky@gmail.com',
                        help='name of the user to fetch the credentials for')
    args = parser.parse_args()
    main(is_fetching_aks_clusters=args.fetch_aks_clusters,
         user_email=args.user_email)
