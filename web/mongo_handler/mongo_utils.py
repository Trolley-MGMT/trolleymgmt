import logging
import os
import platform
import time

import gridfs
from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('../mongo_utils.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# horrible hack to solve the Dockerfile issues. Please find a better solution
run_env = 'not_github'
try:
    github_env_something = os.getenv('GITHUB_ENV')
    if github_env_something is not None:
        run_env = 'github'
        logger.info('this runs on github')
    else:
        logger.error('this does not run on github')
except:
    run_env = 'not github'
    logger.info('this does not run on github')

if 'Darwin' in platform.system() or run_env == 'github':
    from web.variables.variables import GKE, GKE_AUTOPILOT, CLUSTER_NAME, AVAILABILITY, EKS, AKS, EXPIRATION_TIMESTAMP, \
        USER_NAME, USER_EMAIL, HELM, CLUSTER_TYPE
else:
    from variables.variables import GKE, GKE_AUTOPILOT, CLUSTER_NAME, AVAILABILITY, EKS, AKS, EXPIRATION_TIMESTAMP, \
        USER_NAME, USER_EMAIL, HELM

MONGO_URL = os.environ['MONGO_URL']
PROJECT_NAME = os.environ.get('PROJECT_NAME', 'trolley')
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']
MONGO_USER = os.environ['MONGO_USER']

client = MongoClient(MONGO_URL, connect=False, username=MONGO_USER, password=MONGO_PASSWORD)
db = client[PROJECT_NAME]
logger.info(db.list_collection_names())
gke_clusters: Collection = db.gke_clusters
gke_autopilot_clusters: Collection = db.gke_autopilot_clusters
eks_clusters: Collection = db.eks_clusters
aks_clusters: Collection = db.aks_clusters
users: Collection = db.users
deployment_yamls: Collection = db.deployment_yamls
aks_cache: Collection = db.aks_cache
gke_cache: Collection = db.gke_cache
helm_cache: Collection = db.helm_cache
eks_cache: Collection = db.eks_cache

aks_discovery: Collection = db.aks_discovery
gke_discovery: Collection = db.gke_discovery
eks_discovery: Collection = db.eks_discovery

fs = gridfs.GridFS(db)

agents_data: Collection = db.agents_data
providers_data: Collection = db.providers_data

logger.info(f'MONGO_USER is: {MONGO_USER}')
logger.info(f'MONGO_URL is: {MONGO_URL}')
logger.info(f'PROJECT_NAME is: {PROJECT_NAME}')


def insert_gke_deployment(cluster_type: str = '', gke_deployment_object: dict = None) -> bool:
    """
    @param cluster_type: The type of the cluster we want to add to the DB. Ex: GKE/GKE Autopilot
    @param gke_deployment_object: The dictionary with all the cluster data.
    """
    if cluster_type == GKE:
        try:
            mongo_response = gke_clusters.insert_one(gke_deployment_object)
            logger.info(mongo_response.acknowledged)
            logger.info(f'Inserted ID for Mongo DB is: {mongo_response.inserted_id}')
            return True
        except:
            logger.error('failure to insert data into gke_clusters table')
            return False
    elif cluster_type == GKE_AUTOPILOT:
        try:
            gke_autopilot_clusters.insert_one(gke_deployment_object)
            return True
        except:
            logger.error('failure to insert data into gke_autopilot_clusters table')
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
    logger.info(f'A request to fetch {cluster_type} clusters for {user_name} was received')
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
    logger.info(f'A request to fetch {cluster_name} details was received')
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


def retrieve_agent_cluster_details(cluster_name: str) -> dict:
    logger.info(f'A request to fetch {cluster_name} details was received')
    cluster_object = agents_data.find_one({CLUSTER_NAME.lower(): cluster_name})
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
            logger.info(expired_clusters_list)
    elif cluster_type == GKE_AUTOPILOT:
        autopilot_clusters_objects = gke_autopilot_clusters.find(mongo_query)
        for object in autopilot_clusters_objects:
            expired_clusters_list.append(object)
            logger.info(expired_clusters_list)
    elif cluster_type == EKS:
        eks_clusters_objects = eks_clusters.find(mongo_query)
        for object in eks_clusters_objects:
            expired_clusters_list.append(object)
            logger.info(expired_clusters_list)
    elif cluster_type == AKS:
        aks_clusters_objects = aks_clusters.find(mongo_query)
        for object in aks_clusters_objects:
            expired_clusters_list.append(object)
            logger.info(expired_clusters_list)
    return expired_clusters_list


def insert_cache_object(caching_object: dict = None, provider: str = None) -> bool:
    """
    @param caching_object: The dictionary with all the cluster data.
    @param provider: The dictionary with all the cluster data.
    """
    if provider == GKE:
        gke_cache.drop()
        try:
            mongo_response = gke_cache.insert_one(caching_object)
            logger.info(mongo_response.acknowledged)
            logger.info(f'Inserted ID for Mongo DB is: {mongo_response.inserted_id}')
            return True
        except:
            logger.error('failure to insert data into gke_cache table')
            return False
    elif provider == EKS:
        eks_cache.drop()
        try:
            mongo_response = eks_cache.insert_one(caching_object)
            logger.info(mongo_response.acknowledged)
            logger.info(f'Inserted ID for Mongo DB is: {mongo_response.inserted_id}')
            return True
        except:
            logger.error('failure to insert data into eks_cache table')
            return False
    elif provider == AKS:
        aks_cache.drop()
        try:
            mongo_response = aks_cache.insert_one(caching_object)
            logger.info(mongo_response.acknowledged)
            logger.info(f'Inserted ID for Mongo DB is: {mongo_response.inserted_id}')
            return True
        except:
            logger.error('failure to insert data into aks_cache table')
            return False
    elif provider == HELM:
        helm_cache.drop()
        try:
            mongo_response = helm_cache.insert_one(caching_object)
            logger.info(mongo_response.acknowledged)
            logger.info(f'Inserted ID for Mongo DB is: {mongo_response.inserted_id}')
            return True
        except:
            logger.error('failure to insert data into helm_cache table')
            return False


def insert_discovery_object(discovery_object: dict = None, provider: str = None) -> bool:
    """
    @param discovery_object: The dictionary with all the discovered clusters' data.
    @param provider: The dictionary with all the cluster data.
    """
    if provider == GKE:
        gke_discovery.drop()
        try:
            mongo_response = gke_discovery.insert_one(discovery_object)
            logger.info(mongo_response.acknowledged)
            logger.info(f'Inserted ID for Mongo DB is: {mongo_response.inserted_id}')
            return True
        except:
            logger.error('failure to insert data into gke_cache table')
            return False
    elif provider == EKS:
        eks_discovery.drop()
        try:
            mongo_response = eks_discovery.insert_one(discovery_object)
            logger.info(mongo_response.acknowledged)
            logger.info(f'Inserted ID for Mongo DB is: {mongo_response.inserted_id}')
            return True
        except:
            logger.error('failure to insert data into eks_cache table')
            return False
    elif provider == AKS:
        aks_discovery.drop()
        try:
            mongo_response = aks_discovery.insert_one(discovery_object)
            logger.info(mongo_response.acknowledged)
            logger.info(f'Inserted ID for Mongo DB is: {mongo_response.inserted_id}')
            return True
        except:
            logger.error('failure to insert data into aks_cache table')
            return False


def retrieve_cache(cache_type: str = '', provider: str = '') -> dict:
    if provider == GKE:
        cache_object = gke_cache.find()[0]
    elif provider == EKS:
        cache_object = eks_cache.find()[0]
    elif provider == AKS:
        cache_object = aks_cache.find()[0]
    elif provider == HELM:
        return helm_cache.find()[0]['helms_installs']
    else:
        cache_object = gke_cache.find()[0]
    return cache_object[cache_type]


def retrieve_user(user_email: str):
    """
    @param user_email:  retrieve a returning user data
    @return:
    """
    mongo_query = {USER_EMAIL: user_email}
    user_object = users.find_one(mongo_query)
    logger.info(f'found user_object is: {user_object}')
    if not user_object:
        return None
    try:
        profile_image_id = user_object['profile_image_id']
        file = fs.find_one({"_id": profile_image_id})
        user_object['profile_image'] = file
    except:
        logger.error(f'There was a problem here')
    return user_object


def retrieve_deployment_yaml(cluster_type: str, cluster_name: str) -> dict:
    """
    @param cluster_type:
    @param cluster_name:
    @return:
    """
    mongo_query = {CLUSTER_TYPE: cluster_type, CLUSTER_NAME.lower(): cluster_name}
    deployment_yaml_object = deployment_yamls.find_one(mongo_query)
    logger.info(f'found user_object is: {deployment_yaml_object}')
    if not deployment_yaml_object:
        return {}
    else:
        return deployment_yaml_object['deployment_yaml_dict']


def remove_deployment_yaml(cluster_type: str, cluster_name: str) -> bool:
    """
    @param cluster_type:
    @param cluster_name:
    @return:
    """
    mongo_query = {CLUSTER_TYPE: cluster_type, CLUSTER_NAME.lower(): cluster_name}
    deployment_yaml_object = deployment_yamls.delete_one(mongo_query)
    logger.info(f'found user_object is: {deployment_yaml_object}')
    if not deployment_yaml_object:
        return False
    else:
        return True


def insert_user(user_object: dict = None) -> bool:
    """
    @param user_object: The dictionary with all the user data.
    """
    users.insert_one(user_object)
    return True


def insert_file(profile_image_filename: str = '') -> ObjectId:
    """
    @param profile_image_filename: The filename of the image to save
    """
    with open(profile_image_filename, 'rb') as f:
        contents = f.read()

    return fs.put(contents, filename=profile_image_filename)


def insert_deployment_yaml(deployment_yaml_object: dict):
    try:
        deployment_yamls.insert_one(deployment_yaml_object)
        return True
    except:
        return False


def insert_agents_data_object(agents_data_object: dict) -> bool:
    """
    @param agents_data_object: The filename of the image to save
    """
    try:
        mongo_query = {CLUSTER_NAME.lower(): agents_data_object[CLUSTER_NAME.lower()]}
        existing_agents_data_object = agents_data.find_one(mongo_query)
        if existing_agents_data_object:
            result = agents_data.replace_one(existing_agents_data_object, agents_data_object)
            logger.info(f'agents_data_object was updated properly')
            return result.raw_result['updatedExisting']
        else:
            result = agents_data.insert_one(agents_data_object)
            if result.inserted_id:
                logger.info(f'agents_data_object was inserted properly')
                return True
            else:
                logger.error(f'agents_data_object was not inserted properly')
                return False
    except:
        logger.error(f'agents_data_object was not inserted properly')


def add_providers_data_object(providers_data_object: dict) -> bool:
    """
    @param providers_data_object: The filename of the image to save
    """
    try:
        mongo_query = {'provider': providers_data_object['provider']}
        existing_providers_data_object = providers_data.find_one(mongo_query)
        if existing_providers_data_object:
            result = providers_data.replace_one(existing_providers_data_object, providers_data_object)
            logger.info(f'agents_data_object was updated properly')
            return result.raw_result['updatedExisting']
        else:
            result = providers_data.insert_one(providers_data_object)
            if result.inserted_id:
                logger.info(f'provider was inserted properly')
                return True
            else:
                logger.error(f'provider was not inserted properly')
                return False
    except:
        logger.error(f'provider data was not inserted properly')
