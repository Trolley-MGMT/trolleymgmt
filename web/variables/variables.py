import sys

sys.path.append("../")

# OS
MACOS = 'macOS'

# verbs
DELETE = 'DELETE'
PUT = 'PUT'
GET = 'GET'
POST = 'POST'

OK = 'OK'
FAILURE = 'Failure'

#object types
OBJECT_TYPE = 'object_type'
CLUSTER = 'cluster'
INSTANCE = 'instance'
FILE = 'file'
BUCKET = 'bucket'

# providers
PROVIDER = 'provider'
AWS = 'aws'
GCP = 'gcp'
AZ = 'azure'

# GKE
CLUSTER_TYPE = 'cluster_type'
GKE = 'gke'
GKE_AUTOPILOT = 'gke_autopilot'
TROLLEY_PROJECT_NAME = 'trolley'


# GENERAL
HELM = 'helm'
HELM_INSTALLS = 'HELM_INSTALLS'
PROJECT_NAME = 'PROJECT_NAME'
CLUSTER_NAME = 'CLUSTER_NAME'
INSTANCE_NAME = 'INSTANCE_NAME'
CLIENT_NAME = 'CLIENT_NAME'
ACCOUNT_ID = 'ACCOUNT_ID'
CLUSTER_VERSION = 'CLUSTER_VERSION'
NUM_NODES = 'NUM_NODES'
EXPIRATION_TIME = 'EXPIRATION_TIME'
ZONE_NAME = 'ZONE_NAME'
IMAGE_TYPE = 'IMAGE_TYPE'
REGION_NAME = 'REGION_NAME'
REGION_ZONE = 'REGION_ZONE'
APPLICATION_JSON = 'application/json'
AVAILABILITY = 'availability'
EXPIRATION_TIMESTAMP = 'expiration_timestamp'
CREATED_TIMESTAMP = 'created_timestamp'
HUMAN_CREATED_TIMESTAMP = 'human_created_timestamp'
HUMAN_EXPIRATION_TIMESTAMP = 'human_expiration_timestamp'
KUBECONFIG = 'kubeconfig'
NODES_NAMES = 'nodes_names'
JENKINS_BUILD_URL = 'jenkins_build_url'
NODES_IPS = 'nodes_IPs'
PROJECT_NAME = 'project_name'
RESOURCE_GROUP = 'resource_group'
PROJECT_ID = 'project_id'
CLUSTER_DEPLOYMENT_YAML = 'cluster_deployment_yaml'
#  USER
USER_NAME = 'USER_NAME'
USER_ID = 'USER_ID'
USER_EMAIL = 'user_email'
FIRST_NAME = 'first_name'
LAST_NAME = 'last_name'
HASHED_PASSWORD = 'hashed_password'
TEAM_NAME = 'team_name'


# EKS
VERSION = 'version'
EKS = 'eks'
EKS_LOCATION = 'eks_location'
EKS_ZONES = 'eks_zones'

# AKS
AKS_VERSION = 'AKS_VERSION'
AKS_LOCATION = 'AKS_LOCATION'
AKS = 'aks'

# CACHE TYPES
REGIONS_LIST = 'regions_list'
LOCATIONS_DICT = 'locations_dict'
LOCATIONS_LIST = 'locations_list'
ZONES_LIST = 'zones_list'
HELM_INSTALLS_LIST = 'helm_installs_list'
GKE_VERSIONS_LIST = 'versions_list'
GKE_IMAGE_TYPES = 'gke_image_types'
