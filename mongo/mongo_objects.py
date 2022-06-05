from dataclasses import dataclass


@dataclass
class UserObject:
    first_name: str
    last_name: str
    user_name: str
    hashed_password: str
    team_name: str
    user_email: str


@dataclass
class GKEObject:
    cluster_name: str
    username: str
    kubeconfig: str
    nodes_names: list
    nodes_ips: list
    jenkins_build_url: str
    created_timestamp: int
    human_created_timestamp: str
    expiration_timestamp: int
    human_expiration_timestamp: str
    project_id: str
    zone_name: str
    cluster_version: str
    region_name: str
    availability: bool = True


@dataclass
class GKEAutopilotObject:
    cluster_name: str
    username: str
    kubeconfig: str
    nodes_names: list
    nodes_ips: list
    jenkins_build_url: str
    created_timestamp: int
    human_created_timestamp: str
    expiration_timestamp: int
    human_expiration_timestamp: str
    project_id: str
    zone_name: str
    cluster_version: str
    region_name: str
    availability: bool = True


@dataclass
class EKSObject:
    cluster_name: str
    username: str
    kubeconfig: str
    nodes_names: list
    nodes_ips: list
    jenkins_build_url: str
    created_timestamp: int
    human_created_timestamp: str
    expiration_timestamp: int
    human_expiration_timestamp: str
    project_id: str
    zone_name: str
    cluster_version: str
    availability: bool = True


@dataclass
class AKSObject:
    cluster_name: str
    username: str
    kubeconfig: str
    nodes_names: list
    nodes_ips: list
    resource_group: str
    jenkins_build_url: str
    created_timestamp: int
    human_created_timestamp: str
    expiration_timestamp: int
    human_expiration_timestamp: str
    zone_name: str
    cluster_version: str
    availability: bool = True
