import logging
import os
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from dataclasses import asdict
import getpass

import yaml
from kubernetes import client

from web.mongo_handler.mongo_objects import AgentsDataObject
from web.mongo_handler.mongo_utils import insert_agents_data_object, retrieve_cluster_details

from agent.k8s_client.api_client import K8sApiClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('agent_main.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

KUBECONFIG_TEMP_PATH = f'/Users/{getpass.getuser()}/.kube/temp_config'


def fetch_namespaces_list(k8s_api) -> list:
    namespaces_list = []
    namespaces = k8s_api.list_namespace().items
    for namespace in namespaces:
        namespaces_list.append(namespace.metadata.name)
    return namespaces_list


def fetch_pods_list(k8s_api, namespaces_list) -> list:
    pods_list = []
    for namespace in namespaces_list:
        pods = k8s_api.list_namespaced_pod(namespace).items
        for pod in pods:
            pods_list.append({'namespace': namespace,
                              'pod': pod.metadata.name})
    return pods_list


def fetch_containers_list(k8s_api, namespaces_list: list = None) -> list:
    containers_list = []
    for namespace in namespaces_list:
        pods = k8s_api.list_namespaced_pod(namespace).items
        for pod in pods:
            if len(pod.spec.containers) > 1:
                for container in pod.spec.containers:
                    log = k8s_api.read_namespaced_pod_log(name=pod.metadata.name, container=container.name,
                                                          namespace=namespace)
                    containers_list.append({'namespace': namespace,
                                            'pod_name': pod.metadata.name,
                                            'container_name': container.name,
                                            'log': str(log)})
            else:
                log = k8s_api.read_namespaced_pod_log(name=pod.metadata.name,
                                                      namespace=namespace)
                containers_list.append({'namespace': namespace,
                                        'pod': pod.metadata.name,
                                        'container': pod.spec.containers[0].name,
                                        'log': str(log)})
    return containers_list


def fetch_deployments_list(apis_api, namespaces_list: '') -> list:
    deployments_list = []
    for namespace in namespaces_list:
        deployments = apis_api.list_namespaced_deployment(namespace)
        if len(deployments.items) > 0:
            if len(deployments.items) == 1:
                deployment_data = apis_api.read_namespaced_deployment(name=deployments.items[0].metadata.name,
                                                                      namespace=namespace)
                deployments_list.append({'namespace': namespace, 'deployment':
                    deployments.items[0].metadata.name,
                                         'deployment_data': str(deployment_data)})
            else:
                for deployment in deployments.items:
                    deployment_data = apis_api.read_namespaced_deployment(name=deployment.metadata.name,
                                                                          namespace=namespace)
                    deployments_list.append({'namespace': namespace,
                                             'deployment': deployment.metadata.name,
                                             'deployment_data': str(deployment_data)})
    return deployments_list


def fetch_daemonsets_list(apis_api, namespaces_list: '') -> list:
    daemonsets_list = []
    for namespace in namespaces_list:
        daemonsets = apis_api.list_namespaced_daemon_set(namespace)
        if len(daemonsets.items) > 0:
            if len(daemonsets.items) == 1:
                daemonset_data = apis_api.read_namespaced_daemon_set(name=daemonsets.items[0].metadata.name,
                                                                     namespace=namespace)
                daemonsets_list.append({'namespace': namespace, 'daemonsets':
                    daemonsets.items[0].metadata.name, 'daemonset_data': str(daemonset_data)})
            else:
                for daemonset in daemonsets.items:
                    daemonset_data = apis_api.read_namespaced_daemon_set(name=daemonset.metadata.name,
                                                                         namespace=namespace)
                    daemonsets_list.append({'namespace': namespace,
                                            'daemonsets': daemonset.metadata.name,
                                            'daemonset_data': str(daemonset_data)})
    return daemonsets_list


def fetch_services_list(k8s_api, namespaces_list: '') -> list:
    services_list = []
    for namespace in namespaces_list:
        services = k8s_api.list_namespaced_service(namespace)
        if len(services.items) > 0:
            if len(services.items) == 1:
                service_data = k8s_api.read_namespaced_service(name=services.items[0].metadata.name,
                                                               namespace=namespace)
                services_list.append({'namespace': namespace, 'deployment':
                    services.items[0].metadata.name,
                                      'service_data': str(service_data)})
            else:
                for service in services.items:
                    service_data = k8s_api.read_namespaced_service(name=service.metadata.name,
                                                                   namespace=namespace)
                    services_list.append({'namespace': namespace,
                                          'service': service.metadata.name,
                                          'service_data': str(service_data)})
    return services_list


def fetch_stateful_sets_list(apis_api, namespaces_list):
    stateful_sets_list = []
    for namespace in namespaces_list:
        stateful_sets = apis_api.list_namespaced_stateful_set(namespace)
        if len(stateful_sets.items) > 0:
            if len(stateful_sets.items) == 1:
                stateful_set_data = apis_api.read_namespaced_stateful_set(name=stateful_sets.items[0].metadata.name,
                                                                        namespace=namespace)
                stateful_sets_list.append({'namespace': namespace, 'stateful_set':
                    stateful_sets.items[0].metadata.name, 'stateful_set_data': str(stateful_set_data)})
            else:
                for stateful_set in stateful_sets.items:
                    stateful_set_data = apis_api.read_namespaced_stateful_set(name=stateful_set.metadata.name,
                                                                            namespace=namespace)
                    stateful_sets_list.append({'namespace': namespace,
                                               'stateful_set': stateful_set.metadata.name,
                                               'stateful_set_data': str(stateful_set_data)})
    return stateful_sets_list


def main(debug_mode: bool, cluster_name: str = None, context_name: str = None, cluster_type: str = None,
         fetch_interval: int = 30):
    if not context_name:
        try:
            cluster_object = retrieve_cluster_details(cluster_type, cluster_name)
            context_name = cluster_object['context_name']
            with open(KUBECONFIG_TEMP_PATH, 'a+') as kubeconfig_file:
                kubeconfig_file.write(cluster_object['kubeconfig'])
        except:
            logger.error(f'{cluster_name} was not found in the system')
    k8s_api_client = K8sApiClient(debug_mode, cluster_name, context_name)
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
    agents_data_object = AgentsDataObject(cluster_name=cluster_name, context_name=context_name, namespaces=namespaces,
                                          deployments=deployments, stateful_sets=stateful_sets, pods=pods,
                                          containers=containers, daemonsets=daemonsets, services=services)
    if insert_agents_data_object(asdict(agents_data_object)):
        logger.info('Agent data inserted successfully')
    else:
        logger.info('Agent data did not get inserted')
    logger.info(f'Taking a {fetch_interval} sleep time between fetches')
    time.sleep(fetch_interval)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--debug_mode', default=True, type=bool, help='Debugging Mode')
    parser.add_argument('--cluster_name', default='pavelzagalsky-gke-dixcybsp', type=str,
                        help='Cluster Name of the built cluster')
    parser.add_argument('--context_name', default='', type=str, help='Context Name of the built cluster')
    parser.add_argument('--cluster_type', default='gke', type=str, help='Cluster Type of the built cluster')
    parser.add_argument('--fetch_interval', default=5, type=int, help='interval between objects fetching')
    args = parser.parse_args()
    while True:
        main(args.debug_mode, args.cluster_name, args.context_name, args.cluster_type, args.fetch_interval)
