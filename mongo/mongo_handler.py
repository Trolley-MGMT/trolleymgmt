import configparser
import os
import platform
import time

from pymongo import MongoClient
from pymongo.collection import Collection
from variables import GKE, MACOS, GKE_AUTOPILOT, CLUSTER_NAME, AVAILABILITY, EKS, AKS, EXPIRATION_TIMESTAMP, USER_NAME, \
    USER_EMAIL

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

print(f'MONGO_USER is: {MONGO_USER}')
print(f'MONGO_PASSWORD is: {MONGO_PASSWORD}')


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


def retrieve_available_clusters(cluster_type: str, user_name: str) -> list:
    print(f'A request to fetch {cluster_type} clusters for {user_name} was received')
    clusters_object = []
    if cluster_type == GKE:
        cluster_object = gke_clusters.find({AVAILABILITY: True, USER_NAME: user_name})
    elif cluster_type == GKE_AUTOPILOT:
        cluster_object = gke_autopilot_clusters.find({AVAILABILITY: True, USER_NAME: user_name})
    elif cluster_type == EKS:
        cluster_object = eks_clusters.find({AVAILABILITY: True, USER_NAME: user_name})
    elif cluster_type == AKS:
        cluster_object = aks_clusters.find({AVAILABILITY: True, USER_NAME: user_name})
    else:
        cluster_object = []
    for cluster in cluster_object:
        del cluster['_id']
        clusters_object.append(cluster)
    return clusters_object


def retrieve_expired_clusters(cluster_type: str) -> list:
    current_time = int(time.time())
    expired_clusters_list = []
    mongo_query = {"$and": [{EXPIRATION_TIMESTAMP: {"$lt": current_time}},
                            {AVAILABILITY: True}]}
    if cluster_type == GKE:
        clusters_objects = gke_clusters.find(mongo_query)
        for object in clusters_objects:
            expired_clusters_list.append(object)
            print(expired_clusters_list)
    elif cluster_type == GKE_AUTOPILOT:
        autopilot_clusters_objects = gke_autopilot_clusters.find(mongo_query)
        for object in autopilot_clusters_objects:
            expired_clusters_list.append(object)
            print(expired_clusters_list)
    elif cluster_type == EKS:
        eks_clusters_objects = eks_clusters.find(mongo_query)
        for object in eks_clusters_objects:
            expired_clusters_list.append(object)
            print(expired_clusters_list)
    elif cluster_type == AKS:
        aks_clusters_objects = aks_clusters.find(mongo_query)
        for object in aks_clusters_objects:
            expired_clusters_list.append(object)
            print(expired_clusters_list)
    return expired_clusters_list


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


def retrieve_user(user_email: str):
    """
    @param user_email:  retrieve a returning user data
    @return:
    """
    mongo_query = {USER_EMAIL: user_email}
    user_object = users.find_one(mongo_query)
    print(f'found user_object is: {user_object}')
    return user_object


def insert_user(user_object: dict = None) -> bool:
    """
    @param user_object: The dictionary with all the user data.
    """
    users.insert_one(user_object)
    return True
