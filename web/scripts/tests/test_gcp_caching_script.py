import json
import logging
import os
import platform

import getpass as gt
import sys

from google.oauth2 import service_account
from googleapiclient import discovery

from web.scripts.gcp_caching_script import fetch_zones, fetch_regions, fetch_gke_image_types, fetch_kubernetes_versions

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


def fetch_zones():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            GCP_CREDENTIALS_PATH)
        service = discovery.build('container', 'v1', credentials=credentials)
        gcp_credentials_json = get_gcp_credentials()
        gcp_project_id = json.loads(gcp_credentials_json)['project_id']
        zones_list = fetch_zones(gcp_project_id)
        return gcp_project_id, service, zones_list
    except Exception as e:
        logger.error(f'Credentials were not provided with a file with error: {e}')


def test_fetch_regions():
    gcp_project_id, service, zones_list = fetch_zones()
    regions_list = fetch_regions(gcp_project_id)
    assert isinstance(regions_list, list)
    assert len(regions_list) > 0


def test_fetch_zones():
    gcp_project_id, service, zones_list = fetch_zones()
    assert isinstance(zones_list, list)
    assert len(zones_list) > 0


def test_fetch_kubernetes_versions():
    gcp_project_id, service, zones_list = fetch_zones()
    kubernetes_versions_dict = fetch_kubernetes_versions(zones_list, gcp_project_id, service)
    assert isinstance(kubernetes_versions_dict, dict)
    assert len(kubernetes_versions_dict) > 0


def test_fetch_gke_image_types():
    gcp_project_id, service, zones_list = fetch_zones()
    gke_image_types_list = fetch_gke_image_types(zones_list, gcp_project_id, service)
    assert isinstance(gke_image_types_list, list)
    assert len(gke_image_types_list) > 0
