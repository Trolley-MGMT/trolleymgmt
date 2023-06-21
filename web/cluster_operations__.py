import getpass
import logging
import os
import platform

import requests
from dotenv import load_dotenv

if 'Darwin' in platform.system():
    from web.variables.variables import GKE, ZONE_NAME, EKS, REGION_NAME
    from web.mongo_handler.mongo_utils import retrieve_cluster_details
else:
    from web.variables.variables import GKE, ZONE_NAME, EKS, REGION_NAME
    from web.mongo_handler.mongo_utils import retrieve_cluster_details

log_file_name = 'server.log'
log_file_path = f'{os.getcwd()}/{log_file_name}'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(log_file_name)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

project_folder = os.path.expanduser(os.getcwd())
load_dotenv(os.path.join(project_folder, '.env'))

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
    logger.info('this does not run on github')

if 'Darwin' in platform.system() or run_env == 'github':
    AWS_CREDENTIALS_PATH = f'/Users/{getpass.getuser()}/.aws/credentials'
else:
    AWS_CREDENTIALS_PATH = '/home/app/.aws/credentials'

GITHUB_ACTION_TOKEN = os.getenv('GITHUB_ACTION_TOKEN')
GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY')
GITHUB_ACTIONS_API_URL = f'https://api.github.com/repos/{GITHUB_REPOSITORY}/dispatches'


GITHUB_ACTION_REQUEST_HEADER = {
    'Content-type': 'application/json',
    'Accept': 'application/vnd.github+json',
    'Authorization': f'token {GITHUB_ACTION_TOKEN}'
}

logger.info(f'GitHub Repository is: {GITHUB_REPOSITORY}')
logger.info(f'GITHUB_ACTIONS_API_URL is: {GITHUB_ACTIONS_API_URL}')


def get_aws_credentials() -> tuple:
    with open(AWS_CREDENTIALS_PATH, "r") as f:
        aws_credentials = f.read()
        aws_access_key_id = aws_credentials.split('\n')[1].split(" = ")[1]
        aws_secret_access_key = aws_credentials.split('\n')[2].split(" = ")[1]
        return aws_access_key_id, aws_secret_access_key


def github_check(github_action_token: str, github_repository: str) -> bool:
    github_test_url = f'https://api.github.com/repos/{github_repository}'
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {github_action_token}',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    response = requests.get(url=github_test_url,
                             headers=headers)
    if response.status_code == 200:
        return True
    else:
        logger.info(f'This is the request response: {response.reason}')
        return False



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
                                                   region_name: str = '',
                                                   trolley_server_url: str = '',
                                                   mongo_user: str = '',
                                                   mongo_password: str = '',
                                                   mongo_url: str = ''):
    json_data = {
        "event_type": "trolley-agent-api-deployment-trigger",
        "client_payload": {"cluster_name": cluster_name,
                           "cluster_type": cluster_type,
                           "zone_name": region_name,
                           "trolley_server_url": trolley_server_url,
                           "mongo_user": mongo_user,
                           "mongo_password": mongo_password,
                           "mongo_url": mongo_url}
    }
    response = requests.post(GITHUB_ACTIONS_API_URL,
                             headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)

    return response


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


def delete_gke_cluster(cluster_name: str = '', discovered: bool = False):
    """
    @param cluster_name: from built clusters list
    @param discovered: cluster was discovered by a scan
    @return:
    """
    gke_cluster_details = retrieve_cluster_details(cluster_type=GKE, cluster_name=cluster_name, discovered=discovered)
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


def delete_eks_cluster(cluster_name: str = '', discovered: bool = False):
    """

    @param cluster_name: from built clusters list
    @param discovered: cluster was discovered by a scan
    @return:
    """
    eks_cluster_details = retrieve_cluster_details(cluster_type=EKS, cluster_name=cluster_name, discovered=discovered)
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
