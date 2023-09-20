import os
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import random
from datetime import datetime

import yaml
from cryptography.fernet import Fernet

from web.mongo_handler.mongo_utils import insert_gke_deployment, insert_eks_deployment, insert_aks_deployment, \
    retrieve_cache, retrieve_users_data, retrieve_kubernetes_versions, retrieve_machine_types, retrieve_machine_series, \
    retrieve_teams_data
from web.utils import random_string, fake_string, random_number
from web.variables.variables import GKE, AKS, EKS, LOCATIONS_DICT, REGIONS_LIST, ZONES_LIST

key = os.getenv('SECRET_KEY').encode()
crypter = Fernet(key)
PROJECT_NAME = os.getenv("PROJECT_NAME", "trolley_11")
MEMORIES_LIST = ["2M", "4M", "8M", "16M", "32M", "64M", "128M", "256M", "512M", "1G", "2G", "4G", "8G"]
EXPIRATION_TIMES = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
KUBECONFIG = f"""
clusters:
- cluster:
    certificate-authority-data: Aaasdf32
    server: https://1.1.1.1
  name: gke_trolley-361905_us-east1-b_admin-adminovitch-gke-kkztkwyd
contexts:
- context:
    cluster: gke_trolley-361905_us-east1-b_admin-adminovitch-gke-kkztkwyd
    user: gke_trolley-361905_us-east1-b_admin-adminovitch-gke-kkztkwyd
  name: gke_trolley-361905_us-east1-b_admin-adminovitch-gke-kkztkwyd
current-context: gke_trolley-361905_us-east1-b_admin-adminovitch-gke-kkztkwyd
kind: Config
preferences: {{}}
users:
- name: gke_trolley-361905_us-east1-b_admin-adminovitch-gke-kkztkwyd
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: gke-gcloud-auth-plugin
      installHint: Install gke-gcloud-auth-plugin for use with kubectl by following
        https://cloud.google.com/blog/products/containers-kubernetes/kubectl-auth-changes-in-gke
      provideClusterInfo: true
"""


def fetch_regions_list(cluster_type: str) -> list:
    if cluster_type == AKS:
        regions_dict = retrieve_cache(cache_type=LOCATIONS_DICT, provider=AKS)
        regions = sorted(list(regions_dict.values()))
        regions.remove("switzerlandwest")
        regions.remove("brazilsoutheast")
        regions.remove("australiacentral2")
    elif cluster_type == GKE:
        regions = retrieve_cache(cache_type=REGIONS_LIST, provider=GKE)
    elif cluster_type == EKS:
        regions = retrieve_cache(cache_type=REGIONS_LIST, provider=EKS)
    else:
        regions = retrieve_cache(cache_type=REGIONS_LIST, provider=GKE)
    return regions


def fetch_zones_list(cluster_type: str, selected_region: str) -> list:
    relevant_zones = []
    if cluster_type == AKS:
        zones_dict = retrieve_cache(cache_type=LOCATIONS_DICT, provider=AKS)
        zones = list(zones_dict.values())
    elif cluster_type == GKE:
        zones = retrieve_cache(cache_type=ZONES_LIST, provider=GKE)
    elif cluster_type == EKS:
        zones = retrieve_cache(cache_type=ZONES_LIST, provider=EKS)
    else:
        zones = retrieve_cache(cache_type=ZONES_LIST, provider=GKE)
    for zone in zones:
        if selected_region in zone:
            relevant_zones.append(zone)
    return relevant_zones


def fetch_users_list() -> list:
    users = []
    users_data = retrieve_users_data('admin-adminovitch')
    for user in users_data:
        users.append(user['user_name'])
    return users


def fetch_teams_list() -> list:
    teams = []
    teams_data = retrieve_teams_data()
    for team in teams_data:
        teams.append(team['team_name'])
    return teams


def fetch_creation_time() -> str:
    timestamp = int(time.time())
    human_creatiom_timestamp = datetime.utcfromtimestamp(timestamp).strftime('%d-%m-%Y %H:%M:%S')
    return human_creatiom_timestamp


def fetch_expiration_time() -> str:
    timestamp = int(time.time())
    expiration_time = random.choice(EXPIRATION_TIMES)
    expiration_timestamp = expiration_time * 60 * 60 + timestamp
    human_expiration_timestamp = datetime.utcfromtimestamp(expiration_timestamp).strftime('%d-%m-%Y %H:%M:%S')
    return human_expiration_timestamp


class ClusterObject:
    def __init__(self, cluster_type):
        self.cluster_type = cluster_type

    def generate_cluster_object(self):
        region_name = random.choice(fetch_regions_list(self.cluster_type))
        zone_name = random.choice(fetch_zones_list(self.cluster_type, region_name))
        user_name = random.choice(fetch_users_list())
        random_cluster_name = f'{user_name}-{self.cluster_type}-{random_string(8)}'

        team_name = random.choice(fetch_teams_list())
        num_nodes_amt = random.randint(1, 10)
        node_ips = []
        for x in range(num_nodes_amt):
            node_ip = fake_string(string_type='private_ip')
            node_ips.append(node_ip)
        vCPU = random.randint(1, 10)
        totalvCPU = random.randint(1, 10)
        kubeconfig_yaml = yaml.load_all(KUBECONFIG, yaml.FullLoader)
        for kubeconfig in kubeconfig_yaml:
            kubeconfig['clusters'][0]['cluster']['server'] = f'https://{fake_string("public_ip")}'
            kubeconfig['clusters'][0]['cluster']['certificate-authority-data'] = random_string(length=2012, lower_case_only=False)
            kubeconfig['contexts'][0]['name'] = f'{self.cluster_type}_{zone_name}_{random_cluster_name}'
            kubeconfig['contexts'][0]['context']['cluster'] = f'{self.cluster_type}_{zone_name}_{random_cluster_name}'
            kubeconfig['contexts'][0]['context']['user'] = f'{self.cluster_type}_{zone_name}_{random_cluster_name}'
            kubeconfig['current-context'] = f'{self.cluster_type}_{zone_name}_{random_cluster_name}'
            kubeconfig['users'][0]['name'] = f'{self.cluster_type}_{zone_name}_{random_cluster_name}'
        encrypted_kubeconfig = crypter.encrypt(str.encode(str(kubeconfig)))
        kubernetes_versions_list = retrieve_kubernetes_versions(location_name=zone_name,
                                                                provider=self.cluster_type)
        human_creation_time = fetch_creation_time()
        human_expiration_time = fetch_expiration_time()
        if self.cluster_type == EKS:
            machine_series = retrieve_machine_series(region_name=region_name,
                                                     cluster_type=self.cluster_type)
            machine_types = retrieve_machine_types(machine_series=random.choice(machine_series),
                                                   cluster_type=self.cluster_type,
                                                   region_name=region_name)

        else:
            machine_series = retrieve_machine_series(region_name=zone_name,
                                                     cluster_type=self.cluster_type)
            machine_types = retrieve_machine_types(machine_series=random.choice(machine_series),
                                                   cluster_type=self.cluster_type,
                                                   region_name=zone_name)
        if self.cluster_type == GKE:
            machine_type = random.choice(machine_types)['machine_type']
            random_context_name = f"gke_trolley-{random_number(6)}_{zone_name}_{random_cluster_name}"
        elif self.cluster_type == AKS:
            machine_type = random.choice(machine_types)['machine_type']
            random_context_name = random_cluster_name
        elif self.cluster_type == EKS:
            machine_type = random.choice(machine_types)['machine_type']
            random_context_name = f"arn:aws:eks:{region_name}:{random_number(12)}:cluster/{random_cluster_name}"
        else:
            machine_type = machine_types[0]['machine_type']
        cluster_object = {
            "cluster_name": f'{random_cluster_name}',
            "context_name": random_context_name,
            "user_name": user_name,
            "kubeconfig": encrypted_kubeconfig,
            "nodes_names": [f"{self.cluster_type}-{user_name}-default-pool-cd9b298f-7jzq"],
            "nodes_ips": node_ips,
            "created_timestamp": int(time.time()),
            "human_created_timestamp": human_creation_time,
            "expiration_timestamp": 1,
            "human_expiration_timestamp": human_expiration_time,
            "project_name": PROJECT_NAME,
            "zone_name": zone_name,
            "cluster_version": random.choice(kubernetes_versions_list),
            "runtime_version": "containerd://1.7.2",
            "os_image": "Container-Optimized OS from Google",
            "region_name": region_name,
            "num_nodes": num_nodes_amt,
            "vCPU": vCPU,
            "totalvCPU": totalvCPU,
            "total_memory": random.choice(MEMORIES_LIST),
            "machine_type": machine_type,
            "availability": True

        }
        return cluster_object


def main(cluster_type: str, clusters_amt: int):
    for i in range(clusters_amt):
        cluster_object = ClusterObject(cluster_type)
        cluster_object_dict = cluster_object.generate_cluster_object()
        if cluster_type == GKE:
            insert_gke_deployment(cluster_type=cluster_type, gke_cluster_object=cluster_object_dict)
        elif cluster_type == AKS:
            insert_aks_deployment(aks_cluster_object=cluster_object_dict)
        elif cluster_type == EKS:
            insert_eks_deployment(eks_cluster_object=cluster_object_dict)
    pass


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--cluster_type', default='gke', type=str, help='Type of the cluster built')
    parser.add_argument('--clusters_amt', default=4, type=int, help='Type the amount of test clusters to generate')
    args = parser.parse_args()
    main(cluster_type=args.cluster_type, clusters_amt=args.clusters_amt)
