import os
import time

from pymongo import MongoClient
from pymongo.collection import Collection

from variables.variables import GKE, GKE_AUTOPILOT, CLUSTER_NAME, AVAILABILITY, EKS, AKS, EXPIRATION_TIMESTAMP, \
    USER_NAME, \
    USER_EMAIL

MONGO_URL = os.environ['MONGO_URL']
PROJECT_NAME = os.environ['PROJECT_NAME']
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']
MONGO_USER = os.environ['MONGO_USER']

client = MongoClient(MONGO_URL, connect=False, username=MONGO_USER, password=MONGO_PASSWORD)
db = client[PROJECT_NAME]
print(db.list_collection_names())
gke_clusters: Collection = db.gke_clusters
gke_autopilot_clusters: Collection = db.gke_autopilot_clusters
eks_clusters: Collection = db.eks_clusters
aks_clusters: Collection = db.aks_clusters
users: Collection = db.users
gke_cache: Collection = db.gke_cache

print(f'MONGO_USER is: {MONGO_USER}')
print(f'MONGO_PASSWORD is: {MONGO_PASSWORD}')
print(f'MONGO_URL is: {MONGO_URL}')
print(f'PROJECT_NAME is: {PROJECT_NAME}')


def insert_gke_deployment(cluster_type: str = '', gke_deployment_object: dict = None) -> bool:
    """
    @param cluster_type: The type of the cluster we want to add to the DB. Ex: GKE/GKE Autopilot
    @param gke_deployment_object: The dictionary with all the cluster data.
    """
    if cluster_type == GKE:
        try:
            mongo_response = gke_clusters.insert_one(gke_deployment_object)
            print(mongo_response.acknowledged)
            print(f'Inserted ID for Mongo DB is: {mongo_response.inserted_id}')
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

    @param cluster_type: The type of the cluster to change the availability of
    @param cluster_name: The name of the cluster to set the availability of
    @param availability: Availability True/False
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
        cluster_object = gke_clusters.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
    elif cluster_type == GKE_AUTOPILOT:
        cluster_object = gke_autopilot_clusters.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
    elif cluster_type == EKS:
        cluster_object = eks_clusters.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
    elif cluster_type == AKS:
        cluster_object = aks_clusters.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
    else:
        cluster_object = []
    for cluster in cluster_object:
        del cluster['_id']
        clusters_object.append(cluster)
    return clusters_object


def retrieve_cluster_details(cluster_type: str, cluster_name: str) -> dict:
    print(f'A request to fetch {cluster_type} details was received')
    if cluster_type == GKE:
        cluster_object = gke_clusters.find_one({CLUSTER_NAME.lower(): cluster_name})
    elif cluster_type == GKE_AUTOPILOT:
        cluster_object = gke_autopilot_clusters.find_one({CLUSTER_NAME.lower(): cluster_name})
    elif cluster_type == EKS:
        cluster_object = eks_clusters.find_one({CLUSTER_NAME.lower(): cluster_name})
    elif cluster_type == AKS:
        cluster_object = aks_clusters.find_one({CLUSTER_NAME.lower(): cluster_name})
    else:
        cluster_object = []
    del cluster_object['_id']
    return cluster_object


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


def insert_gke_cache(gke_caching_object: dict = None) -> bool:
    """
    @param gke_caching_object: The dictionary with all the cluster data.
    """
    gke_cache.drop()  # clear previous data in the collection
    try:
        mongo_response = gke_cache.insert_one(gke_caching_object)  # insert updated cache object
        print(mongo_response.acknowledged)
        print(f'Inserted ID for Mongo DB is: {mongo_response.inserted_id}')
        return True
    except:
        print('failure to insert data into gke_cache table')
        return False


def retrieve_gke_cache(gke_cache_type: str = '') -> dict:
    gke_cache_object = gke_cache.find()
    for object in gke_cache_object:
        return object[gke_cache_type]
        # if gke_cache_type == REGIONS_LIST:
        #     return object[REGIONS_LIST]
        # elif gke_cache_type == ZONES_LIST:
        #     return object[ZONES_LIST]
        # elif gke_cache_type == HELM_INSTALLS_LIST:
        #     return object[HELM_INSTALLS_LIST]
        # elif gke_cache_type == VERSIONS_LIST:
        #     return object[VER]
        # print(object)
    print(f'found user_object is: {gke_cache_object}')
    return gke_cache_object


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
