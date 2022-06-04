
from variables import CLUSTER_NAME, USER_NAME, KUBECONFIG, NODES_NAMES, JENKINS_BUILD_URL, \
    CREATED_TIMESTAMP, HUMAN_CREATED_TIMESTAMP, EXPIRATION_TIMESTAMP, HUMAN_EXPIRATION_TIMESTAMP, PROJECT_ID, \
    CLUSTER_VERSION, AVAILABILITY, REGION_NAME, ZONE_NAME, NODES_IPS, PROJECT_NAME, RESOURCE_GROUP, HASHED_PASSWORD, \
    USER_EMAIL, TEAM_NAME, FIRST_NAME, LAST_NAME


class UserObject:
    def __init__(self, first_name: str = '', last_name: str = '', user_name: str = '', hashed_password: str = '',
                 team_name='', user_email: str = ''):
        self.first_name = first_name
        self.last_name = last_name
        self.user_name = user_name
        self.hashed_password = hashed_password
        self.team_name = team_name
        self.user_email = user_email

    def to_dict(self):
        user_object_dict = {
            FIRST_NAME: self.first_name,
            LAST_NAME: self.last_name,
            USER_NAME: self.user_name,
            HASHED_PASSWORD: self.hashed_password,
            TEAM_NAME: self.team_name,
            USER_EMAIL: self.user_email
        }
        return user_object_dict


class GKEObject:
    def __init__(self, cluster_name: str = '', username: str = '', kubeconfig: str = '',
                 nodes_names: list = None, nodes_ips: list = None, jenkins_build_url: str = '',
                 created_timestamp: int = 0,
                 human_created_timestamp: str = '', expiration_timestamp: int = 0, human_expiration_timestamp: str = '',
                 project_id: str = '', zone_name: str = '', cluster_version: str = '', availability: bool = True):
        self.cluster_name = cluster_name
        self.user_name = username
        self.kubeconfig = kubeconfig
        self.nodes_names = nodes_names
        self.nodes_ips = nodes_ips
        self.jenkins_build_url = jenkins_build_url
        self.created_timestamp = created_timestamp
        self.human_created_timestamp = human_created_timestamp
        self.expiration_timestamp = expiration_timestamp
        self.human_expiration_timestamp = human_expiration_timestamp
        self.project_id = project_id
        self.zone_name = zone_name
        self.cluster_version = cluster_version
        self.availability = availability

    def to_dict(self):
        gke_object_dict = {
            CLUSTER_NAME.lower(): self.cluster_name,
            USER_NAME: self.user_name,
            KUBECONFIG: self.kubeconfig,
            NODES_NAMES: self.nodes_names,
            NODES_IPS: self.nodes_ips,
            JENKINS_BUILD_URL: self.jenkins_build_url,
            CREATED_TIMESTAMP: self.created_timestamp,
            HUMAN_CREATED_TIMESTAMP: self.human_created_timestamp,
            EXPIRATION_TIMESTAMP: self.expiration_timestamp,
            HUMAN_EXPIRATION_TIMESTAMP: self.human_expiration_timestamp,
            PROJECT_ID: self.project_id,
            ZONE_NAME: self.zone_name,
            CLUSTER_VERSION.lower(): self.cluster_version,
            AVAILABILITY: self.availability
        }
        return gke_object_dict


class GKEAutopilotObject:
    def __init__(self, cluster_name: str = '', username: str = '', kubeconfig: str = '',
                 nodes_names: list = None, nodes_ips: list = None, jenkins_build_url: str = '',
                 created_timestamp: int = 0,
                 human_created_timestamp: str = '', expiration_timestamp: int = 0, human_expiration_timestamp: str = '',
                 project_id: str = '', zone_name: str = '', cluster_version: str = '', availability: bool = True,
                 region_name: str = ''):
        self.cluster_name = cluster_name
        self.user_name = username
        self.kubeconfig = kubeconfig
        self.nodes_names = nodes_names
        self.nodes_ips = nodes_ips
        self.jenkins_build_url = jenkins_build_url
        self.created_timestamp = created_timestamp
        self.human_created_timestamp = human_created_timestamp
        self.expiration_timestamp = expiration_timestamp
        self.human_expiration_timestamp = human_expiration_timestamp
        self.project_id = project_id
        self.zone_name = zone_name
        self.cluster_version = cluster_version
        self.availability = availability
        self.region_name = region_name

    def to_dict(self):
        gke_autopilot_object_dict = {
            CLUSTER_NAME.lower(): self.cluster_name,
            USER_NAME: self.user_name,
            KUBECONFIG: self.kubeconfig,
            NODES_NAMES: self.nodes_names,
            NODES_IPS: self.nodes_ips,
            JENKINS_BUILD_URL: self.jenkins_build_url,
            CREATED_TIMESTAMP: self.created_timestamp,
            HUMAN_CREATED_TIMESTAMP: self.human_created_timestamp,
            EXPIRATION_TIMESTAMP: self.expiration_timestamp,
            HUMAN_EXPIRATION_TIMESTAMP: self.human_expiration_timestamp,
            PROJECT_ID: self.project_id,
            ZONE_NAME: self.zone_name,
            CLUSTER_VERSION.lower(): self.cluster_version,
            AVAILABILITY: self.availability,
            REGION_NAME.lower(): self.region_name
        }
        return gke_autopilot_object_dict


class EKSObject:
    def __init__(self, cluster_name: str = '', username: str = '', kubeconfig: str = '',
                 nodes_names: list = None, nodes_ips: list = None, jenkins_build_url: str = '',
                 created_timestamp: int = 0,
                 human_created_timestamp: str = '', expiration_timestamp: int = 0, human_expiration_timestamp: str = '',
                 project_id: str = '', zone_name: str = '', cluster_version: str = '', availability: bool = True):
        self.cluster_name = cluster_name
        self.user_name = username
        self.kubeconfig = kubeconfig
        self.nodes_names = nodes_names
        self.nodes_ips = nodes_ips
        self.jenkins_build_url = jenkins_build_url
        self.created_timestamp = created_timestamp
        self.human_created_timestamp = human_created_timestamp
        self.expiration_timestamp = expiration_timestamp
        self.human_expiration_timestamp = human_expiration_timestamp
        self.project_id = project_id
        self.zone_name = zone_name
        self.cluster_version = cluster_version
        self.availability = availability

    def to_dict(self):
        eks_object_dict = {
            CLUSTER_NAME.lower(): self.cluster_name,
            USER_NAME: self.user_name,
            KUBECONFIG: self.kubeconfig,
            NODES_NAMES: self.nodes_names,
            NODES_IPS: self.nodes_ips,
            JENKINS_BUILD_URL: self.jenkins_build_url,
            CREATED_TIMESTAMP: self.created_timestamp,
            HUMAN_CREATED_TIMESTAMP: self.human_created_timestamp,
            EXPIRATION_TIMESTAMP: self.expiration_timestamp,
            HUMAN_EXPIRATION_TIMESTAMP: self.human_expiration_timestamp,
            PROJECT_ID: self.project_id,
            ZONE_NAME: self.zone_name,
            CLUSTER_VERSION.lower(): self.cluster_version,
            AVAILABILITY: self.availability
        }
        return eks_object_dict


class AKSObject:
    def __init__(self, cluster_name: str = '', user_name: str = '', kubeconfig: str = '', nodes_names: list = None,
                 nodes_ips: list = None,
                 jenkins_build_url: str = '', created_timestamp: int = 0, human_created_timestamp: str = '',
                 expiration_timestamp: int = 0, human_expiration_timestamp: str = '', project_id: str = '',
                 zone_name: str = '', cluster_version: str = '', availability: bool = True,
                 resource_group: str = ''):
        self.cluster_name = cluster_name
        self.kubeconfig = kubeconfig
        self.user_name = user_name
        self.nodes_names = nodes_names
        self.nodes_ips = nodes_ips
        self.jenkins_build_url = jenkins_build_url
        self.created_timestamp = created_timestamp
        self.human_created_timestamp = human_created_timestamp
        self.expiration_timestamp = expiration_timestamp
        self.human_expiration_timestamp = human_expiration_timestamp
        self.zone_name = zone_name
        self.cluster_version = cluster_version
        self.availability = availability
        self.resource_group = resource_group

    def to_dict(self):
        aks_object_dict = {
            CLUSTER_NAME.lower(): self.cluster_name,
            USER_NAME: self.user_name,
            KUBECONFIG: self.kubeconfig,
            NODES_NAMES: self.nodes_names,
            NODES_IPS: self.nodes_ips,
            JENKINS_BUILD_URL: self.jenkins_build_url,
            CREATED_TIMESTAMP: self.created_timestamp,
            HUMAN_CREATED_TIMESTAMP: self.human_created_timestamp,
            EXPIRATION_TIMESTAMP: self.expiration_timestamp,
            HUMAN_EXPIRATION_TIMESTAMP: self.human_expiration_timestamp,
            ZONE_NAME: self.zone_name,
            CLUSTER_VERSION.lower(): self.cluster_version,
            AVAILABILITY: self.availability,
            RESOURCE_GROUP: self.resource_group
        }
        return aks_object_dict