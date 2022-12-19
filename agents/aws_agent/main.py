import logging
import os
import sys
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import platform

import boto3

from agents.trolley_server.server_handler import ServerRequest
from web.mongo_handler.mongo_objects import AWSAgentsDataObject

if 'macOS' in platform.platform():
    log_path = f'{os.getcwd()}'
else:
    log_path = '/var/log/'
file_name = 'agent_main.log'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"{log_path}/{file_name}"),
        logging.StreamHandler(sys.stdout)
    ]
)
FETCH_INTERVAL = int(os.environ.get('FETCH_INTERVAL', "30"))
EC2_CLIENT = boto3.client('ec2')


def fetch_regions() -> list:
    response = EC2_CLIENT.describe_regions()
    regions_list = []
    for region_response in response['Regions']:
        regions_list.append(region_response['RegionName'])
    return regions_list


def main(fetch_interval: int = 30, server_url: str = ''):
    timestamp = int(time.time())
    account_id = boto3.client('sts').get_caller_identity().get('Account')
    instances_object = []
    aws_regions = fetch_regions()
    for aws_region in aws_regions:
        ecs_resource = boto3.resource('ec2', region_name=aws_region)
        if len(list(ecs_resource.instances.all())) > 0:
            for instance in ecs_resource.instances.all():
                instance_object = {
                    instance.tags[0]['Value']: {'instance_id': instance.id, 'instance_type': instance.instance_type,
                                                'aws_region': aws_region, 'instance_tags': instance.tags}}
                instances_object.append(instance_object)
    agents_data_object = AWSAgentsDataObject(timestamp=timestamp, account_id=account_id, agent_type='aws',
                                             ec3_instances=instances_object)
    server_request = ServerRequest(agent_data=agents_data_object, operation='insert_agent_data',
                                   server_url=server_url)
    server_request.send_server_request()
    logging.info(f'Taking a {fetch_interval} sleep time between fetches')
    time.sleep(fetch_interval)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    while True:
        main()
