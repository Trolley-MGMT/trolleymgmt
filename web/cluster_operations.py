import os
from subprocess import run, PIPE

import requests

from mongo_handler.mongo_utils import retrieve_cluster_details
from utils import random_string
from variables.variables import GKE, ZONE_NAME, EKS, REGION_NAME

GITHUB_ACTION_TOKEN = os.getenv('ACTION_TOKEN')
print(f'GitHub Action Token: {GITHUB_ACTION_TOKEN}')
GITHUB_ACTIONS_API_URL = 'https://api.github.com/repos/LiorYardeni/trolley/dispatches'
GITHUB_ACTION_REQUEST_HEADER = {
    'Content-type': 'application/json',
    'Accept': 'application/vnd.github+json',
    # 'Accept': 'application / vnd.github.everest - preview + json',
    'Authorization': f'token {GITHUB_ACTION_TOKEN}'
}


def trigger_aks_build_github_action(user_name: str = '',
                                    version: str = '',
                                    aks_location: str = None,
                                    num_nodes: int = '',
                                    helm_installs: list = '',
                                    expiration_time: int = ''):
    cluster_name = f'{user_name}-aks-{random_string(5)}'
    json_data = {
        "event_type": "aks-build-api-trigger",
        "client_payload": {"cluster_name": cluster_name,
                           "cluster_version": version,
                           "aks_location": aks_location,
                           "num_nodes": num_nodes,
                           "helm_installs": ','.join(helm_installs),
                           "expiration_time": expiration_time}
    }
    response = requests.post(GITHUB_ACTIONS_API_URL,
                             headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)
    print(response)


def trigger_gke_build_github_action(user_name: str = '',
                                    version: str = '',
                                    gke_region: str = '',
                                    gke_zone: str = '',
                                    image_type: str = '',
                                    num_nodes: int = '',
                                    helm_installs: list = '',
                                    expiration_time: int = ''):
    cluster_name = f'{user_name}-gke-{random_string(5)}'
    json_data = {
        "event_type": "gke-build-api-trigger",
        "client_payload": {"cluster_name": cluster_name,
                           "cluster_version": version,
                           "zone_name": gke_zone,
                           "image_type": image_type,
                           "region_name": gke_region,
                           "num_nodes": num_nodes,
                           "helm_installs": ','.join(helm_installs),
                           "expiration_time": expiration_time}
    }
    print(f'Sending out the {json_data} json_data')
    # try:
    github_command = 'curl -X POST -H \'Accept: application / vnd.github.everest - preview + json\' -H \'Accept-Encoding: gzip, deflate\' -H \'Authorization: token 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\' -H \'Content-type: application/json\' -H \'User-Agent: python-requests/2.27.1\' -d \'{"event_type": "gke-build-api-trigger", "client_payload": {"cluster_name": "' + cluster_name + '", "cluster_version": "' + version + '", "zone_name": "' + gke_zone + '", "image_type": "' + image_type + '", "region_name": "' + gke_region + '", "num_nodes": "' + str(
        num_nodes) + '", "helm_installs": "' + ','.join(helm_installs) + '", "expiration_time": "' + str(
        expiration_time) + '"}}\' https://api.github.com/repos/LiorYardeni/trolley/dispatches'
    print(f'running the github trigger command: {github_command}')
    response = run(github_command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    print(f'printing out the response: {response}')

        # r = requests.post(GITHUB_ACTIONS_API_URL,
        #                   headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)
        # print(f'The content of the response:')
        # print(f':{GITHUB_ACTIONS_API_URL}')
        # print(f':{GITHUB_ACTION_REQUEST_HEADER}')
        # print(f':{r.content}')
        # print(f':{r.status_code}')
        # print(f':{r.text}')
        # print(f':{r.ok}')
        # r.raise_for_status()
    # except requests.exceptions.HTTPError as err:
    #     print(err)
    #     raise SystemExit(err)


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
    json_data = {
        "event_type": "eks-build-api-trigger",
        "client_payload": {"cluster_name": cluster_name,
                           "cluster_version": version,
                           "region_name": eks_location,
                           "zone_names": ",".join(eks_zones),
                           "num_nodes": num_nodes,
                           "helm_installs": ','.join(helm_installs),
                           "expiration_time": expiration_time,
                           "subnets": ",".join(eks_subnets)}
    }
    response = requests.post(GITHUB_ACTIONS_API_URL,
                             headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)
    print(response)


def delete_aks_cluster(cluster_name: str = ''):
    """

    @param cluster_name: from built clusters list
    @param cluster_type: required param for deletion command
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
