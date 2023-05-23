import logging
import os
import random
import string

DOCKER_ENV = os.getenv('DOCKER_ENV', False)


if DOCKER_ENV:
    from mongo_handler.mongo_utils import retrieve_cluster_details, retrieve_deployment_yaml
    from variables.variables import KUBECONFIG
else:
    from web.mongo_handler.mongo_utils import retrieve_cluster_details, retrieve_deployment_yaml
    from web.variables.variables import KUBECONFIG

from kubernetes import client, config, utils
from kubernetes.client import ApiException

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('../utils.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

KUBECONFIG_PATH = os.environ.get('KUBECONFIG_PATH', '/home/runner/.kube/config')


def random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


def apply_yaml(cluster_type: str, cluster_name: str, cluster_deployment_yaml: dict = None) -> bool:
    cluster_object = retrieve_cluster_details(cluster_type, cluster_name)
    kubeconfig = cluster_object[KUBECONFIG]
    with open(KUBECONFIG_PATH, 'a') as the_file:
        the_file.write(kubeconfig)
    config.load_kube_config(KUBECONFIG_PATH)
    k8s_client = client.ApiClient()
    if not cluster_deployment_yaml:
        cluster_deployment_yaml = retrieve_deployment_yaml(cluster_type, cluster_name)
    if isinstance(cluster_deployment_yaml, dict):
        deployment_name = cluster_deployment_yaml['metadata']['name']
        try:
            utils.create_from_yaml(k8s_client, yaml_objects=[cluster_deployment_yaml])
            logger.info(f'Deployment for {deployment_name} was successful')
            return True
        except ApiException as error:
            logger.error(f'Deployment of {deployment_name} failed. An error occurred: {error}')
            return False
    else:
        for deployment_yaml in cluster_deployment_yaml:
            deployment_name = deployment_yaml['metadata']['name']
            try:
                utils.create_from_yaml(k8s_client, yaml_objects=[deployment_yaml])
                logger.info(f'Deployment for {deployment_name} was successful')
                return True
            except:
                logger.error(f'Deployment of {deployment_name} failed')
                return False