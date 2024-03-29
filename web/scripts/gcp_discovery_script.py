import calendar
import json
import sys
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
import yaml

from cryptography.fernet import Fernet
from google.cloud import compute_v1
from hurry.filesize import size

DOCKER_ENV = os.getenv('DOCKER_ENV', False)
KUBERNETES_SERVICE_HOST = os.getenv('KUBERNETES_SERVICE_HOST', '0.0.0.0')

log_file_name = 'server.log'
if DOCKER_ENV:
    log_file_path = f'{os.getcwd()}/web/{log_file_name}'
else:
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

if KUBERNETES_SERVICE_HOST != '0.0.0.0':
    logger.info(f'Running in Kubernetes in a {KUBERNETES_SERVICE_HOST} host. No need for discovery here')
else:
    logger.info(
        f'Running in a non Kubernetes environment in a {KUBERNETES_SERVICE_HOST} host.')

if DOCKER_ENV:
    from mongo_handler.mongo_objects import GKEObject, GCPBucketsObject, GCPFilesObject, GCPInstanceDataObject
    from mongo_handler.mongo_utils import insert_discovered_gke_cluster_object, update_discovered_gke_cluster_object, \
        insert_gcp_vm_instances_object, insert_gke_deployment ,\
        insert_gcp_buckets_object, insert_gcp_files_object, retrieve_available_clusters, retrieve_instances, \
        retrieve_compute_per_machine_type, retrieve_provider_data_object, drop_discovered_clusters
    from variables.variables import GKE, GCP
else:
    from web.mongo_handler.mongo_objects import GKEObject, GCPBucketsObject, GCPFilesObject, GCPInstanceDataObject
    from web.mongo_handler.mongo_utils import insert_discovered_gke_cluster_object, \
        update_discovered_gke_cluster_object, insert_gke_deployment ,\
        insert_gcp_vm_instances_object, \
        insert_gcp_buckets_object, insert_gcp_files_object, retrieve_available_clusters, retrieve_instances, \
        retrieve_compute_per_machine_type, retrieve_provider_data_object, drop_discovered_clusters
    from web.variables.variables import GKE, GCP

from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient import discovery

key = os.getenv('SECRET_KEY').encode()
crypter = Fernet(key)

TS = int(time.time())
TS_IN_20_YEARS = TS + 60 * 60 * 24 * 365 * 20
LOCAL_USER = gt.getuser()
GCP_PROJECT_NAME = os.environ.get('GCP_PROJECT_NAME', 'trolley-361905')
PYTHONANYWHERE_DOMAIN = os.environ.get('PYTHONANYWHERE_DOMAIN', '')

if 'Darwin' in platform.system():
    logger.info('Running the gcp_discovery_script on Mac OS')
    KUBECONFIG_PATH = f'/Users/{LOCAL_USER}/.kube/config'  # path to the GCP credentials
    CREDENTIALS_DEFAULT_PATH = f'/Users/{LOCAL_USER}/.gcp/gcp_credentials.json'
    GCP_CREDENTIALS_TEMP_DIRECTORY = f'{os.getcwd()}/.gcp'
    CREDENTIALS_PATH_TO_SAVE = f'{GCP_CREDENTIALS_TEMP_DIRECTORY}/gcp_credentials.json'
else:
    if PYTHONANYWHERE_DOMAIN == 'pythonanywhere.com':
        logger.info('Running the gcp_discovery_script on Python Anywhere')
        GCP_CREDENTIALS_TEMP_DIRECTORY = '/var/www/.gcp'
        CREDENTIALS_PATH_TO_SAVE = f'{GCP_CREDENTIALS_TEMP_DIRECTORY}/gcp_credentials.json'
    else:
        logger.info('Running the gcp_discovery_script god knows where')
        KUBECONFIG_PATH = '/root/.kube/config'
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/app/.gcp/gcp_credentials.json'
        GCP_CREDENTIALS_TEMP_DIRECTORY = "/home/app/.gcp"
        GCP_CREDENTIALS_DEFAULT_DIRECTORY = "/home/app/.gcp"
        CREDENTIALS_DEFAULT_PATH = f'{GCP_CREDENTIALS_DEFAULT_DIRECTORY}/gcp_credentials.json'
        CREDENTIALS_PATH_TO_SAVE = f'{GCP_CREDENTIALS_TEMP_DIRECTORY}/gcp_credentials.json'

logger.info(f"CREDENTIALS_PATH_TO_SAVE is: {CREDENTIALS_PATH_TO_SAVE}")


def generate_kubeconfig(cluster_name: str, zone: str) -> str:
    if os.path.exists(KUBECONFIG_PATH):
        os.remove(KUBECONFIG_PATH)
    os.environ['KUBECONFIG'] = KUBECONFIG_PATH
    kubeconfig_generate_command = f'gcloud container clusters get-credentials {cluster_name} --zone={zone}'
    file = Path(KUBECONFIG_PATH)
    file.touch(exist_ok=True)
    run(kubeconfig_generate_command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    with open(KUBECONFIG_PATH, "r") as f:
        kubeconfig = f.read()
        logger.info(f'The kubeconfig content is: {kubeconfig}')
        return kubeconfig


def list_all_instances(project_id: str, ) -> list:
    """
    Returns a list of all instances present in a project, grouped by their zone.

    Args:
        project_id: project ID or project number of the Cloud project you want to use.
    Returns:
        A dictionary with zone names as keys (in form of "zones/{zone_name}") and
        iterable collections of Instance objects as values.
    """
    logger.info(
        f'A request to list all instances was issued with the following variables: CREDENTIALS_PATH_TO_SAVE: {CREDENTIALS_PATH_TO_SAVE}')
    if os.path.exists(CREDENTIALS_PATH_TO_SAVE):
        try:
            with open(CREDENTIALS_PATH_TO_SAVE, "r") as f:
                credentials = f.read()
                logger.info(f'The credentials file content is: {credentials}')
            instance_client = compute_v1.InstancesClient.from_service_account_file(CREDENTIALS_PATH_TO_SAVE)
        except Exception as e:
            logger.error(
                f'There was an issue getting the info with the credentials file on {CREDENTIALS_PATH_TO_SAVE} path: {e}')
    else:
        try:
            with open(CREDENTIALS_DEFAULT_PATH, "r") as f:
                credentials = f.read()
                print(f'The credentials file content is: {credentials}')
            instance_client = compute_v1.InstancesClient.from_service_account_file(CREDENTIALS_DEFAULT_PATH)
        except Exception as e:
            logger.error(
                f'There was an issue getting the info with the credentials file on {CREDENTIALS_DEFAULT_PATH} path: {e}')
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
                    except Exception as e:
                        external_ip = ''
                        logger.warning(f'External IP was not found: {e}')
                    instance_object = GCPInstanceDataObject(timestamp=TS, project_name=project_id,
                                                            instance_name=instance.name, user_name="vacant",
                                                            client_name="vacant", availability=True,
                                                            internal_ip=internal_ip,
                                                            external_ip=external_ip, tags=dict(instance.labels),
                                                            machine_type=instance.machine_type.split("/")[-1],
                                                            instance_zone=instance.zone.split("/")[-1])
                    instances_object.append(instance_object)
    return instances_object


def fetch_buckets(credentials) -> GCPBucketsObject:
    gcp_buckets_list = []
    storage_client = storage.Client(credentials=credentials)
    buckets = storage_client.list_buckets()
    for bucket in buckets:
        gcp_buckets_list.append(bucket.name)
    return GCPBucketsObject(timestamp=TS, project_name=GCP_PROJECT_NAME,
                            buckets=gcp_buckets_list)


def fetch_files(credentials, gcp_buckets: GCPBucketsObject):
    gcp_files_list = []
    gcp_files_dict = {}
    storage_client = storage.Client(credentials=credentials)
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


def fetch_gke_clusters(service) -> list:
    gcp_projects = [GCP_PROJECT_NAME]
    gke_clusters_object = []
    for project in gcp_projects:
        request = service.projects().zones().clusters().list(projectId=project, zone='-')
        response = request.execute()

        if 'clusters' in response:
            clusters_list = response['clusters']
            for cluster in clusters_list:
                if cluster['status'] == 'RUNNING':
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
                    human_created_timestamp = datetime.datetime.fromtimestamp(created_epoch_time).strftime(
                        '%d-%m-%Y %H:%M:%S')
                    expiration_timestamp = TS_IN_20_YEARS
                    human_expiration_timestamp = datetime.datetime.fromtimestamp(
                        TS_IN_20_YEARS).strftime('%d-%m-%Y %H:%M:%S')

                    try:
                        kubeconfig_ = generate_kubeconfig(cluster_name=cluster['name'],
                                                         zone=cluster['zone'])
                        kubeconfig_yaml = yaml.safe_load(kubeconfig_)
                        context_name = kubeconfig_yaml['current-context']
                        kubeconfig = crypter.encrypt(str.encode(kubeconfig_))
                    except Exception as e:
                        kubeconfig = ''
                        logger.warning(f'failed to work with gcloud: {e}')
                    num_nodes = 0
                    for node_pool in cluster['nodePools']:
                        num_nodes += node_pool['initialNodeCount']
                        machine_type = node_pool['config']['machineType']
                        vCPU = retrieve_compute_per_machine_type('gke', machine_type, cluster['locations'][0])['vCPU']
                        memory = retrieve_compute_per_machine_type('gke', machine_type, cluster['locations'][0])[
                            'memory']
                        total_memory = memory * num_nodes * 1024
                    gke_cluster_object = GKEObject(cluster_name=cluster['name'], context_name=context_name,
                                                   user_name='vacant',
                                                   kubeconfig=kubeconfig, nodes_names=[], nodes_ips=[],
                                                   project_name=GCP_PROJECT_NAME,
                                                   zone_name=cluster['zone'], created_timestamp=created_epoch_time,
                                                   human_created_timestamp=human_created_timestamp,
                                                   expiration_timestamp=expiration_timestamp,
                                                   human_expiration_timestamp=human_expiration_timestamp,
                                                   cluster_version=cluster['currentMasterVersion'], runtime_version='',
                                                   os_image=cluster['nodeConfig']['imageType'],
                                                   region_name=cluster['locations'],
                                                   num_nodes=num_nodes,
                                                   machine_type=machine_type, vCPU=vCPU, total_memory=size(total_memory),
                                                   totalvCPU=vCPU * num_nodes)
                    gke_clusters_object.append(gke_cluster_object)
    return gke_clusters_object


def main(is_fetching_files: bool = False, is_fetching_buckets: bool = False, is_fetching_vm_instances: bool = False,
         is_fetching_gke_clusters: bool = False, user_email: str = ''):
    logger.info(f'PYTHONANYWHERE_DOMAIN content is:{PYTHONANYWHERE_DOMAIN}')
    logger.info("Creating a temp dir for gcp")
    logger.info(f'Checking if GCP_CREDENTIALS_TEMP_DIRECTORY: {GCP_CREDENTIALS_TEMP_DIRECTORY} exists')
    if not os.path.exists(GCP_CREDENTIALS_TEMP_DIRECTORY):
        os.mkdir(GCP_CREDENTIALS_TEMP_DIRECTORY)
    logger.info(f'Trying to fetch credentials for {user_email} user_email')
    credentials = get_credentials(user_email)
    if not credentials:
        sys.exit("provider credentials were not found")
    service = discovery.build('container', 'v1', credentials=credentials)
    global gcp_discovered_buckets
    if is_fetching_gke_clusters:
        discovered_clusters_to_add = []
        discovered_clusters_to_update = []
        trolley_built_clusters = retrieve_available_clusters(GKE)
        gke_discovered_clusters = fetch_gke_clusters(service)
        for gke_discovered_cluster in gke_discovered_clusters:
            for trolley_built_cluster in trolley_built_clusters:
                if gke_discovered_cluster['cluster_name'] != trolley_built_cluster['cluster_name']:
                    discovered_clusters_to_add.append(gke_discovered_cluster)
                else:
                    discovered_clusters_to_update.append(gke_discovered_cluster)
            if gke_discovered_cluster not in trolley_built_clusters:
                discovered_clusters_to_add.append(gke_discovered_cluster)
        logger.info(f'List of discovered GKE clusters: {gke_discovered_clusters}')
        logger.info(f'List of trolley built GKE clusters: {trolley_built_clusters}')
        logger.info(f'List of discovered clusters to add: {discovered_clusters_to_add}')
        if not gke_discovered_clusters:
            drop_discovered_clusters(cluster_type=GKE)
        for discovered_cluster_to_add in discovered_clusters_to_add:
            insert_discovered_gke_cluster_object(asdict(discovered_cluster_to_add))
        for discovered_cluster_to_update in discovered_clusters_to_update:
            update_discovered_gke_cluster_object(discovered_cluster_to_update)
    if is_fetching_vm_instances:
        already_discovered_vm_instances_to_test = []
        discovered_vm_instances_to_add = []

        already_discovered_vm_instances = retrieve_instances(GCP)
        gcp_discovered_vm_instances_object = list_all_instances(project_id=GCP_PROJECT_NAME)

        for already_discovered_vm in already_discovered_vm_instances:
            if already_discovered_vm in gcp_discovered_vm_instances_object:
                discovered_vm_instances_to_add.append(already_discovered_vm['instance_name'])

        for gcp_discovered_vm_instance in gcp_discovered_vm_instances_object:
            if gcp_discovered_vm_instance.instance_name not in already_discovered_vm_instances_to_test:
                discovered_vm_instances_to_add.append(gcp_discovered_vm_instance)

        print('List of discovered VM Instances: ')
        print(gcp_discovered_vm_instances_object)
        print('List of discovered VMs to add: ')
        print(discovered_vm_instances_to_add)
        insert_gcp_vm_instances_object(discovered_vm_instances_to_add)
    if is_fetching_buckets:
        gcp_discovered_buckets = fetch_buckets(credentials)
        print('List of discovered GCP Buckets: ')
        print(asdict(gcp_discovered_buckets))
        insert_gcp_buckets_object(asdict(gcp_discovered_buckets))
    if is_fetching_files:
        gcp_discovered_files_object = fetch_files(credentials, gcp_discovered_buckets)
        print('List of discovered GCP Files: ')
        print(asdict(gcp_discovered_files_object))
        insert_gcp_files_object(asdict(gcp_discovered_files_object))
    print('Finished the discovery script')


def get_credentials(user_email: str):
    provider_data = retrieve_provider_data_object(user_email, 'gcp')
    logger.info(f"provider_data {provider_data}")
    if provider_data:
        try:
            google_creds = provider_data['google_creds_json']
            decrypted_credentials_ = crypter.decrypt(google_creds)
            decrypted_credentials = json.loads(decrypted_credentials_)
            logger.info(f"decrypted_credentials {decrypted_credentials}")
            with open(CREDENTIALS_PATH_TO_SAVE, 'w') as fp:
                json.dump(decrypted_credentials, fp)
        except Exception as e:
            logger.error(f'google creds json were not found with error: {e}')
        credentials_file = Path(CREDENTIALS_PATH_TO_SAVE)
        if not credentials_file.is_file():
            logger.warning(f'{CREDENTIALS_PATH_TO_SAVE} file does not exist')
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH_TO_SAVE)
        return credentials
    else:
        try:
            credentials_file = Path(CREDENTIALS_DEFAULT_PATH)
            if not credentials_file.is_file():
                logger.warning(f'{CREDENTIALS_DEFAULT_PATH} file does not exist')
            credentials = service_account.Credentials.from_service_account_file(
                CREDENTIALS_DEFAULT_PATH)
            return credentials
        except:
            print("credentials file was not found")
            return ''


if __name__ == '__main__':
    if KUBERNETES_SERVICE_HOST != '0.0.0.0':
        logger.info(f'Running in Kubernetes in a {KUBERNETES_SERVICE_HOST} host. No need for discovery here')
        sys.exit('Running in Kubernetes. No need for discovery here')
    else:
        logger.info(
            f'Running in a non Kubernetes environment in a {KUBERNETES_SERVICE_HOST} host. No need for discovery here')
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--fetch-gke-clusters', action='store_true', default=True, help='Fetch GKE clusters or not')
    parser.add_argument('--fetch-vm-instances', action='store_true', default=True,
                        help='Fetch GCP compute instances or not')
    parser.add_argument('--fetch-files', action='store_true', default=True, help='Fetch files or not')
    parser.add_argument('--fetch-buckets', action='store_true', default=True, help='Fetch buckets or not')
    parser.add_argument('--user-email', default='zagalsky@gmail.com',
                        help='name of the user to fetch the credentials for')
    args = parser.parse_args()
    main(is_fetching_gke_clusters=args.fetch_gke_clusters,
         is_fetching_vm_instances=args.fetch_vm_instances,
         is_fetching_files=args.fetch_files,
         is_fetching_buckets=args.fetch_buckets,
         user_email=args.user_email)
