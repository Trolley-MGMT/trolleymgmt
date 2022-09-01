import logging
import platform
import json

from dataclasses import asdict
import getpass as gt
from subprocess import PIPE, run

from web.mongo_handler.mongo_utils import insert_cache_object
from web.mongo_handler.mongo_objects import HelmCacheObject

from web.variables.variables import HELM

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('Caching.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

LOCAL_USER = gt.getuser()

if 'Darwin' in platform.system():
    HELM_COMMAND = '/opt/homebrew/bin/helm'
else:
    HELM_PATH = '/tmp/helm_path'
    with open(HELM_PATH, "r") as f:
        HELM_COMMAND = f.read().strip()
        print(f'The helm command is: {HELM_COMMAND}')


def fetch_helm_installs():
    print(f'A request to fetch helm installs')
    helm_installs_list = []
    update_helm_command = f'{HELM_COMMAND} repo add stable https://charts.helm.sh/stable'
    run(update_helm_command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    helm_charts_fetch_command = f'{HELM_COMMAND} search repo stable -o json'
    result = run(helm_charts_fetch_command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    installs = json.loads(result.stdout)
    for install in installs:
        helm_installs_list.append(install['name'])
    return helm_installs_list


def main():
    helm_installs_list = fetch_helm_installs()
    helm_caching_object = HelmCacheObject(
        helms_installs=helm_installs_list)
    insert_cache_object(caching_object=asdict(helm_caching_object), provider=HELM)


if __name__ == '__main__':
    main()

