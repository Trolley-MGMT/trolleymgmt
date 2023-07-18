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
    confirmation_url: str
    registration_status: str
    user_type: str
    profile_image_filename: str
    availability: bool
    created_timestamp: int
    profile_image_id: ObjectId = ObjectId()


@dataclass
class ProviderObject:
    provider: str
    aws_access_key_id: bytes
    aws_secret_access_key: bytes
    azure_credentials: bytes
    google_creds_json: bytes
    user_email: str
    created_timestamp: int


@dataclass
class GithubObject:
    github_actions_token: bytes
    github_repository: str
    user_email: str
    created_timestamp: int


@dataclass
class InfracostObject:
    infracost_token: bytes
    user_email: str
    created_timestamp: int


@dataclass
class GKEObject:
    cluster_name: str
    context_name: str
    user_name: str
    kubeconfig: bytes
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
    vCPU: int
    totalvCPU: int
    total_memory: str
    machine_type: str
    availability: bool = True


@dataclass
class GKEAutopilotObject:
    cluster_name: str
    context_name: str
    user_name: str
    kubeconfig: bytes
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
    kubeconfig: bytes
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
    vCPU: int
    totalvCPU: int
    total_memory: str
    machine_type: str
    availability: bool = True


@dataclass
class AKSObject:
    az_resource_group: str
    cluster_name: str
    context_name: str
    user_name: str
    kubeconfig: bytes
    nodes_names: list
    nodes_ips: list
    created_timestamp: int
    human_created_timestamp: str
    expiration_timestamp: int
    human_expiration_timestamp: str
    zone_name: str
    region_name: str
    cluster_version: str
    num_nodes: int
    vCPU: int
    totalvCPU: int
    total_memory: str
    availability: bool = True


@dataclass
class EKSMachineTypeObject:
    machine_type: str
    vCPU: int
    memory: int


@dataclass
class GKECacheObject:
    zones_list: list
    regions_list: list
    gke_image_types: list
    regions_zones_dict: dict


@dataclass
class GKEMachinesCacheObject:
    region: str
    machines_list: list


@dataclass
class GKEMachineTypeObject:
    zone: str
    machine_series: str
    machine_type: str
    vCPU: int
    memory: int
    unit_price: float


@dataclass
class AZMachineTypeObject:
    location_name: str
    machine_type: str
    machine_series: str
    vCPU: int
    memory: int
    unit_price: float


@dataclass
class AZMachinesCacheObject:
    location_name: str
    machines_list: list


@dataclass
class AKSKubernetesVersionsCacheObject:
    location_name: str
    kubernetes_versions_list: list


@dataclass
class GKEKubernetesVersionsCacheObject:
    region_name: str
    kubernetes_versions_list: list


@dataclass
class GKESeriesAndMachineTypesObject:
    machine_series: str
    machines_list: list


@dataclass
class GKEZonesAndMachineSeriesObject:
    zone: str
    series_list: list


@dataclass
class GKEMachinesSeriesObject:
    zone: str
    machines_series_list: list


@dataclass
class AWSCacheObject:
    zones_list: list
    regions_list: list
    subnets_dict: dict
    regions_zones_dict: dict


@dataclass
class AWSMachinesCacheObject:
    region: str
    machines_list: list


@dataclass
class AWSMachineTypeObject:
    region: str
    machine_series: str
    machine_type: str
    vCPU: int
    memory: int
    unit_price: float


@dataclass
class AWSRegionsAndMachineSeriesObject:
    region: str
    series_list: list


@dataclass
class AWSSeriesAndMachineTypesObject:
    machine_series: str
    machines_list: list


@dataclass
class EKSCTLMetadataObject:
    name: str
    region: str


@dataclass
class EKSCTLNodeGroupObject:
    name: str
    instanceType: str
    desiredCapacity: int
    volumeSize: int


@dataclass
class EKSCTLObject:
    apiVersion: str
    kind: str
    metadata: EKSCTLMetadataObject
    nodeGroups: [EKSCTLNodeGroupObject]


@dataclass
class AZLocationsCacheObject:
    locations_dict: dict


@dataclass
class AZResourceGroupObject:
    location_name: str
    resource_groups_list: list


@dataclass
class AZZonesAndMachineSeriesObject:
    location_name: str
    series_list: list


@dataclass
class AZSeriesAndMachineTypesObject:
    machine_series: str
    machines_list: list


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
    machine_type: str
    internal_ip: str
    external_ip: str
    instance_zone: str
    client_name: str
    user_name: str
    availability: bool
    tags: dict


@dataclass
class AWSEC2InstanceDataObject:
    timestamp: int
    account_id: int
    instance_name: str
    machine_type: str
    instance_id: str
    instance_zone: str
    client_name: str
    user_name: str
    availability: bool
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
