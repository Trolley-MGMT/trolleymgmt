from dataclasses import dataclass
from bson import ObjectId


@dataclass
class UserObject:
    first_name: str
    last_name: str
    user_name: str
    hashed_password: str
    team_name: str
    user_email: str
    profile_image_id: ObjectId = ObjectId()


@dataclass
class ProviderObject:
    provider: str
    aws_access_key_id: bytes
    aws_secret_access_key: bytes
    azure_credentials: bytes
    google_creds_json: bytes
    user_email: str


@dataclass
class GKEObject:
    cluster_name: str
    context_name: str
    user_name: str
    kubeconfig: str
    nodes_names: list
    nodes_ips: list
    created_timestamp: int
    human_created_timestamp: str
    expiration_timestamp: int
    human_expiration_timestamp: str
    project_name: str
    zone_name: str
    cluster_version: str
    runtime_version: str
    os_image: str
    region_name: str
    num_nodes: int
    availability: bool = True


@dataclass
class GKEAutopilotObject:
    cluster_name: str
    context_name: str
    user_name: str
    kubeconfig: str
    nodes_names: list
    nodes_ips: list
    created_timestamp: int
    human_created_timestamp: str
    expiration_timestamp: int
    human_expiration_timestamp: str
    project_name: str
    zone_name: str
    cluster_version: str
    region_name: str
    num_nodes: int
    availability: bool = True


@dataclass
class EKSObject:
    cluster_name: str
    context_name: str
    user_name: str
    kubeconfig: str
    nodes_names: list
    nodes_ips: list
    created_timestamp: int
    human_created_timestamp: str
    expiration_timestamp: int
    human_expiration_timestamp: str
    project_name: str
    zone_name: str
    region_name: str
    cluster_version: str
    num_nodes: int
    availability: bool = True


@dataclass
class AKSObject:
    cluster_name: str
    context_name: str
    user_name: str
    kubeconfig: str
    nodes_names: list
    nodes_ips: list
    resource_group: str
    created_timestamp: int
    human_created_timestamp: str
    expiration_timestamp: int
    human_expiration_timestamp: str
    zone_name: str
    region_name: str
    cluster_version: str
    num_nodes: int
    availability: bool = True


@dataclass
class GKEMachineTypeObject:
    machine_type: str
    vCPU: int
    memory: int


@dataclass
class EKSMachineTypeObject:
    machine_type: str
    vCPU: int
    memory: int


@dataclass
class GKECacheObject:
    zones_list: list
    regions_list: list
    versions_list: list
    gke_image_types: list
    regions_zones_dict: dict

@dataclass
class GKEMachinesCacheObject:
    region: str
    machines_list: list

@dataclass
class AWSCacheObject:
    zones_list: list
    regions_list: list
    subnets_dict: dict
    regions_zones_dict: dict
    machine_types_list: list


@dataclass
class AKSCacheObject:
    locations_dict: dict


@dataclass
class HelmCacheObject:
    helms_installs: list


@dataclass
class DeploymentYAMLObject:
    cluster_type: str
    cluster_name: str
    deployment_yaml_dict: dict


@dataclass
class NamespacesDataObject:
    namespaces: list


@dataclass
class DeploymentsDataObject:
    deployments: list


@dataclass
class PodsDataObject:
    pods: list


@dataclass
class ContainersDataObject:
    containers: list


@dataclass
class DaemonsetsDataObject:
    daemonsets: list


@dataclass
class StatefulSetsDataObject:
    statefulsets: list


@dataclass
class ServicesDataObject:
    services: list


@dataclass
class ClusterDataObject:
    timestamp: int
    agent_type: str
    cluster_name: str
    context_name: str
    namespaces: list
    deployments: list
    pods: list
    containers: list
    daemonsets: list
    stateful_sets: list
    services: list


@dataclass
class AWSEC2DataObject:
    timestamp: int
    account_id: int
    ec2_instances: list


@dataclass
class GCPInstanceDataObject:
    timestamp: int
    project_name: str
    instance_name: str
    internal_ip: str
    external_ip: str
    instance_type: str
    instance_zone: str
    client_name: str
    tags: dict


@dataclass
class AWSEC2InstanceDataObject:
    timestamp: int
    account_id: int
    instance_name: str
    instance_id: str
    instance_type: str
    instance_region: str
    client_name: str
    internal_ip: str
    external_ip: str
    tags: dict


@dataclass
class AWSS3FilesObject:
    timestamp: int
    account_id: int
    files: dict


@dataclass
class GCPFilesObject:
    timestamp: int
    project_name: int
    files: dict


@dataclass
class AWSS3BucketsObject:
    timestamp: int
    account_id: int
    buckets: list


@dataclass
class GCPBucketsObject:
    timestamp: int
    project_name: str
    buckets: list


@dataclass
class AWSEKSDataObject:
    timestamp: int
    account_id: int
    eks_clusters: list


@dataclass
class AWSObject:
    agent_type: str
    ec2Object: AWSEC2DataObject
    s3FilesObject: AWSS3FilesObject
    s3BucketsObject: AWSS3BucketsObject
    eksObject: AWSEKSDataObject
