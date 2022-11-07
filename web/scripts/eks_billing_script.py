import platform
from dataclasses import asdict
import logging
from subprocess import run, PIPE

import getpass as gt

import yaml

from web.mongo_handler.mongo_utils import insert_discovery_object
from web.mongo_handler.mongo_objects import EKSDiscoveryObject
from web.variables.variables import EKS

import boto3

client = boto3.client('ce')


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('eks_billing_script.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
LOCAL_USER = gt.getuser()

if 'Darwin' in platform.system():
    KUBECONFIG_PATH = f'/Users/{LOCAL_USER}/.kube/config'  # path to the GCP credentials
else:
    KUBECONFIG_PATH = '/root/.kube/config'


def generate_kubeconfig(cluster_object: dict) -> dict:
    cluster_name = cluster_object['cluster']['name']
    cluster_region = cluster_object['cluster']['arn'].split(':')[3]
    kubeconfig_generate_command = f'aws eks --region {cluster_region} update-kubeconfig --name {cluster_name}'
    response = run(kubeconfig_generate_command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    print(response)
    with open(KUBECONFIG_PATH, "r") as f:
        kubeconfig = f.read()
        print(f'The kubeconfig content is: {kubeconfig}')
        kubeconfig_yaml = yaml.safe_load(kubeconfig)
        return kubeconfig_yaml


def fetch_clusters():
    response = client.list_clusters()
    clusters_list = []
    for cluster in response['clusters']:
        cluster_object = client.describe_cluster(name=cluster)
        if cluster_object['cluster']['status'] == 'ACTIVE':
            kubeconfig = generate_kubeconfig(cluster_object)
            cluster_object['kubeconfig'] = kubeconfig
            cluster_object['cluster_name'] = cluster_object['cluster']['name']
            cluster_object['region'] = cluster_object['cluster']['arn'].split(":")[3]
            cluster_object['kubernetes_version'] = cluster_object['cluster']['version']
            cluster_object['created_timestamp'] = cluster_object['cluster']['createdAt']
            clusters_list.append(cluster_object)
    return clusters_list


def main():
    response = client.get_cost_and_usage(
        TimePeriod={
            'Start': '2022-11-01',
            'End': '2022-11-07'
        },
        Metrics=['BlendedCost'],
        Granularity='DAILY',
        Filter={
            "Tags": {
                "Key": "Key",
                "Values": [
                    "kubernetes.io/cluster/pavel-test-2",
                ]
            }
        }
    )
    eh = client.list_account_associations()
    clusters_list = fetch_clusters()
    eks_discovery_object = EKSDiscoveryObject(
        clusters_list=clusters_list
    )
    insert_discovery_object(discovery_object=asdict(eks_discovery_object), provider=EKS)


if __name__ == '__main__':
    main()
