import logging
import os
import re
import time
from dataclasses import asdict
from datetime import datetime
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import yaml
from hurry.filesize import size
from kubernetes import client, config
from kubernetes.client import V1NodeList

from web.mongo_handler.mongo_utils import insert_gke_deployment, insert_eks_deployment, insert_aks_deployment, \
    retrieve_deployment_yaml, remove_deployment_yaml
from web.mongo_handler.mongo_objects import GKEObject, GKEAutopilotObject, EKSObject, AKSObject
from web.utils import apply_yaml
from web.variables.variables import GKE, GKE_AUTOPILOT, EKS, AKS


MONGO_PASSWORD = os.environ['MONGO_PASSWORD']
MONGO_USER = os.environ['MONGO_USER']

KUBECONFIG_PATH = os.environ['KUBECONFIG']
MONGO_URL = os.environ['MONGO_URL']
JOB_NAME = os.getenv('JOB_NAME')
BUILD_ID = os.getenv('BUILD_ID')

PROJECT_NAME = os.environ.get('PROJECT_NAME')
CLUSTER_NAME = os.environ.get('CLUSTER_NAME')
USER_NAME = os.environ.get('USER_NAME')
ZONE_NAME = os.environ.get('ZONE_NAME')
EXPIRATION_TIME = os.environ.get('EXPIRATION_TIME')


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
        return [nodes_items[0].metadata.name]


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
         region_name: str = '', expiration_time: int = None, resource_group=''):
    if EXPIRATION_TIME:
        expiration_time = int(EXPIRATION_TIME)
    if USER_NAME:
        user_name = USER_NAME
    if CLUSTER_NAME:
        cluster_type = CLUSTER_NAME
    if ZONE_NAME:
        zone_name = ZONE_NAME
    if not kubeconfig_path:
        kubeconfig_path = KUBECONFIG_PATH
    print(f'The kubeconfig path is: {kubeconfig_path}')
    with open(kubeconfig_path, "r") as f:
        kubeconfig = f.read()
        print(f'The kubeconfig content is: {kubeconfig}')
        kubeconfig_yaml = yaml.safe_load(kubeconfig)
        print(kubeconfig_yaml)
        context_name = kubeconfig_yaml['current-context']
        print(f'The current context is: {context_name}')
    node_info = k8s_api.list_node()
    nodes_ips = get_nodes_ips(node_info)
    nodes_names = get_nodes_names(node_info)
    num_nodes = len(nodes_names)
    machine_type = node_info.items[0].metadata.labels['node.kubernetes.io/instance-type']
    vCPU = int(node_info.items[0].status.capacity['cpu'])
    total_memory_ = node_info.items[0].status.capacity['memory']
    total_memory = size(int(re.sub(r'[^0-9]', '', total_memory_)))
    cluster_version, runtime_version, os_image = get_cluster_parameters(node_info)
    timestamp = int(time.time())
    human_created_timestamp = datetime.utcfromtimestamp(timestamp).strftime('%d-%m-%Y %H:%M:%S')
    expiration_timestamp = expiration_time * 60 * 60 + timestamp
    human_expiration_timestamp = datetime.utcfromtimestamp(expiration_timestamp).strftime('%d-%m-%Y %H:%M:%S')
    if cluster_type == GKE:
        gke_deployment_object = GKEObject(cluster_name=cluster_name, context_name=context_name, user_name=user_name,
                                          kubeconfig=kubeconfig,
                                          nodes_names=nodes_names, nodes_ips=nodes_ips, project_name=PROJECT_NAME,
                                          zone_name=zone_name, created_timestamp=timestamp,
                                          human_created_timestamp=human_created_timestamp,
                                          expiration_timestamp=expiration_time,
                                          human_expiration_timestamp=human_expiration_timestamp,
                                          cluster_version=cluster_version, runtime_version=runtime_version,
                                          os_image=os_image, region_name=region_name, num_nodes=num_nodes,
                                          machine_type=machine_type, vCPU=vCPU, total_memory=total_memory,
                                          totalvCPU=vCPU * num_nodes)
        insert_gke_deployment(cluster_type=GKE, gke_deployment_object=asdict(gke_deployment_object))
        # send_slack_message(deployment_object=gke_deployment_object)
    elif cluster_type == GKE_AUTOPILOT:
        gke_autopilot_deployment_object = GKEAutopilotObject(
            cluster_name=cluster_name, context_name=context_name, user_name=user_name, kubeconfig=kubeconfig,
            nodes_names=nodes_names,
            nodes_ips=nodes_ips, project_name=project_name,
            zone_name=zone_name, region_name=region_name,
            created_timestamp=timestamp,
            human_created_timestamp=human_created_timestamp,
            expiration_timestamp=expiration_timestamp,
            human_expiration_timestamp=human_expiration_timestamp,
            cluster_version=cluster_version, num_nodes=num_nodes)
        insert_gke_deployment(cluster_type=GKE_AUTOPILOT,
                              gke_deployment_object=asdict(gke_autopilot_deployment_object))
    elif cluster_type == EKS:
        eks_deployment_object = EKSObject(cluster_name=cluster_name, context_name=context_name, user_name=user_name,
                                          kubeconfig=kubeconfig,
                                          nodes_names=nodes_names, nodes_ips=nodes_ips, project_name=project_name,
                                          zone_name=zone_name, region_name=region_name, created_timestamp=timestamp,
                                          human_created_timestamp=human_created_timestamp,
                                          expiration_timestamp=expiration_timestamp,
                                          human_expiration_timestamp=human_expiration_timestamp,
                                          cluster_version=cluster_version, num_nodes=num_nodes,
                                          machine_type=machine_type, vCPU=vCPU, total_memory=total_memory,
                                          totalvCPU=vCPU * num_nodes)
        insert_eks_deployment(eks_deployment_object=asdict(eks_deployment_object))

    elif cluster_type == AKS:
        aks_deployment_object = AKSObject(cluster_name=cluster_name, context_name=context_name, user_name=user_name,
                                          kubeconfig=kubeconfig,
                                          nodes_names=nodes_names, nodes_ips=nodes_ips, resource_group=resource_group,
                                          zone_name=zone_name, region_name=region_name, created_timestamp=timestamp,
                                          human_created_timestamp=human_created_timestamp,
                                          expiration_timestamp=expiration_timestamp,
                                          human_expiration_timestamp=human_expiration_timestamp,
                                          cluster_version=cluster_version, num_nodes=3)
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
    args = parser.parse_args()
    with open(KUBECONFIG_PATH, "r") as f:
        kubeconfig_yaml = f.read()
        print(f'The kubeconfig content is: {kubeconfig_yaml}')

    main(cluster_type=args.cluster_type,  resource_group=args.resource_group)
