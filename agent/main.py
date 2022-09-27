import os

from kubernetes import client, config
from kubernetes.client import V1NodeList

KUBECONFIG_PATH = os.environ['KUBECONFIG']

config.load_kube_config(KUBECONFIG_PATH)
k8s_client = client.ApiClient()
k8s_api = client.CoreV1Api()
apis_api = client.AppsV1Api()


def fetch_namespaces_list() -> list:
    namespaces_list = []
    namespaces = k8s_api.list_namespace().items
    for namespace in namespaces:
        namespaces_list.append(namespace.metadata.name)
    return namespaces_list


def fetch_pods_list(namespaces_list) -> list:
    pods_list = []
    for namespace in namespaces_list:
        pods = k8s_api.list_namespaced_pod(namespace).items
        for pod in pods:
            pods_list.append({'namespace': namespace,
                              'pod': pod.metadata.name})
    return pods_list


def fetch_deployments_list(namespaces_list: '') -> list:
    deployments_list = []
    for namespace in namespaces_list:
        deployments = apis_api.list_namespaced_deployment(namespace)
        if len(deployments.items) > 0:
            if len(deployments.items) == 1:
                deployments_list.append({'namespace': namespace, 'deployment':
                    deployments.items[0].metadata.name})
            else:
                for deployment in deployments.items:
                    deployments_list.append({'namespace': namespace,
                                             'deployment': deployment.metadata.name})
    return deployments_list


def fetch_daemonsets_list(namespaces_list: '') -> list:
    daemonsets_list = []
    for namespace in namespaces_list:
        daemonsets = apis_api.list_namespaced_daemon_set(namespace)
        if len(daemonsets.items) > 0:
            if len(daemonsets.items) == 1:
                daemonsets_list.append({'namespace': namespace, 'daemonsets':
                    daemonsets.items[0].metadata.name})
            else:
                for daemonset in daemonsets.items:
                    daemonsets_list.append({'namespace': namespace,
                                            'daemonsets': daemonset.metadata.name})
    return daemonsets_list


def main():
    namespaces_list = fetch_namespaces_list()
    deployments_list = fetch_deployments_list(namespaces_list)
    pods_list = fetch_pods_list(namespaces_list)
    daemonsets_list = fetch_daemonsets_list(namespaces_list)
    # fetch_services_list()
    pass


if __name__ == '__main__':
    while True:
        main()
