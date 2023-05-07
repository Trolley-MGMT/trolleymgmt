from argparse import ArgumentParser, RawDescriptionHelpFormatter
import datetime
import getpass as gt
import logging
import os
import platform
from dataclasses import asdict
from subprocess import run, PIPE
import sys
import time

import boto3

from web.mongo_handler.mongo_objects import AWSS3FilesObject, AWSS3BucketsObject, \
    AWSEC2InstanceDataObject

from web.mongo_handler.mongo_utils import insert_aws_instances_object, insert_aws_files_object, \
    insert_aws_buckets_object, insert_eks_cluster_object, retrieve_instances, retrieve_available_clusters, \
    retrieve_compute_per_machine_type
# from web.variables.variables import AWS, EKS

file_name = 'server.log'
log_file_path = f'{os.getcwd()}/{file_name}'


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(sys.stdout)
    ]
)
FETCH_INTERVAL = int(os.environ.get('FETCH_INTERVAL', "30"))
DEFAULT_AWS_REGION = os.environ.get('DEFAULT_AWS_REGION', "us-east-1")
EC2_CLIENT = boto3.client('ec2', region_name=DEFAULT_AWS_REGION)
S3_CLIENT = boto3.client('s3')
EKS_CLIENT = boto3.client('eks', region_name=DEFAULT_AWS_REGION)
ACCOUNT_ID = int(boto3.client('sts').get_caller_identity().get('Account'))
TS = int(time.time())
TS_IN_20_YEARS = TS + 60 * 60 * 24 * 365 * 20
LOCAL_USER = gt.getuser()
if 'Darwin' in platform.system():
    KUBECONFIG_PATH = f'/Users/{LOCAL_USER}/.kube/config'  # path to the GCP credentials
else:
    KUBECONFIG_PATH = '/root/.kube/config'


def generate_kubeconfig(cluster_name: str, cluster_region: str) -> str:
    kubeconfig_generate_command = f'aws eks --region {cluster_region} update-kubeconfig --name {cluster_name}'
    run(kubeconfig_generate_command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    with open(KUBECONFIG_PATH, "r") as f:
        kubeconfig = f.read()
        logging.info(f'The kubeconfig content is: {kubeconfig}')
        return kubeconfig


def fetch_regions() -> list:
    response = EC2_CLIENT.describe_regions()
    regions_list = []
    for region_response in response['Regions']:
        regions_list.append(region_response['RegionName'])
    logging.info(f'The fetched list of regions is: {regions_list}')
    return regions_list


def fetch_buckets() -> AWSS3BucketsObject:
    response = S3_CLIENT.list_buckets()
    buckets_list = []
    for bucket in response['Buckets']:
        buckets_list.append(bucket["Name"])
    return AWSS3BucketsObject(timestamp=TS, account_id=ACCOUNT_ID,
                              buckets=buckets_list)


def fetch_files(aws_buckets: AWSS3BucketsObject) -> AWSS3FilesObject:
    aws_buckets_list = []
    aws_files_dict = {}
    for aws_bucket in aws_buckets.buckets:
        aws_buckets_list.append(aws_bucket)
    files_list = []
    for bucket in aws_buckets_list:
        for file in S3_CLIENT.list_objects(Bucket=bucket)['Contents']:
            file_object = {
                file['Key']: {'size': file['Size'], 'owner': file['Owner']['DisplayName'],
                              'last_modified': int(file['LastModified'].timestamp())}}
            files_list.append(file_object)
        aws_files_dict[bucket] = files_list
        files_list = []
    return AWSS3FilesObject(timestamp=TS, account_id=ACCOUNT_ID,
                            files=aws_files_dict)


def list_all_instances():
    instances_object = []
    aws_regions = fetch_regions()
    for aws_region in aws_regions:
        ecs_resource = boto3.resource('ec2', region_name=aws_region)
        if len(list(ecs_resource.instances.all())) > 0:
            for instance in ecs_resource.instances.all():
                if instance.state['Name'] == 'running':
                    instance_name = ''
                    tags = {}
                    for i, tag in enumerate(instance.tags):
                        if tag['Key'] == 'Name':
                            instance_name = tag['Value']
                        key = instance.tags[i]['Key'].lower()
                        value = instance.tags[i]['Value'].lower()
                        tags[key] = value
                    aws_ec2_instance = AWSEC2InstanceDataObject(timestamp=TS, account_id=ACCOUNT_ID,
                                                                instance_id=instance.id,
                                                                instance_name=instance_name,
                                                                internal_ip=instance.network_interfaces[
                                                                    0].private_ip_address,
                                                                external_ip=instance.network_interfaces[
                                                                    0].private_ip_address,
                                                                instance_zone=aws_region, machine_type=instance.instance_type,
                                                                tags=tags, client_name='vacant', user_name='vacant', availability=True)
                    instances_object.append(aws_ec2_instance)
    return instances_object


def fetch_eks_clusters() -> list:
    aws_regions = fetch_regions()
    eks_clusters_object = []
    eks_clusters_names = []
    for aws_region in aws_regions:
        eks_client = boto3.client('eks', region_name=aws_region)
        response = eks_client.list_clusters()
        if len(response['clusters']) > 0:
            for cluster in response['clusters']:
                eks_clusters_names.append(cluster)
            for cluster_name in eks_clusters_names:
                cluster_object = {}
                cluster_data = eks_client.describe_cluster(name=cluster_name)
                if cluster_data['cluster']['status'] == 'ACTIVE':
                    response = eks_client.list_nodegroups(clusterName=cluster_name)
                    machine_types = []
                    totalVCPU = 0
                    totalNodes = 0
                    machines_list = []
                    for node_group in response['nodegroups']:
                        node_groups_response = eks_client.describe_nodegroup(clusterName=cluster_name,
                                                                             nodegroupName=node_group)
                        machines_amount = node_groups_response['nodegroup']['scalingConfig']['desiredSize']
                        totalNodes += machines_amount
                        machine_type = node_groups_response['nodegroup']['instanceTypes'][0]
                        machines_list.append(machine_type)
                        vCPU = retrieve_compute_per_machine_type('eks', machine_type)['vCPU']
                        machine_types.append({'machine_type': machine_type,
                                              'machines_amount': machines_amount,
                                              'vCPU': vCPU
                                              })
                        for machine_type_ in machine_types:
                            totalVCPU += machine_type_['vCPU']
                    cluster_object['vCPU'] = totalVCPU
                    cluster_object['num_nodes'] = totalNodes
                    cluster_object['machine_type'] = machines_list
                    cluster_object['cluster_name'] = cluster_name
                    cluster_object['user_name'] = 'vacant'
                    cluster_object['created_timestamp'] = int(cluster_data['cluster']['createdAt'].timestamp())
                    cluster_object['human_created_timestamp'] = cluster_data['cluster']['createdAt'].strftime(
                        '%d-%m-%Y %H:%M:%S')
                    cluster_object['expiration_timestamp'] = TS_IN_20_YEARS
                    cluster_object['human_expiration_timestamp'] = datetime.datetime.fromtimestamp(
                        TS_IN_20_YEARS).strftime(
                        '%d-%m-%Y %H:%M:%S')
                    cluster_object['cluster_version'] = cluster_data['cluster']['version']
                    cluster_object['region_name'] = cluster_data['cluster']['arn'].split(":")[3]
                    cluster_object['tags'] = cluster_data['cluster']['tags']
                    cluster_object['availability'] = True
                    cluster_object['kubeconfig'] = generate_kubeconfig(cluster_name=cluster_name,
                                                                       cluster_region=aws_region)
                    cluster_object['nodes_names'] = []
                    cluster_object['nodes_ips'] = []
                    eks_clusters_object.append(cluster_object)
    return eks_clusters_object


def main(is_fetching_files: bool = False, is_fetching_buckets: bool = False, is_fetching_ec2_instances: bool = False,
         is_fetching_eks_clusters: bool = False):
    global aws_buckets_data_object
    if is_fetching_eks_clusters:
        already_discovered_clusters_to_test = []
        discovered_clusters_to_add = []

        already_discovered_eks_clusters = retrieve_available_clusters('eks')
        eks_discovered_clusters = fetch_eks_clusters()

        for already_discovered_cluster in already_discovered_eks_clusters:
            already_discovered_clusters_to_test.append(already_discovered_cluster['cluster_name'])

        for eks_discovered_cluster in eks_discovered_clusters:
            if eks_discovered_cluster['cluster_name'] not in already_discovered_clusters_to_test:
                discovered_clusters_to_add.append(eks_discovered_cluster)

        print('List of discovered EKS clusters: ')
        print(eks_discovered_clusters)
        for eks_discovered_cluster in eks_discovered_clusters:
            insert_eks_cluster_object(eks_discovered_cluster)
    if is_fetching_ec2_instances:
        already_discovered_vm_instances_to_test = []
        discovered_vm_instances_to_add = []

        already_discovered_vm_instances = retrieve_instances('aws')
        aws_discovered_vm_instances_object = list_all_instances()

        for already_discovered_vm in already_discovered_vm_instances:
            already_discovered_vm_instances_to_test.append(already_discovered_vm['instance_name'])

        for aws_discovered_vm_instance in aws_discovered_vm_instances_object:
            if aws_discovered_vm_instance.instance_name not in already_discovered_vm_instances_to_test:
                discovered_vm_instances_to_add.append(aws_discovered_vm_instance)

        print('List of discovered EC2 instances: ')
        print(discovered_vm_instances_to_add)
        insert_aws_instances_object(discovered_vm_instances_to_add)
    if is_fetching_buckets:
        aws_buckets_data_object = fetch_buckets()
        print('List of discovered S3 buckets: ')
        print(asdict(aws_buckets_data_object))
        insert_aws_buckets_object(asdict(aws_buckets_data_object))
    if is_fetching_files:
        aws_files_data_object = fetch_files(aws_buckets_data_object)
        print('List of discovered S3 files: ')
        print(asdict(aws_files_data_object))
        insert_aws_files_object(asdict(aws_files_data_object))


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--fetch-files', action='store_true', default=True, help='Fetch files or not')
    parser.add_argument('--fetch-buckets', action='store_true', default=True, help='Fetch buckets or not')
    parser.add_argument('--fetch-ec2-instances', action='store_true', default=True, help='Fetch EC2 instances or not')
    parser.add_argument('--fetch-eks-clusters', action='store_true', default=True, help='Fetch EKS clusters or not')
    args = parser.parse_args()
    main(is_fetching_files=args.fetch_files, is_fetching_buckets=args.fetch_buckets,
         is_fetching_ec2_instances=args.fetch_ec2_instances, is_fetching_eks_clusters=args.fetch_eks_clusters)
