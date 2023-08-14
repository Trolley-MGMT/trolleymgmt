import getpass
import json
import logging
import os
import platform
import sys
from dataclasses import asdict

import requests
from dotenv import load_dotenv

DOCKER_ENV = os.getenv('DOCKER_ENV', False)
GITHUB_ENV = os.getenv('GITHUB_ENV', False)

if GITHUB_ENV:
    from web.variables.variables import GKE, ZONE_NAME, EKS, REGION_NAME, PROJECT_NAME
    from web.mongo_handler.mongo_utils import retrieve_cluster_details
    from web.mongo_handler.mongo_objects import EKSCTLNodeGroupObject, EKSCTLObject, EKSCTLMetadataObject
else:
    from variables.variables import GKE, ZONE_NAME, EKS, REGION_NAME, PROJECT_NAME
    from mongo_handler.mongo_utils import retrieve_cluster_details
    from mongo_handler.mongo_objects import EKSCTLNodeGroupObject, EKSCTLObject, EKSCTLMetadataObject

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

project_folder = os.path.expanduser(os.getcwd())
load_dotenv(os.path.join(project_folder, '.env'))

# horrible hack to solve the Dockerfile issues. Please find a better solution
run_env = 'not_github'
try:
    github_env_something = os.getenv('GITHUB_ENV')
    if github_env_something is not None:
        run_env = 'github'
        logger.info('this runs on github')
    else:
        logger.info('this does not run on github')
except:
    run_env = 'not github'
    logger.info('this does not run on github')

if 'Darwin' in platform.system() or run_env == 'github':
    AWS_CREDENTIALS_PATH = f'/Users/{getpass.getuser()}/.aws/credentials'
else:
    AWS_CREDENTIALS_PATH = '/home/app/.aws/credentials'


class ClusterOperation:
    def __init__(self, provider: str = "", user_email: str = "", secret_key: str = "", github_actions_token: str = "",
                 github_repository: str = "", infracost_token: str = "", user_name: str = "", project_name: str = "",
                 cluster_name: str = "",
                 cluster_type: str = "", cluster_version: str = "", az_location_name: str = "",
                 az_resource_group: str = "", az_subscription_id: str = "", az_machine_type: str = "",
                 region_name: str = "", zone_name: str = "", gcp_project_id: str = "", gke_machine_type: str = "",
                 gke_region: str = "", gke_zone: str = "", eks_machine_type: str = "",
                 eks_volume_size: int = "",
                 eks_location: str = "", eks_zones: str = "", num_nodes: int = "", image_type: str = "",
                 expiration_time: int = 0, discovered: bool = False, mongo_url: str = "",
                 mongo_password: str = "", mongo_user: str = "", trolley_server_url: str = "",
                 aws_access_key_id: str = "", aws_secret_access_key: str = "", google_creds_json: str = "",
                 azure_credentials: str = ""):
        self.secret_key = secret_key
        self.mongo_url = mongo_url
        self.mongo_password = mongo_password
        self.mongo_user = mongo_user
        self.trolley_server_url = trolley_server_url
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.google_creds_json = google_creds_json
        self.azure_credentials = azure_credentials
        self.cluster_name = cluster_name
        self.user_name = user_name
        self.project_name = project_name
        self.github_actions_token = github_actions_token
        self.github_repository = github_repository
        self.infracost_token = infracost_token
        self.cluster_type = cluster_type
        self.cluster_version = cluster_version
        self.az_location_name = az_location_name
        self.az_resource_group = az_resource_group
        self.az_subscription_id = az_subscription_id
        self.az_machine_type = az_machine_type
        self.region_name = region_name
        self.zone_name = zone_name
        self.eks_machine_type = eks_machine_type
        self.eks_volume_size = eks_volume_size
        self.gcp_project_id = gcp_project_id
        self.gke_machine_type = gke_machine_type
        self.gke_region = gke_region
        self.gke_zone = gke_zone
        self.eks_zones = eks_zones
        self.eks_location = eks_location
        self.num_nodes = num_nodes
        self.image_type = image_type
        self.expiration_time = expiration_time
        self.discovered = discovered
        self.eksctl_object_dict = {}

        self.github_action_request_header = {
            'Content-type': 'application/json',
            'Accept': 'application/vnd.github+json',
            'Authorization': f'token {self.github_actions_token}'
        }
        self.infracost_request_header = {
            'X-Api-Key': self.infracost_token,
            'Content-Type': 'application/json',
        }

        self.github_actions_api_url = f'https://api.github.com/repos/{self.github_repository}/dispatches'
        self.github_test_url = f'https://api.github.com/repos/{self.github_repository}'
        self.infracost_test_url = f'https://pricing.api.infracost.io/graphql'
        self.infracost_test_json_data = {
            'query': '{ products(filter: {vendorName: "aws", service: "AmazonEC2", region: "us-east-1", attributeFilters: [{key: "instanceType", value: "m3.large"}, {key: "operatingSystem", value: "Linux"}, {key: "tenancy", value: "Shared"}, {key: "capacitystatus", value: "Used"}, {key: "preInstalledSw", value: "NA"}]}) { prices(filter: {purchaseOption: "on_demand"}) { USD } } } ',
        }

    def build_eksctl_object(self):
        eksctl_node_groups_object = EKSCTLNodeGroupObject(name='ng1', instanceType=self.eks_machine_type,
                                                          desiredCapacity=int(self.num_nodes),
                                                          volumeSize=int(self.eks_volume_size))
        eksctl_metadata = EKSCTLMetadataObject(name=self.cluster_name, region=self.eks_location,
                                               version=float(self.cluster_version))
        metadata: EKSCTLMetadataObject
        node_groups: [EKSCTLNodeGroupObject]
        eksctl_object = EKSCTLObject(apiVersion="eksctl.io/v1alpha5", kind="ClusterConfig", metadata=eksctl_metadata,
                                     nodeGroups=[eksctl_node_groups_object])
        self.eksctl_object_dict = asdict(eksctl_object)

    def get_aws_credentials(self) -> tuple:
        if self.aws_access_key_id and self.aws_secret_access_key:
            return self.aws_access_key_id, self.aws_secret_access_key
        else:
            try:
                with open(AWS_CREDENTIALS_PATH, "r") as f:
                    aws_credentials = f.read()
                    aws_access_key_id = aws_credentials.split('\n')[1].split(" = ")[1]
                    aws_secret_access_key = aws_credentials.split('\n')[2].split(" = ")[1]
                    return aws_access_key_id, aws_secret_access_key
            except Exception as e:
                logger.warning('AWS credentials were not found')

    def github_check(self) -> bool:
        response = requests.get(url=self.github_test_url,
                                headers=self.github_action_request_header)
        if response.status_code == 200:
            return True
        else:
            logger.error(f'GitHub credentials check failed due to the following reason: {response.reason}')
            return False

    def infracost_check(self) -> bool:
        response = requests.post(url=self.infracost_test_url,
                                 headers=self.infracost_request_header,
                                 json=self.infracost_test_json_data)
        if response.status_code == 200:
            return True
        else:
            error_response = response.json()['error']
            logger.error(
                f'Infracost credentials check failed due to the following reason: {response.reason} : {error_response}')
            return False

    def trigger_gke_build_github_action(self) -> bool:
        encoded_data = {
            "secret_key": self.secret_key,
            "gcp_project_id": self.gcp_project_id,
            "project_name": self.project_name,
            "mongo_url": self.mongo_url,
            "mongo_user": self.mongo_user,
            "mongo_password": self.mongo_password,
            "cluster_name": self.cluster_name,
            "user_name": self.user_name,
            "cluster_version": self.cluster_version,
            "gke_machine_type": self.gke_machine_type,
            "region_name": self.gke_region,
            "zone_name": self.gke_zone,
            "image_type": self.image_type,
            "num_nodes": str(self.num_nodes),
            "expiration_time": self.expiration_time
        }
        json_data = {
            "event_type": "gke-build-api-trigger",
            "client_payload": {
                "google_creds_json": self.google_creds_json,
                "payload": str(encoded_data)
            }
        }
        response = requests.post(self.github_actions_api_url,
                                 headers=self.github_action_request_header, json=json_data)
        logger.info(f'This is the request response: {response}')
        if response.status_code == 200 or response.status_code == 204:
            return True
        else:
            logger.warning(f'This is the request response: {response.reason}')
            return False

    def trigger_eks_build_github_action(self) -> bool:
        aws_access_key_id, aws_secret_access_key = self.get_aws_credentials()
        encoded_data = {
            "secret_key": self.secret_key,
            "cluster_name": self.cluster_name,
            "mongo_url": self.mongo_url,
            "mongo_user": self.mongo_user,
            "mongo_password": self.mongo_password,
            "project_name": self.project_name,
            "user_name": self.user_name,
            "cluster_version": self.cluster_version,
            "region_name": self.eks_location,
            "num_nodes": str(self.num_nodes),
            "expiration_time": self.expiration_time,
            "eksctl_deployment_file": self.eksctl_object_dict
        }
        json_data = {
            "event_type": "eks-build-api-trigger",
            "client_payload": {
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key,
                "payload": str(encoded_data)
            }
        }
        response = requests.post(self.github_actions_api_url,
                                 headers=self.github_action_request_header, json=json_data)
        logger.info(f'This is the request response: {response}')
        if response.status_code == 200 or response.status_code == 204:
            return True
        else:
            logger.warning(f'This is the request response: {response.reason}')
            return False

    def trigger_aks_build_github_action(self) -> bool:
        encoded_data = {
            "secret_key": self.secret_key,
            "mongo_url": self.mongo_url,
            "mongo_user": self.mongo_user,
            "mongo_password": self.mongo_password,
            "cluster_name": self.cluster_name,
            "az_machine_type": self.az_machine_type,
            "project_name": self.project_name,
            "user_name": self.user_name,
            "cluster_version": self.cluster_version,
            "az_location_name": self.az_location_name,
            "az_resource_group": self.az_resource_group,
            "az_subscription_id": self.az_subscription_id,
            "num_nodes": str(self.num_nodes),
            "expiration_time": self.expiration_time,
        }
        json_data = {
            "event_type": "aks-build-api-trigger",
            "client_payload": {"azure_credentials": self.azure_credentials,
                               "payload": str(encoded_data)}
        }
        response = requests.post(self.github_actions_api_url,
                                 headers=self.github_action_request_header, json=json_data)
        logger.info(f'This is the request response: {response}')
        if response.status_code == 200 or response.status_code == 204:
            return True
        else:
            logger.warning(f'This is the request response: {response.reason}')
            return False

    def trigger_trolley_agent_deployment_github_action(self):
        json_data = {
            "event_type": "trolley-agent-api-deployment-trigger",
            "client_payload": {"cluster_name": self.cluster_name,
                               "google_creds_json": self.google_creds_json,
                               "cluster_type": self.cluster_type,
                               "zone_name": self.zone_name,
                               "trolley_server_url": self.trolley_server_url,
                               "mongo_user": self.mongo_user,
                               "mongo_password": self.mongo_password,
                               "mongo_url": self.mongo_url}
        }
        response = requests.post(self.github_actions_api_url,
                                 headers=self.github_action_request_header, json=json_data)

        return response

    def trigger_gcp_caching(self):
        if self.infracost_token:
            event_type = "gcp-caching-action-infracost-trigger"
        else:
            event_type = "gcp-caching-action-trigger"
        json_data = {
            "event_type": event_type,
            "client_payload": {"project_name": self.project_name,
                               "google_creds_json": self.google_creds_json,
                               "infracost_token": self.infracost_token,
                               "mongo_user": self.mongo_user,
                               "mongo_password": self.mongo_password,
                               "mongo_url": self.mongo_url}
        }
        response = requests.post(self.github_actions_api_url,
                                 headers=self.github_action_request_header, json=json_data)
        logger.info(f'trigger_gcp_caching request returned with response: {response}')
        if response.status_code == 204:
            return True
        else:
            return False

    def trigger_aws_caching(self):
        if self.infracost_token:
            event_type = "aws-caching-action-infracost-trigger"
        else:
            event_type = "aws-caching-action-trigger"
        json_data = {
            "event_type": event_type,
            "client_payload": {"project_name": self.project_name,
                               "aws_access_key_id": self.aws_access_key_id,
                               "aws_secret_access_key": self.aws_secret_access_key,
                               "infracost_token": self.infracost_token,
                               "mongo_user": self.mongo_user,
                               "mongo_password": self.mongo_password,
                               "mongo_url": self.mongo_url}
        }
        response = requests.post(self.github_actions_api_url,
                                 headers=self.github_action_request_header, json=json_data)

        logger.info(f'trigger_aws_caching request returned with response: {response}')
        if response.status_code == 204:
            return True
        else:
            return False

    def trigger_az_caching(self):
        client_id = json.loads(self.azure_credentials)['clientId']
        client_secret = json.loads(self.azure_credentials)['clientSecret']
        tenant_id = json.loads(self.azure_credentials)['tenantId']
        if self.infracost_token:
            event_type = "az-caching-action-infracost-trigger"
        else:
            event_type = "az-caching-action-trigger"
        json_data = {
            "event_type": event_type,
            "client_payload": {"azure_credentials": self.azure_credentials,
                               "infracost_token": self.infracost_token,
                               "client_id": client_id,
                               "client_secret": client_secret,
                               "tenant_id": tenant_id,
                               "project_name": self.project_name,
                               "mongo_user": self.mongo_user,
                               "mongo_password": self.mongo_password,
                               "mongo_url": self.mongo_url}
        }
        response = requests.post(self.github_actions_api_url,
                                 headers=self.github_action_request_header, json=json_data)

        logger.info(f'trigger_az_caching request returned with response: {response}')
        if response.status_code == 204:
            return True
        else:
            return False

    def delete_aks_cluster(self):
        json_data = {
            "event_type": "aks-delete-api-trigger",
            "client_payload": {
                "azure_credentials": self.azure_credentials,
                "project_name": self.project_name,
                "discovered": str(self.discovered),
                "cluster_name": self.cluster_name,
                "mongo_user": self.mongo_user,
                "mongo_password": self.mongo_password,
                "mongo_url": self.mongo_url,
                "az_subscription_id": self.az_subscription_id,
                "az_resource_group": self.az_resource_group,
            }
        }
        response = requests.post(self.github_actions_api_url,
                                 headers=self.github_action_request_header, json=json_data)
        logger.info(f'This is the request response: {response}')
        if response.status_code == 200 or response.status_code == 204:
            return True
        else:
            logger.warning(f'This is the request response: {response.reason}')
            return False

    def delete_gke_cluster(self):
        gke_cluster_details = retrieve_cluster_details(cluster_type=GKE, cluster_name=self.cluster_name,
                                                       discovered=self.discovered)
        gke_zone_name = gke_cluster_details[ZONE_NAME.lower()]
        print(f'Attempting to delete {self.cluster_name} in {gke_zone_name}')
        json_data = {
            "event_type": "gke-delete-api-trigger",
            "client_payload": {"cluster_name": self.cluster_name,
                               "discovered": self.discovered,
                               "zone_name": gke_zone_name,
                               "project_name": self.project_name,
                               "google_creds_json": self.google_creds_json,
                               "mongo_user": self.mongo_user,
                               "mongo_password": self.mongo_password,
                               "mongo_url": self.mongo_url
                               }
        }
        response = requests.post(self.github_actions_api_url,
                                 headers=self.github_action_request_header, json=json_data)
        logger.info(f'This is the request response: {response}')
        if response.status_code == 200 or response.status_code == 204:
            return True
        else:
            logger.warning(f'This is the request response: {response.reason}')
            return False

    def delete_eks_cluster(self):
        eks_cluster_details = retrieve_cluster_details(cluster_type=EKS, cluster_name=self.cluster_name,
                                                       discovered=self.discovered)
        eks_cluster_region_name = eks_cluster_details[REGION_NAME.lower()]
        aws_access_key_id, aws_secret_access_key = self.get_aws_credentials()
        json_data = {
            "event_type": "eks-delete-api-trigger",
            "client_payload":
                {"cluster_name": self.cluster_name,
                 "discovered": self.discovered,
                 "project_name": self.project_name,
                 "region_name": eks_cluster_region_name,
                 "aws_access_key_id": aws_access_key_id,
                 "aws_secret_access_key": aws_secret_access_key,
                 "mongo_user": self.mongo_user,
                 "mongo_password": self.mongo_password,
                 "mongo_url": self.mongo_url
                 }
        }
        response = requests.post(self.github_actions_api_url,
                                 headers=self.github_action_request_header, json=json_data)
        logger.info(f'This is the request response: {response}')
        if response.status_code == 200 or response.status_code == 204:
            return True
        else:
            logger.warning(f'This is the request response: {response.reason}')
            return False
