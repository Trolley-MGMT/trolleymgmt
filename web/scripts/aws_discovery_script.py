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

from web.mongo_handler.mongo_objects import AWSEC2DataObject, AWSS3FilesObject, AWSS3BucketsObject

from web.mongo_handler.mongo_utils import insert_aws_instances_object, insert_aws_files_object, \
    insert_aws_buckets_object, insert_eks_cluster_object

if 'macOS' in platform.platform():
    log_path = f'{os.getcwd()}'
else:
    log_path = '/var/log/'
file_name = 'aws_agent_main.log'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"{log_path}/{file_name}"),
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
                cluster_object['cluster_name'] = cluster_name
                cluster_object['user_name'] = 'vacant'
                cluster_object['created_timestamp'] = int(cluster_data['cluster']['createdAt'].timestamp())
                cluster_object['human_created_timestamp'] = cluster_data['cluster']['createdAt'].strftime(
                    '%d-%m-%Y %H:%M:%S')
                cluster_object['expiration_timestamp'] = TS_IN_20_YEARS
                cluster_object['human_expiration_timestamp'] = datetime.datetime.fromtimestamp(TS_IN_20_YEARS).strftime(
                    '%d-%m-%Y %H:%M:%S')
                cluster_object['cluster_version'] = cluster_data['cluster']['version']
                cluster_object['region_name'] = cluster_data['cluster']['arn'].split(":")[3]
                cluster_object['tags'] = cluster_data['cluster']['tags']
                cluster_object['availability'] = True
                cluster_object['kubeconfig'] = generate_kubeconfig(cluster_name=cluster_name, cluster_region=aws_region)
                cluster_object['nodes_names'] = []
                cluster_object['nodes_ips'] = []
                eks_clusters_object.append(cluster_object)
    return eks_clusters_object


def main(is_fetching_files: bool = False, is_fetching_buckets: bool = False, is_fetching_ec2_instances: bool = False,
         is_fetching_eks_clusters: bool = False):
    if is_fetching_eks_clusters:
        aws_discovered_clusters = fetch_eks_clusters()
        for aws_discovered_cluster in aws_discovered_clusters:
            insert_eks_cluster_object(aws_discovered_cluster)
    if is_fetching_files:
        aws_files_data_object = fetch_files()
        print(asdict(aws_files_data_object))
        insert_aws_files_object(asdict(aws_files_data_object))
    if is_fetching_buckets:
        aws_buckets_data_object = fetch_buckets()
        print(asdict(aws_buckets_data_object))
        insert_aws_buckets_object(asdict(aws_buckets_data_object))
    if is_fetching_ec2_instances:
        aws_instances_data_object = fetch_ec2_instances()
        print(asdict(aws_instances_data_object))
        insert_aws_instances_object(asdict(aws_instances_data_object))


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--fetch-files', action='store_true', default=True, help='Fetch files or not')
    parser.add_argument('--fetch-buckets', action='store_true', default=True, help='Fetch buckets or not')
    parser.add_argument('--fetch-ec2-instances', action='store_true', default=True, help='Fetch EC2 instances or not')
    parser.add_argument('--fetch-eks-clusters', action='store_true', default=True, help='Fetch EKS clusters or not')
    args = parser.parse_args()
    main(is_fetching_files=args.fetch_files, is_fetching_buckets=args.fetch_buckets,
         is_fetching_ec2_instances=args.fetch_ec2_instances, is_fetching_eks_clusters=args.fetch_eks_clusters)
