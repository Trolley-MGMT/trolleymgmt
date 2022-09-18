import logging
import os
import platform
import time
from dataclasses import asdict
from datetime import datetime
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from subprocess import PIPE, run

from kubernetes import client, config
from kubernetes.client import V1NodeList

from web.mongo_handler.mongo_utils import insert_gke_deployment, insert_eks_deployment, insert_aks_deployment, \
    retrieve_deployment_yaml, remove_deployment_yaml
from web.mongo_handler.mongo_objects import GKEObject, GKEAutopilotObject, EKSObject, AKSObject
from web.utils import apply_yaml
from web.variables.variables import GKE, GKE_AUTOPILOT, EKS, AKS, MACOS

if MACOS in platform.platform():
    HELM_COMMAND = '/opt/homebrew/bin/helm'

else:
    HELM_PATH = '/tmp/helm_path'
    with open(HELM_PATH, "r") as f:
        HELM_COMMAND = f.read().strip()
        print(f'The helm command is: {HELM_COMMAND}')
    PROJECT_NAME = os.environ['PROJECT_NAME']
    MONGO_PASSWORD = os.environ['MONGO_PASSWORD']
    MONGO_USER = os.environ['MONGO_USER']

KUBECONFIG_PATH = os.environ['KUBECONFIG']
MONGO_URL = os.environ['MONGO_URL']
PROJECT_NAME = os.environ['PROJECT_NAME']
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']
MONGO_USER = os.environ['MONGO_USER']
JOB_NAME = os.getenv('JOB_NAME')
BUILD_ID = os.getenv('BUILD_ID')
KUBECTL_COMMAND = 'kubectl'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('kubernetes_post_deployment.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

config.load_kube_config(KUBECONFIG_PATH)
k8s_client = client.ApiClient()
k8s_api = client.CoreV1Api()


def get_nodes_ips(node_info: V1NodeList) -> list:
    nodes_ips = []
    if len(node_info.items) > 1:
        for node in node_info.items:
            internal_address = node.status.addresses[0].address
            external_address = node.status.addresses[1].address
            nodes_ips.append(internal_address)
    else:
        return node_info.items[0].status.addresses[0].address


def get_nodes_names(node_info: V1NodeList) -> list:
    nodes_items = node_info.items
    nodes_names = []
    if len(nodes_items) > 1:
        for node in nodes_items:
            node_name = node.metadata.name
            nodes_names.append(node_name)
        return nodes_names
    else:
        return nodes_items[0].metadata.name


def get_cluster_parameters(node_info: V1NodeList) -> tuple:
    nodes_items = node_info.items
    if len(nodes_items) > 1:
        for node in nodes_items:
            return node.status.node_info.kubelet_version, \
                   node.status.node_info.container_runtime_version, \
                   node.status.node_info.os_image
    else:
        return nodes_items[0].status.node_info.kubelet_version, \
               nodes_items[0].status.node_info.container_runtime_version, \
               nodes_items[0].status.node_info.os_image


# def apply_yaml(deployment_yaml_dict: dict):
#     if isinstance(deployment_yaml_dict, dict):
#         deployment_name = deployment_yaml_dict['metadata']['name']
#         try:
#             utils.create_from_yaml(k8s_client, yaml_objects=[deployment_yaml_dict])
#             logger.info(f'Deployment for {deployment_name} was successful')
#         except ApiException as error:
#             logger.error(f'Deployment of {deployment_name} failed. An error occurred: {error}')
#     else:
#         for deployment_yaml in deployment_yaml_dict:
#             deployment_name = deployment_yaml['metadata']['name']
#             try:
#                 utils.create_from_yaml(k8s_client, yaml_objects=[deployment_yaml])
#                 logger.info(f'Deployment for {deployment_name} was successful')
#             except:
#                 logger.error(f'Deployment of {deployment_name} failed')


def main(kubeconfig_path: str = '', cluster_type: str = '', project_name: str = '', user_name: str = '',
         cluster_name: str = '', zone_name: str = '',
         region_name: str = '', expiration_time: int = '', helm_installs: str = '', resource_group=''):
    if not kubeconfig_path:
        kubeconfig_path = KUBECONFIG_PATH
    print(f'The kubeconfig path is: {kubeconfig_path}')
    with open(kubeconfig_path, "r") as f:
        kubeconfig = f.read()
        print(f'The kubeconfig content is: {kubeconfig}')

    if ',' in helm_installs:
        helm_installs_list = helm_installs.split(',')
        for helm_install in helm_installs_list:
            helm_name = helm_install.split('/')[1]
            command = HELM_COMMAND + ' upgrade --install ' + helm_name + ' ' + helm_install
            print(f'Running a {command} command')
            result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
            print(f'The result is: {result}')
    elif '.' in helm_installs:
        print(f'No helm charts to install for {cluster_name} cluster')
    node_info = k8s_api.list_node()
    nodes_ips = get_nodes_ips(node_info)
    nodes_names = get_nodes_names(node_info)
    cluster_version, runtime_version, os_image = get_cluster_parameters(node_info)
    timestamp = int(time.time())
    human_created_timestamp = datetime.utcfromtimestamp(timestamp).strftime('%d-%m-%Y %H:%M:%S')
    expiration_timestamp = expiration_time * 60 * 60 + timestamp
    human_expiration_timestamp = datetime.utcfromtimestamp(expiration_timestamp).strftime('%d-%m-%Y %H:%M:%S')

    if cluster_type == GKE:
        gke_deployment_object = GKEObject(cluster_name=cluster_name, user_name=user_name, kubeconfig=kubeconfig,
                                          nodes_names=nodes_names, nodes_ips=nodes_ips, project_name=project_name,
                                          zone_name=zone_name, created_timestamp=timestamp,
                                          human_created_timestamp=human_created_timestamp,
                                          expiration_timestamp=expiration_timestamp,
                                          human_expiration_timestamp=human_expiration_timestamp,
                                          cluster_version=cluster_version, runtime_version=runtime_version,
                                          os_image=os_image, region_name=region_name)
        insert_gke_deployment(cluster_type=GKE, gke_deployment_object=asdict(gke_deployment_object))
        # send_slack_message(deployment_object=gke_deployment_object)
    elif cluster_type == GKE_AUTOPILOT:
        gke_autopilot_deployment_object = GKEAutopilotObject(
            cluster_name=cluster_name, user_name=user_name, kubeconfig=kubeconfig, nodes_names=nodes_names,
            nodes_ips=nodes_ips, project_name=project_name,
            zone_name=zone_name, region_name=region_name,
            created_timestamp=timestamp,
            human_created_timestamp=human_created_timestamp,
            expiration_timestamp=expiration_timestamp,
            human_expiration_timestamp=human_expiration_timestamp,
            cluster_version=cluster_version)
        insert_gke_deployment(cluster_type=GKE_AUTOPILOT,
                              gke_deployment_object=asdict(gke_autopilot_deployment_object))
    elif cluster_type == EKS:
        eks_deployment_object = EKSObject(cluster_name=cluster_name, user_name=user_name, kubeconfig=kubeconfig,
                                          nodes_names=nodes_names, nodes_ips=nodes_ips, project_name=project_name,
                                          zone_name=zone_name, region_name=region_name, created_timestamp=timestamp,
                                          human_created_timestamp=human_created_timestamp,
                                          expiration_timestamp=expiration_timestamp,
                                          human_expiration_timestamp=human_expiration_timestamp,
                                          cluster_version=cluster_version)
        insert_eks_deployment(eks_deployment_object=asdict(eks_deployment_object))

    elif cluster_type == AKS:
        aks_deployment_object = AKSObject(cluster_name=cluster_name, user_name=user_name, kubeconfig=kubeconfig,
                                          nodes_names=nodes_names, nodes_ips=nodes_ips, resource_group=resource_group,
                                          zone_name=zone_name, region_name=region_name, created_timestamp=timestamp,
                                          human_created_timestamp=human_created_timestamp,
                                          expiration_timestamp=expiration_timestamp,
                                          human_expiration_timestamp=human_expiration_timestamp,
                                          cluster_version=cluster_version)
        insert_aks_deployment(aks_deployment_object=asdict(aks_deployment_object))
    try:
        deployment_yaml_dict = retrieve_deployment_yaml(cluster_type, cluster_name)
    except:
        deployment_yaml_dict = {}
    if deployment_yaml_dict:
        apply_yaml(cluster_type, cluster_name)
    remove_deployment_yaml(cluster_type, cluster_name)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--cluster_type', default='gke', type=str, help='Type of the cluster built')
    parser.add_argument('--project_name', default='trolley', type=str, help='Name of the project')
    parser.add_argument('--resource_group', default='myResourceGroup', type=str, help='Name of Resource Group for AKS')
    parser.add_argument('--cluster_name', default='latest', type=str, help='Name of the built cluster')
    parser.add_argument('--user_name', default='lioryardeni', type=str, help='Name of the user who built the cluster')
    parser.add_argument('--region_name', default='us-central1', type=str,
                        help='Name of the region where the cluster was built')
    parser.add_argument('--zone_name', default='us-central1-c', type=str,
                        help='Name of the zone where the cluster was built')
    parser.add_argument('--expiration_time', default=24, type=int, help='Expiration time of the cluster in hours')
    parser.add_argument('--helm_installs', default='', type=str, help='Helm installation to run post deployment')
    args = parser.parse_args()
    with open(KUBECONFIG_PATH, "r") as f:
        kubeconfig_yaml = f.read()
        print(f'The kubeconfig content is: {kubeconfig_yaml}')

    main(cluster_type=args.cluster_type, project_name=args.project_name,
         user_name=args.user_name,
         cluster_name=args.cluster_name,
         region_name=args.region_name, zone_name=args.zone_name, expiration_time=args.expiration_time,
         helm_installs=args.helm_installs,
         resource_group=args.resource_group)
