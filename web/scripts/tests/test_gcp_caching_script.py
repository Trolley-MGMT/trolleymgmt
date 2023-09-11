import json
import logging
import os
import platform

import getpass as gt
import sys


from dotenv import load_dotenv

project_folder_ = os.path.expanduser(os.getcwd())
project_folder = "/".join(project_folder_.split('/')[:-2])
load_dotenv(os.path.join(project_folder, '.env'))

from web.scripts.gcp_caching_script import fetch_zones, fetch_regions

LOCAL_USER = gt.getuser()
GITHUB_ACTIONS_ENV = os.getenv('GITHUB_ACTIONS_ENV')
GOOGLE_CREDS_JSON = os.getenv('GOOGLE_CREDS_JSON')

log_file_name = 'server.log'
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
    logger.info(f'platform system is Darwin')
    GCP_CREDENTIALS_DIRECTORY = f'/Users/{LOCAL_USER}/.gcp'
    GCP_CREDENTIALS_PATH = f'{GCP_CREDENTIALS_DIRECTORY}/gcp_credentials.json'
else:
    if GITHUB_ACTIONS_ENV:
        GCP_CREDENTIALS_DIRECTORY = "/home/runner/work"
        GCP_CREDENTIALS_PATH = f'{GCP_CREDENTIALS_DIRECTORY}/gcp_credentials.json'
    else:
        logger.info(f'checking the docker_env path')
        GCP_CREDENTIALS_DIRECTORY = "/home/app/.gcp"
        GCP_CREDENTIALS_PATH = f'{GCP_CREDENTIALS_DIRECTORY}/gcp_credentials.json'


def get_gcp_credentials() -> str:
    try:
        google_creds_json = os.getenv(GOOGLE_CREDS_JSON)
        return google_creds_json
    except Exception as e:
        logger.warning(f'google_creds_json was not passed: {e}')
    if 'Darwin' in platform.system():
        try:
            with open(GCP_CREDENTIALS_PATH, "r") as f:
                google_creds_json = f.read()
                return google_creds_json
        except Exception as e:
            logger.error(f'GCP credentials were not found with error: {e}')




def test_fetch_regions():
    gcp_credentials_json = get_gcp_credentials()
    # if not os.path.exists(GCP_CREDENTIALS_DIRECTORY):
    #     logger.info(f'{GCP_CREDENTIALS_DIRECTORY} was not found. Creating a directory')
    #     os.makedirs(GCP_CREDENTIALS_DIRECTORY)
    # if os.path.exists(GCP_CREDENTIALS_DIRECTORY):
    #     logger.info(f'{GCP_CREDENTIALS_DIRECTORY} exists, removing the file')
    #     os.remove(GCP_CREDENTIALS_PATH)
    # f = open(GCP_CREDENTIALS_PATH, 'a')
    # f.write(gcp_credentials_json)
    # f.close()
    # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GCP_CREDENTIALS_PATH
    gcp_project_id = json.loads(gcp_credentials_json)['project_id']
    regions_list = fetch_regions(gcp_project_id)
    assert isinstance(regions_list, list)
    assert len(regions_list) > 0

# def test_fetch_zones():
#     pass
#
# def test_fetch_subnets():
#     pass