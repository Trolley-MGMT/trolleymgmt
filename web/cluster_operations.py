import getpass
import logging
import os
import platform
import subprocess
from subprocess import run, PIPE

import requests

from variables.variables import GKE, ZONE_NAME, EKS, REGION_NAME
from mongo_handler.mongo_utils import retrieve_cluster_details

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('../cluster_operations.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# horrible hack to solve the Dockerfile issues. Please find a better solution
run_env = 'not_github'
try:
    github_env_something = os.getenv('GITHUB_ENV')
    logger.info(github_env_something)
    if github_env_something is not None:
        run_env = 'github'
        logger.info('this runs on github')
    else:
        logger.info('this does not run on github')
except:
    run_env = 'not github'
    logger.error('this does not run on github')

if 'Darwin' in platform.system() or run_env == 'github':
    AWS_CREDENTIALS_PATH = f'/Users/{getpass.getuser()}/.aws/credentials'
else:
    AWS_CREDENTIALS_PATH = '/home/app/.aws/credentials'

GITHUB_ACTION_TOKEN = os.getenv('GITHUB_ACTION_TOKEN')
GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY')
GITHUB_ACTIONS_API_URL = f'https://api.github.com/repos/{GITHUB_REPOSITORY}/dispatches'
GITHUB_ACTION_REQUEST_HEADER_DOCKER = """curl -X POST -H \'Accept: application / vnd.github.everest - preview + json\' ' \
                     '-H \'Accept-Encoding: gzip, deflate\' ' \
                     """
GITHUB_ACTION_REQUEST_HEADER = {
    'Content-type': 'application/json',
    'Accept': 'application/vnd.github+json',
    'Authorization': f'token {GITHUB_ACTION_TOKEN}'
}

logger.info(f'GitHub Action Token: {GITHUB_ACTION_TOKEN}')
logger.info(f'GitHub Repository is: {GITHUB_REPOSITORY}')
logger.info(f'GITHUB_ACTIONS_API_URL is: {GITHUB_ACTIONS_API_URL}')
logger.info(f'GITHUB_ACTION_REQUEST_HEADER_DOCKER is: {GITHUB_ACTION_REQUEST_HEADER_DOCKER}')


def get_aws_credentials() -> tuple:
    with open(AWS_CREDENTIALS_PATH, "r") as f:
        aws_credentials = f.read()
        aws_access_key_id = aws_credentials.split('\n')[1].split(" = ")[1]
        aws_secret_access_key = aws_credentials.split('\n')[2].split(" = ")[1]
        return aws_access_key_id, aws_secret_access_key


def trigger_aks_build_github_action(user_name: str = '',
                                    cluster_name: str = '',
                                    cluster_type: str = '',
                                    deployment_yaml: str = '',
                                    version: str = '',
                                    aks_location: str = None,
                                    num_nodes: int = '',
                                    helm_installs: list = '',
                                    expiration_time: int = '') -> bool:
    if len(helm_installs) < 1:
        helm_installs = ["."]
    json_data = {
        "event_type": "aks-build-api-trigger",
        "client_payload": {"cluster_name": cluster_name,
                           "user_name": user_name,
                           "cluster_version": version,
                           "aks_location": aks_location,
                           "num_nodes": str(num_nodes),
                           "expiration_time": expiration_time}
    }
    response = requests.post(GITHUB_ACTIONS_API_URL,
                             headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)
    logger.info(f'This is the request response: {response}')
    return response


def trigger_gke_build_github_action(user_name: str = '',
                                    cluster_name: str = '',
                                    cluster_type: str = '',
                                    deployment_yaml: str = '',
                                    version: str = '',
                                    gke_region: str = '',
                                    gke_zone: str = '',
                                    image_type: str = '',
                                    num_nodes: int = '',
                                    helm_installs: list = '',
                                    expiration_time: int = '') -> bool:
    if len(helm_installs) < 1:
        helm_installs = ["."]
    json_data = {
        "event_type": "gke-build-api-trigger",
        "client_payload": {"cluster_name": cluster_name,
                           "user_name": user_name,
                           "cluster_version": version,
                           "region_name": gke_region,
                           "zone_name": gke_zone,
                           "image_type": image_type,
                           "num_nodes": str(num_nodes),
                           "expiration_time": expiration_time}
    }
    response = requests.post(GITHUB_ACTIONS_API_URL,
                             headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)
    logger.info(f'This is the request response: {response}')
    return response


def trigger_eks_build_github_action(user_name: str,
                                    cluster_name: str = '',
                                    cluster_type: str = '',
                                    deployment_yaml: str = '',
                                    version: str = '',
                                    eks_location: str = '',
                                    eks_zones: list = None,
                                    eks_subnets: list = None,
                                    image_type: str = '',
                                    num_nodes: int = '',
                                    helm_installs: list = '',
                                    expiration_time: int = '') -> dict:
    aws_access_key_id, aws_secret_access_key = get_aws_credentials()
    if len(helm_installs) < 1:
        helm_installs = ["."]

    json_data = {
        "event_type": "eks-build-api-trigger",
        "client_payload": {"cluster_name": cluster_name,
                           "user_name": user_name,
                           "cluster_version": version,
                           "region_name": eks_location,
                           "num_nodes": str(num_nodes),
                           "zone_names": ','.join(eks_zones),
                           "subnets": ','.join(eks_subnets),
                           "aws_access_key_id": aws_access_key_id,
                           "aws_secret_access_key": aws_secret_access_key,
                           "expiration_time": expiration_time}
    }
    response = requests.post(GITHUB_ACTIONS_API_URL,
                             headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)
    logger.info(f'This is the request response: {response}')
    return response


def trigger_trolley_agent_deployment_github_action(cluster_name: str = '',
                                                   cluster_type: str = '',
                                                   server_url: str = '',
                                                   mongo_user: str = '',
                                                   mongo_password: str = '',
                                                   mongo_url: str = '',
                                                   project_name: str = ''):
    github_command = 'curl -X POST -H \'Accept: application / vnd.github.everest - preview + json\' ' \
                     '-H \'Accept-Encoding: gzip, deflate\' ' \
                     '-H \'Authorization: token ' + GITHUB_ACTION_TOKEN + '\' ' \
                                                                          '-H \'Content-type: application/json\' -H \'User-Agent: python-requests/2.27.1\' ' \
                                                                          '-d \'{"event_type": "trolley-agent-api-deployment-trigger", "client_payload": ' \
                                                                          '{"cluster_name": "' + cluster_name + '", "cluster_type": "' + cluster_type + '",' \
                                                                                                                                                        '"server_url": "' + server_url + '", "mongo_user": "' + mongo_user + '", ' \
                                                                                                                                                                                                                             '"mongo_password": "' + mongo_password + '", "mongo_url": "' + mongo_url + '", ' \
                                                                                                                                                                                                                                                                                                        '"project_name": "' + project_name + '"}}\' ' + GITHUB_ACTIONS_API_URL + ''
    logger.info(f'Running the gke build command: {github_command}')
    try:
        response = run(github_command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
        logger.info(f'printing out the response: {response}')
        return True
    except subprocess.SubprocessError as e:
        logger.error(f'The request failed with the following error: {e}')
        return False


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
    logger.info(response)


def delete_gke_cluster(cluster_name: str = ''):
    """
    @param cluster_name: from built clusters list
    @return:
    """
    gke_cluster_details = retrieve_cluster_details(cluster_type=GKE, cluster_name=cluster_name)
    gke_zone_name = gke_cluster_details[ZONE_NAME.lower()]
    print(f'Attempting to delete {cluster_name} in {gke_zone_name}')
    json_data = {
        "event_type": "gke-delete-api-trigger",
        "client_payload": {"cluster_name": cluster_name,
                           "zone_name": gke_zone_name}
    }
    print(f'The JSON Data for the request is: {json_data}')
    print(f'The GITHUB_ACTION_REQUEST_HEADER for the request is: {GITHUB_ACTION_REQUEST_HEADER}')
    response = requests.post(GITHUB_ACTIONS_API_URL,
                             headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)
    print(response)
    logger.info(response)


def delete_eks_cluster(cluster_name: str = ''):
    """

    @param cluster_name: from built clusters list
    @return:
    """
    eks_cluster_details = retrieve_cluster_details(cluster_type=EKS, cluster_name=cluster_name)
    eks_cluster_region_name = eks_cluster_details[REGION_NAME.lower()]
    aws_access_key_id, aws_secret_access_key = get_aws_credentials()
    json_data = {
        "event_type": "eks-delete-api-trigger",
        "client_payload":
            {"cluster_name": cluster_name,
             "region_name": eks_cluster_region_name,
             "aws_access_key_id": aws_access_key_id,
             "aws_secret_access_key": aws_secret_access_key,
             }
    }
    response = requests.post(GITHUB_ACTIONS_API_URL,
                             headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)
    logger.info(response)
