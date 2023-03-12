import calendar
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import datetime
import getpass as gt
import logging
import os
import platform
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from subprocess import run, PIPE
import time

from google.cloud import compute_v1

from web.mongo_handler.mongo_objects import GCPVMDataObject, GCPBucketsObject, GCPFilesObject
from web.mongo_handler.mongo_utils import insert_gke_cluster_object, insert_gcp_vm_instances_object, \
    insert_gcp_buckets_object, insert_gcp_files_object

from google.cloud import storage
from google.cloud.compute import ZonesClient
from google.oauth2 import service_account
from googleapiclient import discovery

TS = int(time.time())
TS_IN_20_YEARS = TS + 60 * 60 * 24 * 365 * 20
LOCAL_USER = gt.getuser()
GCP_PROJECT_NAME = os.environ.get('GCP_PROJECT_NAME', 'trolley-361905')

if 'Darwin' in platform.system():
    KUBECONFIG_PATH = f'/Users/{LOCAL_USER}/.kube/config'  # path to the GCP credentials
    CREDENTIALS_PATH = f'/Users/{LOCAL_USER}/.gcp/gcp_credentials.json'
else:
    KUBECONFIG_PATH = '/root/.kube/config'
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/app/.gcp/gcp_credentials.json'
    CREDENTIALS_PATH = '/home/app/.gcp/gcp_credentials.json'

credentials = service_account.Credentials.from_service_account_file(
    CREDENTIALS_PATH)
service = discovery.build('container', 'v1', credentials=credentials)


def generate_kubeconfig(cluster_name: str, zone: str) -> str:
    if os.path.exists(KUBECONFIG_PATH):
        os.remove(KUBECONFIG_PATH)
    kubeconfig_generate_command = f'gcloud container clusters get-credentials {cluster_name} --zone={zone}'
    run(kubeconfig_generate_command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    file = Path(KUBECONFIG_PATH)
    file.touch(exist_ok=True)
    with open(KUBECONFIG_PATH, "r") as f:
        kubeconfig = f.read()
        logging.info(f'The kubeconfig content is: {kubeconfig}')
        return kubeconfig


def fetch_zones() -> list:
    compute_zones_client = ZonesClient(credentials=credentials)
    zones_object = compute_zones_client.list(project=GCP_PROJECT_NAME)
    zones_list = []
    for zone in zones_object:
        zones_list.append(zone.name)
    return zones_list


def fetch_regions() -> list:
    compute_zones_client = ZonesClient(credentials=credentials)
    zones_object = compute_zones_client.list(project=GCP_PROJECT_NAME)
    regions_list = []
    for zone_object in zones_object:
        zone_object_url = zone_object.region
        region_name = zone_object_url.split('/')[-1]
        if region_name not in regions_list:
            regions_list.append(region_name)
    return regions_list


def list_all_instances(
        project_id: str, ) -> GCPVMDataObject:
    """
    Returns a dictionary of all instances present in a project, grouped by their zone.

    Args:
        project_id: project ID or project number of the Cloud project you want to use.
    Returns:
        A dictionary with zone names as keys (in form of "zones/{zone_name}") and
        iterable collections of Instance objects as values.
    """
    instance_client = compute_v1.InstancesClient.from_service_account_file(CREDENTIALS_PATH)
    request = compute_v1.AggregatedListInstancesRequest()
    request.project = project_id
    request.max_results = 50

    agg_list = instance_client.aggregated_list(request=request)

    all_instances = defaultdict(list)
    instances_object = []

    for zone, response in agg_list:
        external_ip = ''
        internal_ip = ''
        if response.instances:
            all_instances[zone].extend(response.instances)
            for instance in response.instances:
                if instance.status == 'RUNNING':
                    try:
                        for networking_interface in instance.network_interfaces:
                            internal_ip = networking_interface.network_i_p
                            for access_config in networking_interface.access_configs:
                                external_ip = access_config.nat_i_p
                    except:
                        external_ip = ''
                    instance_object = {'instance_name': instance.name,
                                       'external_ip': external_ip,
                                       'internal_ip': internal_ip,
                                       'tags': dict(instance.labels),
                                       'instance_type': instance.machine_type.split("/")[-1],
                                       'instance_zone': instance.zone.split("/")[-1]}
                    instances_object.append(instance_object)
    return GCPVMDataObject(timestamp=TS, project_name=project_id, vm_instances=instances_object)


def fetch_buckets() -> GCPBucketsObject:
    gcp_buckets_list = []
    storage_client = storage.Client()
    buckets = storage_client.list_buckets()
    for bucket in buckets:
        gcp_buckets_list.append(bucket.name)
    return GCPBucketsObject(timestamp=TS, project_name=GCP_PROJECT_NAME,
                            buckets=gcp_buckets_list)


def fetch_files(gcp_buckets: GCPBucketsObject):
    gcp_files_list = []
    gcp_files_dict = {}
    storage_client = storage.Client()
    for bucket_name in gcp_buckets.buckets:
        files = storage_client.list_blobs(bucket_name)
        for file in files:
            file_object = {
                file.name: {'size': file.size,
                            'created': int(file.time_created.timestamp()),
                            'last_modified': int(file.updated.timestamp())}}
            gcp_files_list.append(file_object)
        gcp_files_dict[bucket_name] = gcp_files_list
        gcp_files_list = []
    return GCPFilesObject(timestamp=TS, project_name=GCP_PROJECT_NAME, files=gcp_files_dict)


def fetch_gke_clusters() -> list:
    gcp_projects = [GCP_PROJECT_NAME]
    gke_clusters_object = []
    for project in gcp_projects:
        request = service.projects().zones().clusters().list(projectId=project, zone='-')
        response = request.execute()

        if 'clusters' in response:
            clusters_list = response['clusters']
            for cluster in clusters_list:
                cluster_object = {'cluster_name': cluster['name'], 'user_name': 'vacant'}
                cluster_creation_time_object = cluster['createTime'].split("+")[0].split("T")
                cluster_creation_date = cluster_creation_time_object[0].split("-")
                cluster_creation_time = cluster_creation_time_object[1].split(":")
                t = datetime.datetime(int(cluster_creation_date[0]),
                                      int(cluster_creation_date[1]),
                                      int(cluster_creation_date[2]),
                                      int(cluster_creation_time[0]),
                                      int(cluster_creation_time[1]),
                                      int(cluster_creation_time[2]))
                created_epoch_time = calendar.timegm(t.timetuple())
                cluster_object['created_timestamp'] = created_epoch_time
                cluster_object['human_created_timestamp'] = datetime.datetime.fromtimestamp(
                    created_epoch_time).strftime('%d-%m-%Y %H:%M:%S')
                cluster_object['expiration_timestamp'] = TS_IN_20_YEARS
                cluster_object['human_expiration_timestamp'] = datetime.datetime.fromtimestamp(TS_IN_20_YEARS).strftime(
                    '%d-%m-%Y %H:%M:%S')
                cluster_object['cluster_version'] = cluster['currentMasterVersion']
                cluster_object['region_name'] = cluster['locations']
                cluster_object['zone_name'] = cluster['zone']
                try:
                    cluster_object['tags'] = cluster['resourceLabels']
                except:
                    pass
                cluster_object['availability'] = True
                cluster_object['nodes_names'] = []
                cluster_object['nodes_ips'] = []
                cluster_object['os_image'] = cluster['nodeConfig']['imageType']
                cluster_object['node_pools'] = cluster['nodePools']
                cluster_object['node_pools'] = cluster['nodePools']
                cluster_object['kubeconfig'] = generate_kubeconfig(cluster_name=cluster['name'], zone=cluster['zone'])
                gke_clusters_object.append(cluster_object)
    return gke_clusters_object


def main(is_fetching_files: bool = False, is_fetching_buckets: bool = False, is_fetching_vm_instances: bool = False,
         is_fetching_gke_clusters: bool = False):
    global gcp_discovered_buckets
    if is_fetching_gke_clusters:
        gke_discovered_clusters = fetch_gke_clusters()
        print(gke_discovered_clusters)
        print('List of discovered GKE Clusters: ')
        for gke_discovered_cluster in gke_discovered_clusters:
            insert_gke_cluster_object(gke_discovered_cluster)
    if is_fetching_vm_instances:
        gcp_discovered_vm_instances_object = list_all_instances(project_id=GCP_PROJECT_NAME)
        print('List of discovered VM Instances: ')
        print(asdict(gcp_discovered_vm_instances_object))
        insert_gcp_vm_instances_object(asdict(gcp_discovered_vm_instances_object))
    if is_fetching_buckets:
        gcp_discovered_buckets = fetch_buckets()
        print('List of discovered GCP Buckets: ')
        print(asdict(gcp_discovered_buckets))
        insert_gcp_buckets_object(asdict(gcp_discovered_buckets))
    if is_fetching_files:
        gcp_discovered_files_object = fetch_files(gcp_discovered_buckets)
        print('List of discovered GCP Files: ')
        print(asdict(gcp_discovered_files_object))
        insert_gcp_files_object(asdict(gcp_discovered_files_object))


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--fetch-files', action='store_true', default=True, help='Fetch files or not')
    parser.add_argument('--fetch-buckets', action='store_true', default=True, help='Fetch buckets or not')
    parser.add_argument('--fetch-vm-instances', action='store_true', default=True,
                        help='Fetch GCP compute instances or not')
    parser.add_argument('--fetch-gke-clusters', action='store_true', default=True, help='Fetch GKE clusters or not')
    args = parser.parse_args()
    main(is_fetching_files=args.fetch_files, is_fetching_buckets=args.fetch_buckets,
         is_fetching_vm_instances=args.fetch_vm_instances, is_fetching_gke_clusters=args.fetch_gke_clusters)
