import json
import logging
import os
import sys
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import getpass
import platform

from kubernetes import client

from agent.k8s_objects.k8s_objects_handler import fetch_namespaces_list, fetch_deployments_list, fetch_pods_list, \
    fetch_containers_list, fetch_daemonsets_list, fetch_stateful_sets_list, fetch_services_list
from agent.trolley_server.server_handler import ServerRequest
from web.mongo_handler.mongo_objects import AgentsDataObject
from web.mongo_handler.mongo_utils import retrieve_cluster_details

from agent.k8s_client.api_client import K8sApiClient

# logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
if 'macOS' in platform.platform():
    log_path = f'{os.getcwd()}'
    file_name = 'agent_main'
else:
    log_path = '/var/log/'
    file_name = 'agent_main'


logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
logger = logging.getLogger()

fileHandler = logging.FileHandler(f"{log_path}/{file_name}")
logging.StreamHandler(sys.stdout)
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

KUBECONFIG_TEMP_PATH = f'/Users/{getpass.getuser()}/.kube/temp_config'

DEBUG_MODE = json.loads(os.environ.get('DEBUG_MODE', 'false').lower())
SERVER_URL = os.environ.get('SERVER_URL', 'https://77c0-2a0d-6fc2-41e0-1500-e5ed-d9ed-795c-d1a8.eu.ngrok.io')
INTERNAL_CLUSTER_MODE = json.loads(os.environ.get('INTERNAL_CLUSTER_MODE', 'true').lower())
CLUSTER_NAME = os.environ.get('CLUSTER_NAME', 'pavelzagalsky-gke-qjeigibl')
CONTEXT_NAME = os.environ.get('CONTEXT_NAME', '')
CLUSTER_TYPE = os.environ.get('CLUSTER_TYPE', 'gke')
FETCH_INTERVAL = int(os.environ.get('FETCH_INTERVAL', "5"))

logger.info(f'DEBUG_MODE is: {DEBUG_MODE}')
print(f'DEBUG_MODE is: {DEBUG_MODE}')
logger.info(f'SERVER_URL is: {SERVER_URL}')
print(f'SERVER_URL is: {SERVER_URL}')
logger.info(f'INTERNAL_CLUSTER_MODE is: {INTERNAL_CLUSTER_MODE}')
print(f'INTERNAL_CLUSTER_MODE is: {INTERNAL_CLUSTER_MODE}')
logger.info(f'CLUSTER_NAME is: {CLUSTER_NAME}')
logger.info(f'CONTEXT_NAME is: {CONTEXT_NAME}')
logger.info(f'CLUSTER_TYPE is: {CLUSTER_TYPE}')
logger.info(f'FETCH_INTERVAL is: {FETCH_INTERVAL}')


def main(debug_mode: bool, internal_cluster_mode: bool, cluster_name: str = None, context_name: str = None,
         cluster_type: str = None, fetch_interval: int = 30, server_url: str = ''):
    if not internal_cluster_mode:
        if not context_name:
            try:
                cluster_object = retrieve_cluster_details(cluster_type, cluster_name)
                context_name = cluster_object['context_name']
                with open(KUBECONFIG_TEMP_PATH, 'a+') as kubeconfig_file:
                    kubeconfig_file.write(cluster_object['kubeconfig'])
            except:
                logger.error(f'{cluster_name} was not found in the system')
    logger.info(f'The debug_mode is: {debug_mode}')
    logger.info(f'The internal_cluster_mode is: {internal_cluster_mode}')
    logger.info(f'The cluster_name is: {cluster_name}')
    logger.info(f'The context_name is: {context_name}')
    logger.info(f'The cluster_type is: {cluster_type}')
    logger.info(f'The fetch_interval is: {fetch_interval}')
    logger.info(f'The server_url is: {server_url}')

    k8s_api_client = K8sApiClient(debug_mode, internal_cluster_mode, cluster_name, context_name)
    api_client = k8s_api_client.fetch_api_client()
    k8s_api = client.CoreV1Api(api_client=api_client)
    apis_api = client.AppsV1Api(api_client=api_client)

    namespaces = fetch_namespaces_list(k8s_api)
    deployments = fetch_deployments_list(apis_api, namespaces)
    pods = fetch_pods_list(k8s_api, namespaces)
    containers = fetch_containers_list(k8s_api, namespaces)
    daemonsets = fetch_daemonsets_list(apis_api, namespaces)
    stateful_sets = fetch_stateful_sets_list(apis_api, namespaces)
    services = fetch_services_list(k8s_api, namespaces)

    logger.info(f'The namespaces are: {namespaces}')
    logger.info(f'The deployments are: {deployments}')
    logger.info(f'The pods are: {pods}')
    logger.info(f'The containers are: {containers}')
    logger.info(f'The daemonsets are: {daemonsets}')
    logger.info(f'The stateful_sets are: {stateful_sets}')
    logger.info(f'The services are: {services}')

    agents_data_object = AgentsDataObject(cluster_name=cluster_name, context_name=context_name, namespaces=namespaces,
                                          deployments=deployments, stateful_sets=stateful_sets, pods=pods,
                                          containers=containers, daemonsets=daemonsets, services=services)
    server_request = ServerRequest(debug_mode=debug_mode, agent_data=agents_data_object, operation='insert_agent_data',
                                   server_url=server_url)
    server_request.send_server_request()
    logger.info(f'Taking a {fetch_interval} sleep time between fetches')
    time.sleep(fetch_interval)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    while True:
        main(DEBUG_MODE, INTERNAL_CLUSTER_MODE, CLUSTER_NAME, CONTEXT_NAME, CLUSTER_TYPE, FETCH_INTERVAL, SERVER_URL)
