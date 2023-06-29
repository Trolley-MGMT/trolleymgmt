import getpass as gt
import json
import logging
import os
import platform
import sys
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from dotenv import load_dotenv

from web.cluster_operations import ClusterOperation
from web.mongo_handler.mongo_utils import retrieve_expired_clusters, set_cluster_availability
from web.variables.variables import GKE, AKS, EKS, CLUSTER_NAME, USER_NAME, ZONE_NAME

project_folder = os.path.expanduser(os.getcwd())
load_dotenv(os.path.join(project_folder, '.env'))

LOCAL_USER = gt.getuser()
GITHUB_ACTIONS_ENV = os.getenv('GITHUB_ACTIONS_ENV', False)
DOCKER_ENV = os.getenv('DOCKER_ENV', False)

GITHUB_ACTIONS_TOKEN = os.getenv('GITHUB_ACTIONS_TOKEN', '')
GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY', '')



log_file_name = 'server.log'
if DOCKER_ENV:
    log_file_path = f'/var/log/{log_file_name}'
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

if 'Darwin' in platform.system():
    AWS_CREDENTIALS_PATH = f'/Users/{LOCAL_USER}/.aws/'
    GCP_CREDENTIALS_PATH = f'/Users/{LOCAL_USER}/.gcp/'
    AWS_CREDENTIALS_FILE_PATH = f'{AWS_CREDENTIALS_PATH}credentials'
    GCP_CREDENTIALS_FILE_PATH = f'{GCP_CREDENTIALS_PATH}/gcp_credentials.json'
    MONGO_URL = os.getenv('MONGO_URL', '')
    MONGO_USER = os.getenv('MONGO_USER', '')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', '')
    PROJECT_NAME = os.getenv('PROJECT_NAME', '')
    try:
        with open(GCP_CREDENTIALS_FILE_PATH, "r") as f:
            GOOGLE_CREDS_JSON = f.read()
            logger.info('Success read gcp_credentials.json')
    except Exception as e:
        logger.error(f'Problem extracting GCP Credentials with error: {e}')
    try:
        with open(AWS_CREDENTIALS_FILE_PATH, "r") as f:
            aws_credentials = f.read()
            AWS_ACCESS_KEY_ID = aws_credentials.split('\n')[1].split(" = ")[1]
            AWS_SECRET_ACCESS_KEY = aws_credentials.split('\n')[2].split(" = ")[1]
    except Exception as e:
        logger.error(f'Problem extracting AWS Credentials with error: {e}')
else:
    GOOGLE_CREDS_JSON = os.getenv('GOOGLE_CREDS_JSON', '')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    MONGO_URL = os.getenv('MONGO_URL', '')
    MONGO_USER = os.getenv('MONGO_USER', '')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', '')
    PROJECT_NAME = os.getenv('PROJECT_NAME', '')


def delete_clusters(cluster_type: str):
    expired_clusters_list = retrieve_expired_clusters(cluster_type=cluster_type)
    logger.info(f'clusters to expire: {expired_clusters_list}')
    for expired_cluster in expired_clusters_list:
        content = {
            'cluster_name': expired_cluster[CLUSTER_NAME.lower()],
            'user_name': expired_cluster[USER_NAME.lower()],
            'zone_name': expired_cluster[ZONE_NAME.lower()],
            'google_creds_json': GOOGLE_CREDS_JSON,
            'aws_access_key_id': AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': AWS_SECRET_ACCESS_KEY,
            'github_actions_token': GITHUB_ACTIONS_TOKEN,
            'github_repository': GITHUB_REPOSITORY,
            'mongo_url': MONGO_URL,
            'mongo_user': MONGO_USER,
            'mongo_password': MONGO_PASSWORD,
            'project_name': PROJECT_NAME
        }
        cluster_operations = ClusterOperation(**content)
        logger.info(f'expiring {expired_cluster} cluster')
        if cluster_type == GKE:
            cluster_operations.delete_gke_cluster()
        elif cluster_type == AKS:
            cluster_operations.delete_aks_cluster()
        elif cluster_type == EKS:
            cluster_operations.delete_eks_cluster()
        time.sleep(5)
        set_cluster_availability(cluster_type=cluster_type, cluster_name=expired_cluster['cluster_name'],
                                 availability=False)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--cluster_type', default='gke', type=str, help='Type of the cluster built')
    args = parser.parse_args()
    delete_clusters(cluster_type=args.cluster_type)
