from argparse import ArgumentParser, RawDescriptionHelpFormatter
import datetime
import getpass as gt
import logging
import os
import platform
from subprocess import run, PIPE
import sys
import time

import boto3

from agents.trolley_server.server_handler import ServerRequest
from web.mongo_handler.mongo_objects import AWSEC2DataObject, AWSS3FilesObject, AWSS3BucketsObject, AWSEKSDataObject, \
    AWSObject
from web.variables.variables import AWS

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
EC2_CLIENT = boto3.client('ec2')
S3_CLIENT = boto3.client('s3')
EKS_CLIENT = boto3.client('eks')
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


def fetch_buckets():
    response = S3_CLIENT.list_buckets()
    buckets_list = []
    for bucket in response['Buckets']:
        buckets_list.append(bucket["Name"])
    return AWSS3BucketsObject(timestamp=TS, account_id=ACCOUNT_ID,
                              buckets=buckets_list)


def fetch_files():
    response = S3_CLIENT.list_buckets()
    buckets_list = []
    for bucket in response['Buckets']:
        buckets_list.append(bucket["Name"])

    files_list = []
    for bucket in buckets_list:
        for key in S3_CLIENT.list_objects(Bucket=bucket)['Contents']:
            file_object = {
                key['Key']: {'size': key['Size'], 'owner': key['Owner']['DisplayName'],
                             'bucket': bucket, 'last_modified': int(key['LastModified'].timestamp())}}
            files_list.append(file_object)
    return AWSS3FilesObject(timestamp=TS, account_id=ACCOUNT_ID,
                            files=files_list)


def fetch_ec2_instances():
    instances_object = []
    aws_regions = fetch_regions()
    for aws_region in aws_regions:
        ecs_resource = boto3.resource('ec2', region_name=aws_region)
        if len(list(ecs_resource.instances.all())) > 0:
            for instance in ecs_resource.instances.all():
                if instance.state['Name'] == 'running':
                    instance_object = {
                        instance.tags[0]['Value']: {'instance_id': instance.id, 'instance_type': instance.instance_type,
                                                    'aws_region': aws_region, 'instance_tags': instance.tags}}
                    instances_object.append(instance_object)
    return AWSEC2DataObject(timestamp=TS, account_id=ACCOUNT_ID,
                            ec2_instances=instances_object)


def fetch_eks_clusters():
    aws_regions = fetch_regions()
    eks_clusters_object = []
    eks_clusters_names = []
    cluster_object = {}
    for aws_region in aws_regions:
        eks_client = boto3.client('eks', region_name=aws_region)
        response = eks_client.list_clusters()
        if len(response['clusters']) > 0:
            for cluster in response['clusters']:
                eks_clusters_names.append(cluster)
            for cluster_name in eks_clusters_names:
                cluster_data = eks_client.describe_cluster(name=cluster_name)
                cluster_object['user_name'] = 'vacant'
                cluster_object['created_timestamp'] = int(cluster_data['cluster']['createdAt'].timestamp())
                cluster_object['human_created_timestamp'] = cluster_data['cluster']['createdAt'].strftime(
                    '%d-%m-%Y %H:%M:%S')
                cluster_object['expiration_timestamp'] = TS_IN_20_YEARS
                cluster_object['human_expiration_timestamp'] = datetime.datetime.fromtimestamp(TS_IN_20_YEARS).strftime(
                    '%d-%m-%Y %H:%M:%S')
                cluster_object['kubernetes_version'] = cluster_data['cluster']['version']
                cluster_object['region'] = cluster_data['cluster']['arn'].split(":")[3]
                cluster_object['tags'] = cluster_data['cluster']['tags']
                cluster_object['availability'] = True
                cluster_object['kubeconfig'] = generate_kubeconfig(cluster_name=cluster_name, cluster_region=aws_region)
                cluster_object['nodes_names'] = []
                cluster_object['nodes_ips'] = []
                eks_clusters_object.append(cluster_object)
    return AWSEKSDataObject(timestamp=TS, account_id=ACCOUNT_ID,
                            eks_clusters=eks_clusters_object)


def main(fetch_interval: int = 30, server_url: str = '', is_fetching_files: bool = False,
         is_fetching_buckets: bool = False, is_fetching_ec2_instances: bool = False,
         is_fetching_eks_clusters: bool = False):
    if is_fetching_eks_clusters:
        aws_eks_data_object = fetch_eks_clusters()
    else:
        aws_eks_data_object = {}
    if is_fetching_files:
        aws_files_data_object = fetch_files()
    else:
        aws_files_data_object = {}
    if is_fetching_buckets:
        aws_buckets_data_object = fetch_buckets()
    else:
        aws_buckets_data_object = {}
    if is_fetching_ec2_instances:
        aws_instances_data_object = fetch_ec2_instances()
    else:
        aws_instances_data_object = {}

    aws_data_object = AWSObject(ec2Object=aws_instances_data_object, s3FilesObject=aws_files_data_object,
                                s3BucketsObject=aws_buckets_data_object,
                                eksObject=aws_eks_data_object, agent_type=AWS)
    server_request = ServerRequest(agent_data=aws_data_object, operation='insert_agent_data',
                                   server_url=server_url)
    server_request.send_server_request()
    logging.info(f'Taking a {fetch_interval} sleep time between fetches')
    time.sleep(fetch_interval)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--fetch-files', action='store_true', help='Fetch files or not')
    parser.add_argument('--fetch-buckets', action='store_true', help='Fetch buckets or not')
    parser.add_argument('--fetch-ec2-instances', action='store_true', help='Fetch EC2 instances or not')
    parser.add_argument('--fetch-eks-clusters', action='store_true', help='Fetch EKS clusters or not')
    args = parser.parse_args()
    while True:
        main(is_fetching_files=args.fetch_files, is_fetching_buckets=args.fetch_buckets,
             is_fetching_ec2_instances=args.fetch_ec2_instances, is_fetching_eks_clusters=args.fetch_eks_clusters)
