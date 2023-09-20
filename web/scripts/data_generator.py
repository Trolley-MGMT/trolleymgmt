import os
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import random
from datetime import datetime

from cryptography.fernet import Fernet
from faker import Faker

from web.mongo_handler.mongo_utils import insert_gke_deployment, insert_eks_deployment, insert_aks_deployment, \
    retrieve_cache, retrieve_users_data, retrieve_kubernetes_versions, retrieve_machine_types, retrieve_machine_series, \
    retrieve_teams_data
from web.utils import random_string
from web.variables.variables import GKE, AKS, EKS, LOCATIONS_DICT, REGIONS_LIST, ZONES_LIST

key = os.getenv('SECRET_KEY').encode()
crypter = Fernet(key)

PROJECT_NAME = os.getenv("PROJECT_NAME", "trolley_11")
MEMORIES_LIST = ["2M", "4M", "8M", "16M", "32M", "64M", "128M", "256M", "512M", "1G", "2G", "4G", "8G"]
EXPIRATION_TIMES = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
KUBECONFIG = """
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUVMRENDQXBTZ0F3SUJBZ0lRZGM1V1V5M3pmY1ROVGpiNHh3QW5jakFOQmdrcWhraUc5dzBCQVFzRkFEQXYKTVMwd0t3WURWUVFERXlRMlpUSTBOemd3TXkxaFlqUmpMVFJsTWpndE9HSXpaUzB5TXpkaFltTTBORFF6WVRVdwpJQmNOTWpNd09URTRNRGMxT0RReFdoZ1BNakExTXpBNU1UQXdPRFU0TkRGYU1DOHhMVEFyQmdOVkJBTVRKRFpsCk1qUTNPREF6TFdGaU5HTXROR1V5T0MwNFlqTmxMVEl6TjJGaVl6UTBORE5oTlRDQ0FhSXdEUVlKS29aSWh2Y04KQVFFQkJRQURnZ0dQQURDQ0FZb0NnZ0dCQUo3bU8xaWREWUJzYm04V3MzYU0wMGF4NERVT2xlK3JJR2F3anZhZApkN1g1TkZuMGUxRklnbEUrNi9pYnhoS0QvL3gzb1Vpd29pby9JNjFTK1Y5QkVLZlZDZzhuQndPQ0hWZ2NDNGUyCmdxMkpCdkdpd2piR1ZVenR3YkJydnZnSlpCdGtGYWhKaFhTZURkdkp0eVpRSVRQWWQ5bnBEaUErTk5GelpVR1YKWlVVeUdxanV4cmVBZ2ZtMkxtQVJ1aXdQZnlia1YyM2ErOXdkT2d5dEJZdlNSVzJqeCs0bDVxT0FTd3F3T0R3QwpLeGQ2WGdXM2VleVMrdW5teStLMmRjZDJOdHZLWVV4SHg2eVB0UmtBTlZWUk5sZXpLZ1NzbWVNYXFHd0M1ZnJoClBvVUxaYU9ya2VvcWY5NVU3Szd4a2kxV3dmc2YvSXVBbUYzd1QvanBzanpjb3NnbkRXa0RoRFVRZi9oclpQUFoKM0NSUUh3VHZJQlVQMXdLSTF4ZnpTbXFuclh0UUZ6V1hOalczZWFBK0kramQ4UGZxSzBkbFZqL3VUVExTREZWcwpicHFQTTNEWkphMHZRbGdhSm1QdHQ3Z25wRVlrU0pKTW9nYjZ6Mkd2SXpaY1FQNkNmbDRNZ3Y4akdKazBxVU9XClkxRlBPTkg5QUN1TVZvdTIrSWJNSmFaVmp3SURBUUFCbzBJd1FEQU9CZ05WSFE4QkFmOEVCQU1DQWdRd0R3WUQKVlIwVEFRSC9CQVV3QXdFQi96QWRCZ05WSFE0RUZnUVVFa1pmUGtEbVZMZHg4K1VMd0pVTXdYbDIyRkF3RFFZSgpLb1pJaHZjTkFRRUxCUUFEZ2dHQkFCOGt4dXdlblBWb2JObkFoT0R0Mk9jVUNVQi9pOWcvR2NGVEV5SFo1UlIzCnR0d2U2SFlML0ZHQTlsWW1LYUFoS3lwZHVLSUJMa21kaHZlcm5UUFF4L1pmbTYvT2dhVkM5TllNZnQ5V1AwbUYKRE9sSzJHWklFcDB1NkhKWUxOTVV6SE9IV0JseUV0cXhnWnpjdkNZOEFTVjdJQkYwaVJvZ0twSWo1ZXVwZEl4MAo2NmwzTm9mU2xVU3JNbDF1OFMrYlpTMjhiK3ZxZmhHM2lFaEpCcUhqSkZmRFRQUXlTcklra2dXSVdvWEdaTW1qClN2ekFtWEFEV2ZLbjhhWVpkaDgvd2RFNC9MdFJ3bTVQQ2hQaWpsbHVKczlGZ2I3SGV4MUNRcDlXLyt1THFZL20KdFRwbHJLUzN3K3ZTSWNOTGY4alppMEpvL2tIK3d6WkZMTFl0eENxc1FlUVlpbU1sVGFneEhxRWV5cUdWZ0VLbwpYRzMvclNMQ1RoR1cyNkhKMFRNYU81cC9iU2hsd1BrbVhrN3NKM3laK2JNalBPUVFPZU5jWkwvYnFEZkxmNTRaCnRxcjhvb1I2Zjl2dGpNanMxRE9jaE8xdkw4ejRTbUF3c1RXeEErelBLajJPd2RDdlI0L2F6ZUpPMW5MeDduMmwKaE9Mc2xUL1BVd2svMmNJMjhsaWRJQT09Ci0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K
    server: https://34.23.111.91
  name: gke_trolley-361905_us-east1-b_admin-adminovitch-gke-kkztkwyd
contexts:
- context:
    cluster: gke_trolley-361905_us-east1-b_admin-adminovitch-gke-kkztkwyd
    user: gke_trolley-361905_us-east1-b_admin-adminovitch-gke-kkztkwyd
  name: gke_trolley-361905_us-east1-b_admin-adminovitch-gke-kkztkwyd
current-context: gke_trolley-361905_us-east1-b_admin-adminovitch-gke-kkztkwyd
kind: Config
preferences: {}
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
        team_name = random.choice(fetch_teams_list())
        fake = Faker()
        num_nodes_amt = random.randint(1, 10)
        node_ips = []
        for x in range(num_nodes_amt):
            node_ip = fake.ipv4_private()
            node_ips.append(node_ip)
        vCPU = random.randint(1, 10)
        totalvCPU = random.randint(1, 10)
        kubeconfig = crypter.encrypt(str.encode(KUBECONFIG))
        kubernetes_versions_list = retrieve_kubernetes_versions(location_name=zone_name,
                                                                provider=self.cluster_type)
        human_creation_time = fetch_creation_time()
        human_expiration_time = fetch_expiration_time()
        machine_series = retrieve_machine_series(region_name=zone_name,
                                                 cluster_type=self.cluster_type)
        machine_types = retrieve_machine_types(machine_series=random.choice(machine_series),
                                               cluster_type=self.cluster_type,
                                               region_name=zone_name)
        if self.cluster_type == GKE:
            machine_type = random.choice(machine_types)['machine_type']
        elif self.cluster_type == AKS:
            machine_type = random.choice(machine_types)['machine_type']
        elif self.cluster_type == EKS:
            machine_type = machine_types[0]['machine_type']
        else:
            machine_type = machine_types[0]['machine_type']
        cluster_object = {
            "cluster_name": f'{user_name}-{self.cluster_type}-{random_string(8)}',
            "context_name": f"gke_trolley-361905_us-{zone_name}_cluster_name",
            "user_name": user_name,
            "kubeconfig": kubeconfig,
            "nodes_names": [f"gke-{user_name}-gk-default-pool-cd9b298f-7jzq"],
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
    parser.add_argument('--cluster_type', default='eks', type=str, help='Type of the cluster built')
    parser.add_argument('--clusters_amt', default=4, type=int, help='Type the amount of test clusters to generate')
    args = parser.parse_args()
    main(cluster_type=args.cluster_type, clusters_amt=args.clusters_amt)
