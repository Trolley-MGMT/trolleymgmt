import logging
import os
import platform

import getpass as gt
import sys

import boto3
from botocore.client import BaseClient
from dotenv import load_dotenv

project_folder_ = os.path.expanduser(os.getcwd())
project_folder = "/".join(project_folder_.split('/')[:-2])
load_dotenv(os.path.join(project_folder, '.env'))

from web.scripts.aws_caching_script import fetch_zones, fetch_regions, fetch_subnets

LOCAL_USER = gt.getuser()
GITHUB_ACTIONS_ENV = os.getenv('GITHUB_ACTIONS_ENV')

log_file_name = 'server.log'
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
LOCAL_AWS_CREDENTIALS_PATH = f'/Users/{LOCAL_USER}/.aws/credentials'



def get_aws_credentials(request) -> tuple:
    try:
        aws_access_key_id = request.config.getoption("--aws-access-key-id")
        aws_secret_access_key = request.config.getoption("--aws-secret-access-key")
        return aws_access_key_id, aws_secret_access_key
    except Exception as e:
        logger.warning(f'aws_access_key_id was not passed: {e}')
    if 'Darwin' in platform.system():
        try:
            with open(LOCAL_AWS_CREDENTIALS_PATH, "r") as f:
                aws_credentials = f.read()
                aws_access_key_id = aws_credentials.split('\n')[1].split(" = ")[1]
                aws_secret_access_key = aws_credentials.split('\n')[2].split(" = ")[1]
                return aws_access_key_id, aws_secret_access_key
        except Exception as e:
            logger.error(f'AWS credentials were not found with error: {e}')



def get_ec2(aws_access_key_id, aws_secret_access_key) -> BaseClient:
    try:
        ec2 = boto3.client('ec2', region_name='us-east-1',
                           aws_access_key_id=aws_access_key_id,
                           aws_secret_access_key=aws_secret_access_key)
        logger.info('Success connecting to AWS')
        return ec2
    except Exception as e:
        logger.error(f'Trouble connecting to AWS: {e}')


def test_fetch_regions(request):
    aws_access_key_id, aws_secret_access_key = get_aws_credentials(request)
    ec2 = get_ec2(aws_access_key_id, aws_secret_access_key)
    regions_list = fetch_regions(ec2)
    assert isinstance(regions_list, list)
    assert len(regions_list) > 0


def test_fetch_zones(request):
    aws_access_key_id, aws_secret_access_key = get_aws_credentials(request)
    ec2 = get_ec2(aws_access_key_id, aws_secret_access_key)
    zones_list = fetch_zones(ec2, aws_access_key_id, aws_secret_access_key)
    assert isinstance(zones_list, list)
    assert len(zones_list) > 0

def test_fetch_subnets(request):
    aws_access_key_id, aws_secret_access_key = get_aws_credentials(request)
    ec2 = get_ec2(aws_access_key_id, aws_secret_access_key)
    zones_list = fetch_zones(ec2, aws_access_key_id, aws_secret_access_key)
    subnets_dict = fetch_subnets(zones_list, ec2)
    assert isinstance(subnets_dict, dict)
    assert len(subnets_dict) > 0