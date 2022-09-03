import logging
import os
from subprocess import run, PIPE

import requests

from web.mongo_handler.mongo_utils import retrieve_cluster_details
from web.utils import random_string
from web.variables.variables import GKE, ZONE_NAME, EKS, REGION_NAME

GITHUB_ACTION_TOKEN = os.getenv('ACTION_TOKEN')
GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY')
print(f'GitHub Action Token: {GITHUB_ACTION_TOKEN}')
GITHUB_ACTIONS_API_URL = f'https://api.github.com/repos/{GITHUB_REPOSITORY}/dispatches'
GITHUB_ACTION_REQUEST_HEADER = """curl -X POST -H \'Accept: application / vnd.github.everest - preview + json\' ' \
                     '-H \'Accept-Encoding: gzip, deflate\' ' \
                     """

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('../cluster_operations.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def trigger_aks_build_github_action(user_name: str = '',
                                    version: str = '',
                                    aks_location: str = None,
                                    num_nodes: int = '',
                                    helm_installs: list = '',
                                    expiration_time: int = ''):
    cluster_name = f'{user_name}-aks-{random_string(5)}'
    if len(helm_installs) < 1:
        helm_installs = ["."]
    github_command = 'curl -X POST -H \'Accept: application / vnd.github.everest - preview + json\' ' \
                     '-H \'Accept-Encoding: gzip, deflate\' ' \
                     '-H \'Authorization: token ' + GITHUB_ACTION_TOKEN + '\' ' \
                     '-H \'Content-type: application/json\' -H \'User-Agent: python-requests/2.27.1\' ' \
                     '-d \'{"event_type": "aks-build-api-trigger", "client_payload": ' \
                     '{"cluster_name": "' + cluster_name + '", "cluster_version": "' + version + '", ' \
                     '"num_nodes": "' + str(num_nodes) + '", "aks_location": "' + aks_location + '",  ' \
                     '"helm_installs": "' + ','.join(helm_installs) + '", ' \
                     '"expiration_time": "' + str(expiration_time) + '"}}\' ' + GITHUB_ACTIONS_API_URL + ''
    response = run(github_command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    logger.info(f'printing out the response: {response}')


def trigger_gke_build_github_action(user_name: str = '',
                                    version: str = '',
                                    gke_region: str = '',
                                    gke_zone: str = '',
                                    image_type: str = '',
                                    num_nodes: int = '',
                                    helm_installs: list = '',
                                    expiration_time: int = ''):
    cluster_name = f'{user_name}-gke-{random_string(5)}'
    if len(helm_installs) < 1:
        helm_installs = ["."]
    github_command = 'curl -X POST -H \'Accept: application / vnd.github.everest - preview + json\' ' \
                     '-H \'Accept-Encoding: gzip, deflate\' ' \
                     '-H \'Authorization: token ' + GITHUB_ACTION_TOKEN + '\' ' \
                     '-H \'Content-type: application/json\' -H \'User-Agent: python-requests/2.27.1\' ' \
                     '-d \'{"event_type": "gke-build-api-trigger", "client_payload": ' \
                     '{"cluster_name": "' + cluster_name + '", "cluster_version": "' + version + '",' \
                     '"zone_name": "' + gke_zone + '", "image_type": "' + image_type + '", ' \
                     '"region_name": "' + gke_region + '", "num_nodes": "' + str(num_nodes) + '", ' \
                     '"helm_installs": "' + ','.join(helm_installs) + \
                     '", "expiration_time": "' + str(expiration_time) + '"}}\' ' + GITHUB_ACTIONS_API_URL + ''
    response = run(github_command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    logger.info(f'printing out the response: {response}')


def trigger_eks_build_github_action(user_name: str = '',
                                    version: str = '',
                                    eks_location: str = '',
                                    eks_zones: list = None,
                                    eks_subnets: list = None,
                                    image_type: str = '',
                                    num_nodes: int = '',
                                    helm_installs: list = '',
                                    expiration_time: int = ''):
    cluster_name = f'{user_name}-eks-{random_string(5)}'
    if len(helm_installs) < 1:
        helm_installs = ["."]
    github_command = 'curl -X POST -H \'Accept: application / vnd.github.everest - preview + json\' ' \
                     '-H \'Accept-Encoding: gzip, deflate\' ' \
                     '-H \'Authorization: token ' + GITHUB_ACTION_TOKEN + '\' ' \
                     '-H \'Content-type: application/json\' -H \'User-Agent: python-requests/2.27.1\' ' \
                     '-d \'{"event_type": "eks-build-api-trigger", "client_payload": ' \
                     '{"cluster_name": "' + cluster_name + '", "cluster_version": "' + version + '", ' \
                     '"zone_names": "' + ",".join(eks_zones) + '", "subnets": "' + ",".join(eks_subnets) + '", ' \
                     '"num_nodes": "' + str(num_nodes) + '", "region_name": "' + eks_location + '",  ' \
                     '"helm_installs": "' + ','.join(helm_installs) + '", ' \
                     '"expiration_time": "' + str(expiration_time) + '"}}\' ' + GITHUB_ACTIONS_API_URL + ''
    response = run(github_command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    logger.info(f'printing out the response: {response}')


def delete_aks_cluster(cluster_name: str = ''):
    """

    @param cluster_name: from built clusters list
    @return:
    """
    json_data = {
        "event_type": "aks-delete-api-trigger",
        "client_payload": {"cluster_name": cluster_name}
    }
    response = requests.post(GITHUB_ACTIONS_API_URL,
                             headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)
    print(response)


def delete_gke_cluster(cluster_name: str = ''):
    """
    @param cluster_name: from built clusters list
    @return:
    """
    gke_cluster_details = retrieve_cluster_details(cluster_type=GKE, cluster_name=cluster_name)
    gke_zone_name = gke_cluster_details[ZONE_NAME.lower()]

    json_data = {
        "event_type": "gke-delete-api-trigger",
        "client_payload": {"cluster_name": cluster_name,
                           "zone_name": gke_zone_name}
    }
    response = requests.post(GITHUB_ACTIONS_API_URL,
                             headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)
    print(response)


def delete_eks_cluster(cluster_name: str = ''):
    """

    @param cluster_name: from built clusters list
    @return:
    """
    eks_cluster_details = retrieve_cluster_details(cluster_type=EKS, cluster_name=cluster_name)
    eks_cluster_region_name = eks_cluster_details[REGION_NAME.lower()]
    json_data = {
        "event_type": "eks-delete-api-trigger",
        "client_payload": {"cluster_name": cluster_name, 'region_name': eks_cluster_region_name}
    }
    response = requests.post(GITHUB_ACTIONS_API_URL,
                             headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)
    print(response)
