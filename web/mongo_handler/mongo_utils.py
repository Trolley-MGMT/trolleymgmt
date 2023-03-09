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

handler = logging.FileHandler('mongo_utils.log')
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
        USER_NAME, USER_EMAIL, HELM, CLUSTER_TYPE, ACCOUNT_ID, CLIENT_NAME
else:
    from variables.variables import GKE, GKE_AUTOPILOT, CLUSTER_NAME, AVAILABILITY, EKS, AKS, EXPIRATION_TIMESTAMP, \
        USER_NAME, USER_EMAIL, HELM, ACCOUNT_ID

PROJECT_NAME = os.environ.get('PROJECT_NAME', 'trolley-361905')
GCP_PROJECT_NAME = os.environ.get('GCP_PROJECT_NAME', 'trolley-361905')

MONGO_PASSWORD = os.environ['MONGO_PASSWORD']
MONGO_USER = os.environ['MONGO_USER']
MONGO_URL = os.environ['MONGO_URL']
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))

if "mongodb.net" in MONGO_URL:
    client = MongoClient(f"mongodb+srv://admin:{MONGO_PASSWORD}@{MONGO_URL}/?retryWrites=true&w=majority")
else:
    client = MongoClient(host=MONGO_URL, port=MONGO_PORT, connect=False, username=MONGO_USER, password=MONGO_PASSWORD)
db = client[PROJECT_NAME]

gke_clusters: Collection = db.gke_clusters
gke_autopilot_clusters: Collection = db.gke_autopilot_clusters
eks_clusters: Collection = db.eks_clusters

aws_discovered_eks_clusters: Collection = db.aws_discovered_eks_clusters
aws_discovered_ec2_instances: Collection = db.aws_discovered_ec2_instances
aws_discovered_s3_files: Collection = db.aws_discovered_s3_files
aws_discovered_s3_buckets: Collection = db.aws_discovered_s3_buckets

gcp_discovered_gke_clusters: Collection = db.gcp_discovered_gke_clusters
gcp_discovered_vm_instances: Collection = db.gcp_discovered_vm_instances
gcp_discovered_buckets: Collection = db.gcp_discovered_buckets
gcp_discovered_files: Collection = db.gcp_discovered_files

aks_clusters: Collection = db.aks_clusters
users: Collection = db.users
deployment_yamls: Collection = db.deployment_yamls
aks_cache: Collection = db.aks_cache
gcp_cache: Collection = db.gcp_cache
helm_cache: Collection = db.helm_cache
aws_cache: Collection = db.aws_cache

aks_discovery: Collection = db.aks_discovery
gke_discovery: Collection = db.gke_discovery
eks_discovery: Collection = db.eks_discovery

fs = gridfs.GridFS(db)

k8s_agent_data: Collection = db.k8s_agent_data

providers_data: Collection = db.providers_data
clients_data: Collection = db.clients_data

logger.info(f'MONGO_USER is: {MONGO_USER}')
logger.info(f'MONGO_URL is: {MONGO_URL}')
logger.info(f'PROJECT_NAME is: {PROJECT_NAME}')
logger.info(f'Listing all the collections')
logger.info(db.list_collection_names())


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
    """
    aks_clusters.insert_one(aks_deployment_object)
    return True


def set_cluster_availability(cluster_type: str = '', cluster_name: str = '', discovered: bool = False,
                             availability: bool = False):
    """

    @param cluster_type: The type of the cluster to change the availability of
    @param cluster_name: The name of the cluster to set the availability of
    @param discovered: Whether the cluster was found out scanning the cloud provider or not
    @param availability: Availability True/False
    @return:
    """

    myquery = {CLUSTER_NAME.lower(): cluster_name}
    newvalues = {"$set": {AVAILABILITY: availability}}
    if cluster_type == GKE:
        if discovered:
            result = gcp_discovered_gke_clusters.update_one(myquery, newvalues)
        else:
            result = gke_clusters.update_one(myquery, newvalues)
    elif cluster_type == GKE_AUTOPILOT:
        result = gke_autopilot_clusters.update_one(myquery, newvalues)
    elif cluster_type == EKS:
        if discovered:
            result = aws_discovered_eks_clusters.update_one(myquery, newvalues)
        else:
            result = eks_clusters.update_one(myquery, newvalues)
    elif cluster_type == AKS:
        result = aks_clusters.update_one(myquery, newvalues)
    else:
        result = gke_clusters.update_one(myquery, newvalues)
    return result.raw_result['updatedExisting']


def retrieve_available_clusters(cluster_type: str, user_name: str) -> list:
    logger.info(f'A request to fetch {cluster_type} clusters for {user_name} was received')
    clusters_object = []
    discovered_clusters_object = []
    if cluster_type == GKE:
        cluster_object = gke_clusters.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
        discovered_clusters_object = gcp_discovered_gke_clusters.find({AVAILABILITY: True})
    elif cluster_type == GKE_AUTOPILOT:
        cluster_object = gke_autopilot_clusters.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
    elif cluster_type == EKS:
        cluster_object = eks_clusters.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
        discovered_clusters_object = aws_discovered_eks_clusters.find({AVAILABILITY: True})
    elif cluster_type == AKS:
        cluster_object = aks_clusters.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
    else:
        cluster_object = []
    for cluster in cluster_object:
        del cluster['_id']
        cluster['discovered'] = False
        clusters_object.append(cluster)
        if 'client_name' not in cluster.keys():
            cluster['client_name'] = ''
        if 'tags' not in cluster.keys():
            cluster['tags'] = []
    if discovered_clusters_object:
        for cluster in discovered_clusters_object:
            del cluster['_id']
            cluster['discovered'] = True
            clusters_object.append(cluster)
            if 'client_name' not in cluster.keys():
                cluster['client_name'] = ''
            if 'tags' not in cluster.keys():
                cluster['tags'] = []
    return clusters_object


def retrieve_cluster_details(cluster_type: str, cluster_name: str, discovered: bool = False) -> dict:
    logger.info(f'A request to fetch {cluster_name} details was received')
    if cluster_type == GKE:
        if discovered:
            cluster_object = gcp_discovered_gke_clusters.find_one({CLUSTER_NAME.lower(): cluster_name})
        else:
            cluster_object = gke_clusters.find_one({CLUSTER_NAME.lower(): cluster_name})
    elif cluster_type == GKE_AUTOPILOT:
        cluster_object = gke_autopilot_clusters.find_one({CLUSTER_NAME.lower(): cluster_name})
    elif cluster_type == EKS:
        if discovered:
            cluster_object = aws_discovered_eks_clusters.find_one({CLUSTER_NAME.lower(): cluster_name})
        else:
            cluster_object = eks_clusters.find_one({CLUSTER_NAME.lower(): cluster_name})
    elif cluster_type == AKS:
        cluster_object = aks_clusters.find_one({CLUSTER_NAME.lower(): cluster_name})
    else:
        cluster_object = []
    del cluster_object['_id']
    return cluster_object


def retrieve_agent_cluster_details(cluster_name: str) -> list:
    logger.info(f'A request to fetch {cluster_name} details was received')
    cluster_object = k8s_agent_data.find_one({CLUSTER_NAME.lower(): cluster_name})
    if not cluster_object is None:
        del cluster_object['_id']
    else:
        empty_object = {'content': None}
        return [empty_object]
    return [cluster_object]


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
        gcp_cache.drop()
        try:
            mongo_response = gcp_cache.insert_one(caching_object)
            logger.info(mongo_response.acknowledged)
            logger.info(f'Inserted ID for Mongo DB is: {mongo_response.inserted_id}')
            return True
        except:
            logger.error('failure to insert data into gcp_cache table')
            return False
    elif provider == EKS:
        aws_cache.drop()
        try:
            mongo_response = aws_cache.insert_one(caching_object)
            logger.info(mongo_response.acknowledged)
            logger.info(f'Inserted ID for Mongo DB is: {mongo_response.inserted_id}')
            return True
        except:
            logger.error('failure to insert data into aws_cache table')
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
            logger.error('failure to insert data into gcp_cache table')
            return False
    elif provider == EKS:
        eks_discovery.drop()
        try:
            mongo_response = eks_discovery.insert_one(discovery_object)
            logger.info(mongo_response.acknowledged)
            logger.info(f'Inserted ID for Mongo DB is: {mongo_response.inserted_id}')
            return True
        except:
            logger.error('failure to insert data into aws_cache table')
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


def retrieve_clients_data() -> list:
    clients_data_list = []
    mongo_query = {AVAILABILITY.lower(): True}
    clients_data_object = clients_data.find(mongo_query)
    for client_data in clients_data_object:
        del client_data['_id']
        clients_data_list.append(client_data)
    return clients_data_list


def retrieve_client_per_cluster_name(cluster_type: str = '', cluster_name: str = '') -> list:
    mongo_query = {CLUSTER_NAME.lower(): cluster_name}
    if cluster_type == GKE:
        client_name = gke_clusters.find_one(mongo_query)
    elif cluster_type == EKS:
        client_name = eks_clusters.find_one(mongo_query)
    elif cluster_type == AKS:
        client_name = aks_clusters.find_one(mongo_query)
    else:
        client_name = gke_clusters.find_one(mongo_query)
    return client_name[CLIENT_NAME.lower()]


def retrieve_cache(cache_type: str = '', provider: str = '') -> list:
    if provider == GKE:
        cache_object = gcp_cache.find()[0]
    elif provider == EKS:
        cache_object = aws_cache.find()[0]
    elif provider == AKS:
        cache_object = aks_cache.find()[0]
    elif provider == HELM:
        return helm_cache.find()[0]['helms_installs']
    else:
        cache_object = gcp_cache.find()[0]
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


def insert_cluster_data_object(cluster_data_object: dict) -> bool:
    """
    @param cluster_data_object: The filename of the image to save
    """
    try:
        mongo_query = {CLUSTER_NAME.lower(): cluster_data_object[CLUSTER_NAME.lower()]}
        existing_cluster_data_object = k8s_agent_data.find_one(mongo_query)
        if existing_cluster_data_object:
            result = k8s_agent_data.replace_one(existing_cluster_data_object, cluster_data_object)
            logger.info(f'cluster_data_object was updated properly')
            return result.raw_result['updatedExisting']
        else:
            result = k8s_agent_data.insert_one(cluster_data_object)
            if result.inserted_id:
                logger.info(f'cluster_data_object was inserted properly')
                return True
            else:
                logger.error(f'cluster_data_object was not inserted properly')
                return False
    except:
        logger.error(f'cluster_data_object was not inserted properly')


def insert_aws_instances_object(aws_instances_object: dict) -> bool:
    """
    @param aws_instances_object: The aws ec2 instances to save to DB
    """
    logger.info('is this on?')
    logger.info(f'{aws_instances_object}')
    try:
        mongo_query = {ACCOUNT_ID.lower(): aws_instances_object[ACCOUNT_ID.lower()]}
        logger.info(f'Running the following mongo_query {mongo_query}')
        existing_data_object = aws_discovered_ec2_instances.find_one(mongo_query)
        logger.info(f'existing_data_object {existing_data_object}')
        if existing_data_object:
            result = aws_discovered_ec2_instances.replace_one(existing_data_object, aws_instances_object)
            logger.info(f'aws_instances_object was updated properly')
            return result.raw_result['updatedExisting']
        else:
            result = aws_discovered_ec2_instances.insert_one(aws_instances_object)
            logger.info(result.acknowledged)
            if result.inserted_id:
                logger.info(f'aws_instances_object was inserted properly')
                return True
            else:
                logger.error(f'aws_instances_object was not inserted properly')
                return False
    except:
        logger.error(f'aws_instances_object was not inserted properly')


def insert_aws_files_object(aws_files_object: dict) -> bool:
    """
    @param aws_files_object: The aws files list to save
    """
    logger.info('is this on?')
    logger.info(f'{aws_files_object}')
    try:
        mongo_query = {ACCOUNT_ID.lower(): aws_files_object[ACCOUNT_ID.lower()]}
        logger.info(f'Running the following mongo_query {mongo_query}')
        existing_data_object = aws_discovered_s3_files.find_one(mongo_query)
        logger.info(f'existing_data_object {existing_data_object}')
        if existing_data_object:
            result = aws_discovered_s3_files.replace_one(existing_data_object, aws_files_object)
            logger.info(f'aws_files_object was updated properly')
            return result.raw_result['updatedExisting']
        else:
            result = aws_discovered_s3_files.insert_one(aws_files_object)
            if result.inserted_id:
                logger.info(result.acknowledged)
                logger.info(f'aws_files_object was inserted properly')
                return True
            else:
                logger.error(f'aws_files_object was not inserted properly')
                return False
    except:
        logger.error(f'aws_files_object was not inserted properly')


def insert_aws_buckets_object(aws_buckets_object: dict) -> bool:
    """
    @param aws_buckets_object: The aws files list to save
    """
    try:
        mongo_query = {ACCOUNT_ID.lower(): aws_buckets_object[ACCOUNT_ID.lower()]}
        logger.info(f'Running the following mongo_query {mongo_query}')
        existing_data_object = aws_discovered_s3_buckets.find_one(mongo_query)
        logger.info(f'existing_data_object {existing_data_object}')
        if existing_data_object:
            result = aws_discovered_s3_buckets.replace_one(existing_data_object, aws_buckets_object)
            logger.info(f'aws_buckets_object was updated properly')
            return result.raw_result['updatedExisting']
        else:
            result = aws_discovered_s3_buckets.insert_one(aws_buckets_object)
            logger.info(result.acknowledged)
            if result.inserted_id:
                logger.info(f'aws_buckets_object was inserted properly')
                return True
            else:
                logger.error(f'aws_buckets_object was not inserted properly')
                return False
    except:
        logger.error(f'agents_data_object was not inserted properly')


def insert_gcp_files_object(gcp_files_object: dict) -> bool:
    """
    @param gcp_files_object: The gcp files list to save
    """
    try:
        mongo_query = {'project_name': gcp_files_object['project_name']}
        logger.info(f'Running the following mongo_query {mongo_query}')
        existing_data_object = gcp_discovered_files.find_one(mongo_query)
        logger.info(f'existing_data_object {existing_data_object}')
        if existing_data_object:
            result = gcp_discovered_files.replace_one(existing_data_object, gcp_files_object)
            logger.info(f'gcp_files_object was updated properly')
            return result.raw_result['updatedExisting']
        else:
            result = gcp_discovered_files.insert_one(gcp_files_object)
            logger.info(result.acknowledged)
            if result.inserted_id:
                logger.info(f'gcp_files_object was inserted properly')
                return True
            else:
                logger.error(f'gcp_files_object was not inserted properly')
                return False
    except:
        logger.error(f'gcp_files_object was not inserted properly')


def insert_gcp_buckets_object(gcp_buckets_object: dict) -> bool:
    """
    @param gcp_buckets_object: The gcp buckets list to save
    """
    try:
        mongo_query = {'project_name': gcp_buckets_object['project_name']}
        logger.info(f'Running the following mongo_query {mongo_query}')
        existing_data_object = gcp_discovered_buckets.find_one(mongo_query)
        logger.info(f'existing_data_object {existing_data_object}')
        if existing_data_object:
            result = gcp_discovered_buckets.replace_one(existing_data_object, gcp_buckets_object)
            logger.info(f'gcp_buckets_object was updated properly')
            return result.raw_result['updatedExisting']
        else:
            result = gcp_discovered_buckets.insert_one(gcp_buckets_object)
            logger.info(result.acknowledged)
            if result.inserted_id:
                logger.info(f'gcp_buckets_object was inserted properly')
                return True
            else:
                logger.error(f'gcp_buckets_object was not inserted properly')
                return False
    except:
        logger.error(f'gcp_buckets_object was not inserted properly')


def insert_eks_cluster_object(eks_cluster_object: dict) -> bool:
    """
    @param eks_cluster_object: The eks clusters list to save
    """
    logger.info(f'{eks_cluster_object}')
    try:
        mongo_query = {CLUSTER_NAME.lower(): eks_cluster_object[CLUSTER_NAME.lower()]}
        existing_data_object = aws_discovered_eks_clusters.find_one(mongo_query)
        if existing_data_object:
            result = aws_discovered_eks_clusters.replace_one(existing_data_object, eks_cluster_object)
            logger.info(f'aws_discovered_eks_clusters was updated properly')
            return result.raw_result['updatedExisting']
        else:
            result = aws_discovered_eks_clusters.insert_one(eks_cluster_object)
            logger.info(result.acknowledged)
            if result.inserted_id:
                logger.info(f'aws_discovered_eks_clusters was inserted properly')
                return True
            else:
                logger.error(f'aws_discovered_eks_clusters was not inserted properly')
                return False
    except:
        logger.error(f'aws_discovered_eks_clusters was not inserted properly')


def insert_gke_cluster_object(gke_cluster_object: dict) -> bool:
    """
    @param gke_cluster_object: The eks clusters list to save
    """
    logger.info(f'{gke_cluster_object}')
    try:
        mongo_query = {CLUSTER_NAME.lower(): gke_cluster_object[CLUSTER_NAME.lower()]}
        existing_data_object = gcp_discovered_gke_clusters.find_one(mongo_query)
        if existing_data_object:
            result = gcp_discovered_gke_clusters.replace_one(existing_data_object, gke_cluster_object)
            logger.info(f'aws_discovered_eks_clusters was updated properly')
            return result.raw_result['updatedExisting']
        else:
            result = gcp_discovered_gke_clusters.insert_one(gke_cluster_object)
            logger.info(result.acknowledged)
            if result.inserted_id:
                logger.info(f'gcp_discovered_gke_clusters was inserted properly')
                return True
            else:
                logger.error(f'gcp_discovered_gke_clusters was not inserted properly')
                return False
    except:
        logger.error(f'gcp_discovered_gke_clusters was not inserted properly')


def insert_gcp_vm_instances_object(gcp_vm_instances_object: dict) -> bool:
    """
    @param gcp_vm_instances_object: The gcp vm instances object to save
    """
    try:
        mongo_query = {'project_name': gcp_vm_instances_object['project_name']}
        existing_data_object = gcp_discovered_vm_instances.find_one(mongo_query)
        if existing_data_object:
            result = gcp_discovered_vm_instances.replace_one(existing_data_object, gcp_vm_instances_object)
            logger.info(f'gcp_vm_instances_object was updated properly')
            return result.raw_result['updatedExisting']
        else:
            result = gcp_discovered_vm_instances.insert_one(gcp_vm_instances_object)
            logger.info(result.acknowledged)
            if result.inserted_id:
                logger.info(f'gcp_vm_instances_object was inserted properly')
                return True
            else:
                logger.error(f'gcp_vm_instances_object was not inserted properly')
                return False
    except:
        logger.error(f'gcp_vm_instances_object was not inserted properly')


def insert_aws_agent_data_object(agent_data_object: dict) -> bool:
    """
    @param agent_data_object: The filename of the image to save
    """
    if agent_data_object['ec2Object']:
        insert_aws_instances_object(agent_data_object['ec2Object'])
    if agent_data_object['s3FilesObject']:
        insert_aws_files_object(agent_data_object['s3FilesObject'])
    if agent_data_object['s3BucketsObject']:
        insert_aws_buckets_object(agent_data_object['s3BucketsObject'])
    if agent_data_object['eksObject']:
        insert_eks_cluster_object(agent_data_object['eksObject'])
    return True


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


def add_client_data_object(client_data_object: dict) -> bool:
    """
    @param client_data_object: The client data to add
    """
    try:
        mongo_query = {'client_name': client_data_object['client_name']}
        existing_clients_data_object = clients_data.find_one(mongo_query)
        if existing_clients_data_object:
            result = clients_data.replace_one(existing_clients_data_object, client_data_object)
            logger.info(f'clients_data_object was updated properly')
            return result.raw_result['updatedExisting']
        else:
            client_data_object['availability'] = True
            result = clients_data.insert_one(client_data_object)
            if result.inserted_id:
                logger.info(f'client was inserted properly')
                return True
            else:
                logger.error(f'client was not inserted properly')
                return False
    except:
        logger.error(f'client data was not inserted properly')


def add_client_to_cluster(cluster_type: str = '', cluster_name: str = '', client_name: str = '',
                          discovered: bool = False):
    """

    @param cluster_type: The type of the cluster to change the availability of
    @param cluster_name: The name of the cluster to set the availability of
    @param client_name: Name of the client we want to associate with the cluster
    @param discovered: Signifies whether the cluster was discovered by Trolley agent.
    @return:
    """

    myquery = {CLUSTER_NAME.lower(): cluster_name}
    newvalues = {"$set": {CLIENT_NAME.lower(): client_name}}
    if cluster_type == GKE:
        result = gke_clusters.update_one(myquery, newvalues)
    elif cluster_type == GKE_AUTOPILOT:
        result = gke_autopilot_clusters.update_one(myquery, newvalues)
    elif cluster_type == EKS:
        if discovered:
            result = aws_discovered_eks_clusters.update_one(myquery, newvalues)
        else:
            result = eks_clusters.update_one(myquery, newvalues)
    elif cluster_type == AKS:
        result = aks_clusters.update_one(myquery, newvalues)
    else:
        result = gke_clusters.update_one(myquery, newvalues)
    return result.raw_result['updatedExisting']


def delete_client(client_name: str) -> bool:
    """
    @param client_name: The name of the client to delete
    """
    try:
        mongo_query = {'client_name': client_name}
        newvalues = {"$set": {AVAILABILITY.lower(): False}}
        existing_clients_data_object = clients_data.find_one(mongo_query)
        if existing_clients_data_object:
            result = clients_data.update_one(mongo_query, newvalues)
            logger.info(f'clients_name was deleted')
            return True
        else:
            logger.error(f'client does not exist')
            return False
    except:
        logger.error(f'client data was not deleted properly')
