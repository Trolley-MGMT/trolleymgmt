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

from web.scripts.az_caching_script import fetch_locations, fetch_resource_groups, fetch_kubernetes_versions

LOCAL_USER = gt.getuser()

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
    GCP_CREDENTIALS_DIRECTORY = f'/Users/{LOCAL_USER}/.gcp'
else:
    GCP_CREDENTIALS_DIRECTORY = "/home/runner/work"
GCP_CREDENTIALS_PATH = f'{GCP_CREDENTIALS_DIRECTORY}/gcp_credentials.json'


def get_gcp_credentials() -> str:
    try:
        with open(GCP_CREDENTIALS_PATH, "r") as f:
            google_creds_json = f.read()
            return google_creds_json
    except Exception as e:
        logger.error(f'GCP credentials were not found with error: {e}')


#
# def test_fetch_regions():
#     gcp_project_id, service, zones_list = fetch_zones()
#     regions_list = fetch_regions(gcp_project_id)
#     assert isinstance(regions_list, list)
#     assert len(regions_list) > 0
#
#
# def test_fetch_zones():
#     gcp_project_id, service, zones_list = fetch_zones()
#     assert isinstance(zones_list, list)
#     assert len(zones_list) > 0
#

def test_fetch_kubernetes_versions():
    kubernetes_versions_all_locations = fetch_kubernetes_versions()
    assert isinstance(kubernetes_versions_all_locations, dict)
    assert len(kubernetes_versions_all_locations) > 0


# def test_fetch_gke_image_types():
#     gcp_project_id, service, zones_list = fetch_zones()
#     gke_image_types_list = fetch_gke_image_types(zones_list, gcp_project_id, service)
#     assert isinstance(gke_image_types_list, list)
#     assert len(gke_image_types_list) > 0
