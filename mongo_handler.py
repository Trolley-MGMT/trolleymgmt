import configparser
import os
import platform

from pymongo import MongoClient
from pymongo.collection import Collection
from variables import GKE, MACOS, GKE_AUTOPILOT, CLUSTER_NAME, AVAILABILITY, EKS, AKS

CUR_DIR = os.getcwd()
print(f'Current directory is: {CUR_DIR}')
PROJECT_ROOT = "/".join(CUR_DIR.split('/'))
print(f'Project root is: {PROJECT_ROOT}')
config = configparser.ConfigParser()
if MACOS in platform.platform():
    config.read(f'{PROJECT_ROOT}/config.ini')
else:
    config.read(f'{CUR_DIR}/config.ini')

JENKINS_URL = config['DEFAULT']['jenkins_url']
PROJECT_NAME = config['DEFAULT']['project_id']
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_USER = os.getenv('MONGO_USER')


client = MongoClient(JENKINS_URL, connect=False, username=MONGO_USER, password=MONGO_PASSWORD)
db = client[PROJECT_NAME]
gke_clusters: Collection = db.gke_clusters
gke_autopilot_clusters: Collection = db.gke_autopilot_clusters
eks_clusters: Collection = db.eks_clusters
aks_clusters: Collection = db.aks_clusters
users: Collection = db.users


def insert_gke_deployment(cluster_type: str = '', gke_deployment_object: dict = None) -> bool:
    """
    @param cluster_type: The type of the cluster we want to add to the DB. Ex: GKE/GKE Autopilot
    @param gke_deployment_object: The dictionary with all the cluster data.
    """
    if cluster_type == GKE:
        try:
            gke_clusters.insert_one(gke_deployment_object)
            return True
        except:
            print('failure to insert data into gke_clusters table')
            return False
    elif cluster_type == GKE_AUTOPILOT:
        try:
            gke_autopilot_clusters.insert_one(gke_deployment_object)
            return True
        except:
            print('failure to insert data into gke_autopilot_clusters table')
            return False


def insert_eks_deployment(eks_deployment_object: dict = None) -> bool:
    """
    @param eks_deployment_object: The dictionary with all the cluster data.
    @param cluster_type: The type of the cluster we want to add to the DB. Ex: EKS
    """
    eks_clusters.insert_one(eks_deployment_object)
    return True


def insert_aks_deployment(aks_deployment_object: dict = None) -> bool:
    """
    @param aks_deployment_object: The dictionary with all the cluster data.
    @param cluster_type: The type of the cluster we want to add to the DB. Ex: AKS
    """
    aks_clusters.insert_one(aks_deployment_object)
    return True


def set_cluster_availability(cluster_type: str = '', cluster_name: str = '', availability: bool = False):
    """

    @param cluster_type:
    @param cluster_name:
    @param availability:
    @return:
    """

    myquery = {CLUSTER_NAME.lower(): cluster_name}
    newvalues = {"$set": {AVAILABILITY: availability}}
    if cluster_type == GKE:
        result = gke_clusters.update_one(myquery, newvalues)
    elif cluster_type == GKE_AUTOPILOT:
        result = gke_autopilot_clusters.update_one(myquery, newvalues)
    elif cluster_type == EKS:
        result = eks_clusters.update_one(myquery, newvalues)
    elif cluster_type == AKS:
        result = aks_clusters.update_one(myquery, newvalues)
    else:
        result = gke_clusters.update_one(myquery, newvalues)
    return result.raw_result['updatedExisting']