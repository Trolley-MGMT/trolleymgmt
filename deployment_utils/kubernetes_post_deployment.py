import configparser
import getpass
import logging
import os
import platform
import time
from dataclasses import asdict
from datetime import datetime
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from subprocess import call, PIPE, run

from mongo_handler.mongo_utils import insert_gke_deployment, insert_eks_deployment, insert_aks_deployment
from mongo_handler.mongo_objects import GKEObject, GKEAutopilotObject, EKSObject, AKSObject
from variables.variables import GKE, GKE_AUTOPILOT, EKS, AKS, MACOS

if MACOS in platform.platform():
    CUR_DIR = os.getcwd()
    PROJECT_ROOT = "/".join(CUR_DIR.split('/'))
    print(f'current directory is: {PROJECT_ROOT}')
    config = configparser.ConfigParser()
    config_ini_file = "/".join(PROJECT_ROOT.split("/")[:-1]) + "/config.ini"
    print(f'config ini file location is: {config_ini_file}')
    config.read(config_ini_file)
    PROJECT_ID = config['DEFAULT']['project_id']
    JENKINS_URL = config['DEFAULT']['jenkins_url']
    JENKINS_USER = config['DEFAULT']['jenkins_user']
else:
    PROJECT_ID = os.environ['PROJECT_ID']
    JENKINS_URL = os.environ['JENKINS_URL']
    JENKINS_USER = os.environ['JENKINS_USER']

JOB_NAME = os.getenv('JOB_NAME')
BUILD_ID = os.getenv('BUILD_ID')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('kubernetes_post_deployment.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

if 'Darwin' in platform.system():
    JENKINS_BUILD_URL = f'{JENKINS_URL}/job/gke_deployment/5/console'
    WORKSPACE = '/var/lib/jenkins/workspace/gke_deployment'
    CURRENT_DIR = os.getcwd()
    CLUSTER_NAME_FILE_PATH = f'{CURRENT_DIR}/cluster_name_file_path'
    OBJECT_ID_FILE_PATH = f'{CURRENT_DIR}/object_id'
    KUBECONFIG_LOCATION = f'/Users/{getpass.getuser()}/.kube/config'
    KUBECONFIG_REMOVAL_COMMAND = ['rm', KUBECONFIG_LOCATION]
    KUBECTL_COMMAND = 'kubectl'
    HELM_COMMAND = '/opt/homebrew/bin/helm'

else:
    JENKINS_BUILD_URL = os.getenv('BUILD_URL')
    WORKSPACE = os.getenv('WORKSPACE')
    HOME = os.getenv('HOME')
    SLACK_USER = os.getenv('BUILD_USER_ID')
    CLUSTER_NAME_FILE_PATH = 'MEH'
    # CLUSTER_NAME_FILE_PATH = f'{JENKINS_HOME}/jobs/{JOB_NAME}/builds/{BUILD_ID}/cluster_name_file_path'
    OBJECT_ID_FILE_PATH = 'MEH2'
    # OBJECT_ID_FILE_PATH = f'{JENKINS_HOME}/jobs/{JOB_NAME}/builds/{BUILD_ID}/object_id'
    # KUBECONFIG_LOCATION = os.getenv('KUBECONFIG')
    # KUBECONFIG_REMOVAL_COMMAND = ['rm', KUBECONFIG_LOCATION]
    KUBECTL_COMMAND = 'kubectl'
    HELM_COMMAND = 'helm'


def generate_kubeconfig(cluster_type: str = '', project_id: str = '', cluster_name: str = '', zone_name: str = '',
                        region_name: str = '', resource_group: str = '') -> str:
    """
    This function generates a kubeconfig_yaml for the created GKE cluster
    @return:
    """
    # call(KUBECONFIG_REMOVAL_COMMAND, timeout=None)

    if cluster_type == 'gke':
        command = [
            'gcloud', 'container', 'clusters', 'get-credentials',
            cluster_name, '--zone', zone_name, '--project', project_id]
    elif cluster_type == 'gke_autopilot':
        command = [
            'gcloud', 'container', 'clusters', 'get-credentials', cluster_name, '--region', region_name, '--project',
            project_id]
    elif cluster_type == 'aks':
        command = [
            'az', 'aks', 'get-credentials', '--resource-group', resource_group, '--name', cluster_name
        ]
    elif cluster_type == 'eks':
        command = [
            'aws', 'eks', '--region', zone_name, 'update-kubeconfig', '--name', cluster_name
        ]
    if 'Darwin' in platform.system():
        call(command, timeout=None)

        # os.environ["KUBECONFIG"] = KUBECONFIG_LOCATION
        command = [KUBECTL_COMMAND, 'get', 'pods', '--all-namespaces', '--insecure-skip-tls-verify=true']
        call(command, timeout=None)

    with open(os.environ["KUBECONFIG"], "r") as f:
        kubeconfig_yaml = f.read()
    return kubeconfig_yaml


def get_nodes_ips() -> list:
    command = KUBECTL_COMMAND + ' get nodes -o wide | awk \'{print $6}\''
    print(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    print(f'The result is: {result}')
    nodes_ips = result.stdout.split('\n')[1:-1]
    return nodes_ips


def get_nodes_names() -> list:
    command = KUBECTL_COMMAND + ' get nodes -o wide | awk \'{print $1}\''
    print(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    print(f'The result is: {result}')
    nodes_names = result.stdout.split('\n')[1:-1]
    return nodes_names


def get_cluster_version() -> str:
    command = KUBECTL_COMMAND + ' get nodes -o wide | awk \'{print $5}\''
    print(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    print(f'The result is: {result}')
    cluster_version = result.stdout.split('\n')[1:-1][0]
    return cluster_version


def main(cluster_type: str = '', project_id: str = '', user_name: str = '', cluster_name: str = '', zone_name: str = '',
         region_name: str = '', expiration_time: int = '', helm_installs: str = '', resource_group=''):
    kubeconfig = generate_kubeconfig(cluster_type=cluster_type, project_id=project_id, cluster_name=cluster_name,
                                     zone_name=zone_name, region_name=region_name, resource_group=resource_group)

    if ',' in helm_installs:
        helm_installs_list = helm_installs.split(',')
        for helm_install in helm_installs_list:
            helm_name = helm_install.split('/')[1]
            command = HELM_COMMAND + ' upgrade --install ' + helm_name + ' ' + helm_install
            print(f'Running a {command} command')
            result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
            print(f'The result is: {result}')
    elif '.' in helm_installs:
        print(f'No helm charts to install for {cluster_name} cluster')
    # else:
    #     command = HELM_COMMAND + ' upgrade --install ' + helm_installs
    #     print(f'Running a {command} command')
    #     result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    #     print(f'The result is: {result}')
    nodes_ips = get_nodes_ips()
    nodes_names = get_nodes_names()
    try:
        cluster_version = get_cluster_version()
    except:
        cluster_version = ''
    timestamp = int(time.time())
    human_created_timestamp = datetime.utcfromtimestamp(timestamp).strftime('%d-%m-%Y %H:%M:%S')
    expiration_timestamp = expiration_time * 60 * 60 + timestamp
    human_expiration_timestamp = datetime.utcfromtimestamp(expiration_timestamp).strftime('%d-%m-%Y %H:%M:%S')

    if cluster_type == GKE:
        gke_deployment_object = GKEObject(cluster_name=cluster_name, user_name=user_name, kubeconfig=kubeconfig,
                                          nodes_names=nodes_names, nodes_ips=nodes_ips,
                                          jenkins_build_url=JENKINS_BUILD_URL, project_id=project_id,
                                          zone_name=zone_name, created_timestamp=timestamp,
                                          human_created_timestamp=human_created_timestamp,
                                          expiration_timestamp=expiration_timestamp,
                                          human_expiration_timestamp=human_expiration_timestamp,
                                          cluster_version=cluster_version, region_name=region_name)
        insert_gke_deployment(cluster_type=GKE, gke_deployment_object=asdict(gke_deployment_object))
        # send_slack_message(deployment_object=gke_deployment_object)
    elif cluster_type == GKE_AUTOPILOT:
        gke_autopilot_deployment_object = GKEAutopilotObject(
            cluster_name=cluster_name, user_name=user_name, kubeconfig=kubeconfig, nodes_names=nodes_names,
            nodes_ips=nodes_ips,
            jenkins_build_url=JENKINS_BUILD_URL, project_id=project_id,
            zone_name=zone_name, region_name=region_name,
            created_timestamp=timestamp,
            human_created_timestamp=human_created_timestamp,
            expiration_timestamp=expiration_timestamp,
            human_expiration_timestamp=human_expiration_timestamp,
            cluster_version=cluster_version)
        insert_gke_deployment(cluster_type=GKE_AUTOPILOT,
                              gke_deployment_object=asdict(gke_autopilot_deployment_object))
    elif cluster_type == EKS:
        eks_deployment_object = EKSObject(cluster_name=cluster_name, user_name=user_name, kubeconfig=kubeconfig,
                                          nodes_names=nodes_names, nodes_ips=nodes_ips,
                                          jenkins_build_url=JENKINS_BUILD_URL, project_id=project_id,
                                          zone_name=zone_name, created_timestamp=timestamp,
                                          human_created_timestamp=human_created_timestamp,
                                          expiration_timestamp=expiration_timestamp,
                                          human_expiration_timestamp=human_expiration_timestamp,
                                          cluster_version=cluster_version)
        insert_eks_deployment(eks_deployment_object=asdict(eks_deployment_object))

    elif cluster_type == AKS:
        aks_deployment_object = AKSObject(cluster_name=cluster_name, user_name=user_name, kubeconfig=kubeconfig,
                                          nodes_names=nodes_names, nodes_ips=nodes_ips, resource_group=resource_group,
                                          jenkins_build_url=JENKINS_BUILD_URL,
                                          zone_name=zone_name, created_timestamp=timestamp,
                                          human_created_timestamp=human_created_timestamp,
                                          expiration_timestamp=expiration_timestamp,
                                          human_expiration_timestamp=human_expiration_timestamp,
                                          cluster_version=cluster_version)
        insert_aks_deployment(aks_deployment_object=asdict(aks_deployment_object))


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--cluster_type', default='gke', type=str, help='Type of the cluster built')
    parser.add_argument('--project_id', default='boneseye', type=str, help='Name of the project')
    parser.add_argument('--resource_group', default='myResourceGroup', type=str, help='Name of Resource Group for AKS')
    parser.add_argument('--cluster_name', default='latest', type=str, help='Name of the built cluster')
    parser.add_argument('--user_name', default='pavelzagalsky', type=str, help='Name of the user who built the cluster')
    parser.add_argument('--region_name', default='us-central1', type=str,
                        help='Name of the region where the cluster was built')
    parser.add_argument('--zone_name', default='us-central1-c', type=str,
                        help='Name of the zone where the cluster was built')
    parser.add_argument('--expiration_time', default=24, type=int, help='Expiration time of the cluster in hours')
    parser.add_argument('--helm_installs', default='', type=str, help='Helm installation to run post deployment')
    args = parser.parse_args()
    main(cluster_type=args.cluster_type, project_id=args.project_id, user_name=args.user_name,
         cluster_name=args.cluster_name,
         region_name=args.region_name, zone_name=args.zone_name, expiration_time=args.expiration_time,
         helm_installs=args.helm_installs,
         resource_group=args.resource_group)
