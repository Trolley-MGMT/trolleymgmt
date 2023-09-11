import logging
import os

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


def test_fetch_locations():
    locations_dict = fetch_locations()
    assert isinstance(locations_dict, dict)
    assert len(locations_dict) > 0

def test_fetch_resource_groups():
    resource_groups_dict = fetch_resource_groups()
    assert isinstance(resource_groups_dict, dict)
    assert len(resource_groups_dict) > 0

#
def test_fetch_kubernetes_versions():
    kubernetes_versions_all_locations = fetch_kubernetes_versions()
    assert isinstance(kubernetes_versions_all_locations, dict)
    assert len(kubernetes_versions_all_locations) > 0
