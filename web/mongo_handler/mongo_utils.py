import logging
import os
import platform
import time
from dataclasses import asdict
from typing import Any, Mapping, Dict

import gridfs
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor

file_name = 'server.log'
log_file_path = f'{os.getcwd()}/{file_name}'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(log_file_path)
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
    USER_NAME, USER_EMAIL, HELM, CLUSTER_TYPE, ACCOUNT_ID, CLIENT_NAME, AWS, GCP, AZ, INSTANCE_NAME, TEAM_NAME, \
    ADMIN, USER, CLIENT, TEAM_ADDITIONAL_INFO, PROVIDER
else:
    from variables.variables import GKE, GKE_AUTOPILOT, CLUSTER_NAME, AVAILABILITY, EKS, AKS, EXPIRATION_TIMESTAMP, \
        USER_NAME, USER_EMAIL, HELM, CLUSTER_TYPE, ACCOUNT_ID, CLIENT_NAME, AWS, GCP, AZ, INSTANCE_NAME, TEAM_NAME, \
        ADMIN, USER, CLIENT, TEAM_ADDITIONAL_INFO

project_folder = os.path.expanduser(os.getcwd())
load_dotenv(os.path.join(project_folder, '.env'))
logger.info(f'project_folder is: {project_folder}')

PROJECT_NAME = os.environ.get('PROJECT_NAME', 'trolley-361905')
GCP_PROJECT_NAME = os.environ.get('GCP_PROJECT_NAME', 'trolley-361905')

MONGO_PASSWORD = os.environ['MONGO_PASSWORD']
MONGO_USER = os.environ['MONGO_USER']
MONGO_URL = os.environ['MONGO_URL']
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))

ATLAS_FULL_URL = f"mongodb+srv://admin:{MONGO_PASSWORD}@{MONGO_URL}/?retryWrites=true&w=majority"

if "mongodb.net" in MONGO_URL:
    print('mongodb.net was chosen')
    client = MongoClient(ATLAS_FULL_URL)
else:
    print('mongodb.net was not chosen')
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

az_discovered_aks_clusters: Collection = db.az_discovered_aks_clusters
az_discovered_vm_instances: Collection = db.az_discovered_vm_instances
az_discovered_buckets: Collection = db.az_discovered_buckets
az_discovered_files: Collection = db.az_discovered_files

aks_clusters: Collection = db.aks_clusters
invited_users: Collection = db.invited_users
teams: Collection = db.teams
users: Collection = db.users
deployment_yamls: Collection = db.deployment_yamls
aks_cache: Collection = db.aks_cache
gke_cache: Collection = db.gke_cache
gke_machines_cache: Collection = db.gke_machines_cache
helm_cache: Collection = db.helm_cache
aws_cache: Collection = db.aws_cache

fs = gridfs.GridFS(db)

k8s_agent_data: Collection = db.k8s_agent_data

providers_data: Collection = db.providers_data
github_data: Collection = db.github_data
clients_data: Collection = db.clients_data

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


def retrieve_available_clusters(cluster_type: str, client_name: str = '', user_name: str = '') -> list:
    logger.info(f'A request to fetch {cluster_type} clusters for {user_name} was received')
    all_clusters_object = []
    discovered_clusters_object = []
    if cluster_type == GKE:
        if not user_name and not client_name:
            return []
            # clusters_object = gke_clusters.find({AVAILABILITY: True})
        elif is_admin(user_name):
            discovered_clusters_object = gcp_discovered_gke_clusters.find({AVAILABILITY: True})
            clusters_object = gke_clusters.find({AVAILABILITY: True})
        else:
            if user_name:
                clusters_object = gke_clusters.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
                discovered_clusters_object = gcp_discovered_gke_clusters.find(
                    {AVAILABILITY: True, USER_NAME.lower(): user_name})
            elif client_name:
                clusters_object = gke_clusters.find({AVAILABILITY: True, CLIENT_NAME.lower(): client_name})
                discovered_clusters_object = gcp_discovered_gke_clusters.find(
                    {AVAILABILITY: True, CLIENT_NAME.lower(): client_name})
    elif cluster_type == GKE_AUTOPILOT:
        if not user_name or is_admin(user_name):
            clusters_object = gke_autopilot_clusters.find({AVAILABILITY: True})
        else:
            clusters_object = gke_autopilot_clusters.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
    elif cluster_type == EKS:
        if not user_name and not client_name:
            clusters_object = eks_clusters.find({AVAILABILITY: True})
        elif is_admin(user_name):
            discovered_clusters_object = aws_discovered_eks_clusters.find({AVAILABILITY: True})
            clusters_object = eks_clusters.find({AVAILABILITY: True})
        else:
            if user_name:
                clusters_object = eks_clusters.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
                discovered_clusters_object = aws_discovered_eks_clusters.find(
                    {AVAILABILITY: True, USER_NAME.lower(): user_name})
            elif client_name:
                clusters_object = eks_clusters.find({AVAILABILITY: True, CLIENT_NAME.lower(): client_name})
                discovered_clusters_object = aws_discovered_eks_clusters.find(
                    {AVAILABILITY: True, CLIENT_NAME.lower(): client_name})
    elif cluster_type == AKS:
        if not user_name and not client_name:
            clusters_object = aks_clusters.find({AVAILABILITY: True})
        elif is_admin(user_name):
            discovered_clusters_object = az_discovered_aks_clusters.find({AVAILABILITY: True})
            clusters_object = aks_clusters.find({AVAILABILITY: True})
        else:
            if user_name:
                clusters_object = aks_clusters.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
                discovered_clusters_object = az_discovered_aks_clusters.find(
                    {AVAILABILITY: True, USER_NAME.lower(): user_name})
            elif client_name:
                clusters_object = aks_clusters.find({AVAILABILITY: True, CLIENT_NAME.lower(): client_name})
                discovered_clusters_object = az_discovered_aks_clusters.find(
                    {AVAILABILITY: True, CLIENT_NAME.lower(): client_name})
        # if not user_name or is_admin(user_name):
        #     clusters_object = aks_clusters.find({AVAILABILITY: True})
        # else:
        #     clusters_object = aks_clusters.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
    else:
        clusters_object = []
    for cluster in clusters_object:
        del cluster['_id']
        cluster['discovered'] = False
        all_clusters_object.append(cluster)
        if 'client_name' not in cluster.keys():
            cluster['client_name'] = ''
        if 'tags' not in cluster.keys():
            cluster['tags'] = []
    if discovered_clusters_object:
        for cluster in discovered_clusters_object:
            del cluster['_id']
            cluster['discovered'] = True
            all_clusters_object.append(cluster)
            if 'client_name' not in cluster.keys():
                cluster['client_name'] = ''
            if 'tags' not in cluster.keys():
                cluster['tags'] = []
    return all_clusters_object


def retrieve_instances(provider_type: str, client_name: str = '', user_name: str = "") -> list:
    logger.info(f'A request to fetch instance for {provider_type} provider was received')
    instances_list = []
    if provider_type == AWS:
        if not user_name and not client_name:
            instances_object = aws_discovered_ec2_instances.find({AVAILABILITY: True})
        elif is_admin(user_name):
            instances_object = aws_discovered_ec2_instances.find({AVAILABILITY: True})
        else:
            if user_name:
                instances_object = aws_discovered_ec2_instances.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
            elif client_name:
                instances_object = aws_discovered_ec2_instances.find(
                    {AVAILABILITY: True, CLIENT_NAME.lower(): client_name.lower()})
    elif provider_type == GCP:
        if not user_name and not client_name:
            instances_object = gcp_discovered_vm_instances.find({AVAILABILITY: True})
        elif is_admin(user_name):
            instances_object = gcp_discovered_vm_instances.find({AVAILABILITY: True})
        else:
            if user_name:
                instances_object = gcp_discovered_vm_instances.find({AVAILABILITY: True, USER_NAME.lower(): user_name})
            elif client_name:
                instances_object = gcp_discovered_vm_instances.find(
                    {AVAILABILITY: True, CLIENT_NAME.lower(): client_name.lower()})
    elif provider_type == AZ:
        instances_object = az_discovered_vm_instances.find()
    else:
        instances_object = {}
    for instance in instances_object:
        del instance['_id']
        instances_list.append(instance)
    return instances_list


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


def insert_cache_object(caching_object: dict = None, provider: str = None, machine_types: bool = False) -> bool:
    """
    @param caching_object: The dictionary with all the cluster data.
    @param provider: The dictionary with all the cluster data.
    @param machine_types: The list of all the available machines
    """
    if provider == GKE:
        if machine_types:
            try:
                myquery = {"region": caching_object['region']}
                if gke_machines_cache.find_one(myquery):
                    newvalues = {"$set": {'machines_list': caching_object['machines_list'],
                                          'region': caching_object['region']}}
                    mongo_response = gke_machines_cache.update_one(myquery, newvalues)
                    logger.info(mongo_response.acknowledged)
                else:
                    values = {'machines_list': caching_object['machines_list'],
                              'region': caching_object['region']}
                    mongo_response = gke_machines_cache.insert_one(values)
                    logger.info(mongo_response.acknowledged)
                return True
            except:
                logger.error('failure to insert data into gke_machines_cache table')
                return False
        else:
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
        cache_object = gke_cache.find()[0]
    elif provider == EKS:
        cache_object = aws_cache.find()[0]
    elif provider == AKS:
        cache_object = aks_cache.find()[0]
    elif provider == HELM:
        return helm_cache.find()[0]['helms_installs']
    else:
        cache_object = gke_cache.find()[0]
    return cache_object[cache_type]


def retrieve_compute_per_machine_type(provider: str = '', machine_type: str = '', region_name: str = '') -> dict:
    if provider == GKE:
        mongo_query = {'region': region_name}
        cache_object = gke_machines_cache.find_one(mongo_query)
    elif provider == EKS:
        cache_object = aws_cache.find()[0]
    elif provider == AKS:
        cache_object = aks_cache.find()[0]
    elif provider == HELM:
        return helm_cache.find()[0]['helms_installs']
    else:
        cache_object = gke_cache.find()[0]
    machines_list = cache_object['machines_list']
    for machine in machines_list:
        if machine['machine_type'] == machine_type:
            return machine


def retrieve_user(user_email: str):
    """
    @param user_email:  retrieve a returning user data
    @return:
    """
    print(f'Listing all the collections')
    logger.info(f'Listing all the collections')
    print(db.list_collection_names())
    logger.info(db.list_collection_names())
    mongo_query = {USER_EMAIL: user_email}
    logger.info(f'Running the {mongo_query}')
    user_object = users.find_one(mongo_query)
    logger.info(f'The result of the query is: {user_object}')
    if not user_object:
        logger.warning(f'Nothing was found in the users db')
        return None
    try:
        profile_image_id = user_object['profile_image_id']
        file = fs.find_one({"_id": profile_image_id})
        user_object['profile_image'] = file
        logger.info(f'The result of the query is: {user_object}')
    except:
        logger.error(f'There was a problem here')
    return user_object


def retrieve_users_data(logged_user_name: str = ""):
    """
    This endpoint retrieves data for all the available users
    """
    if logged_user_name:
        if is_admin(logged_user_name):
            user_objects = users.find()
        else:
            mongo_query = {USER_NAME.lower(): logged_user_name}
            user_object = users.find(mongo_query)
            user_objects = user_object
    else:
        user_objects = users.find()
    users_data = []
    if not user_objects:
        return None
    else:
        for user_object in user_objects:
            del user_object["_id"]
            try:
                del user_object['profile_image_id']
                del user_object['hashed_password']
            except:
                logger.error(f'There was a problem here')
            if user_object['availability']:
                users_data.append(user_object)
        return users_data


def update_user(user_email: str, update_type: str, update_value: str) -> bool:
    """
    @param user_email: The name of the user to update
    @param update_type: The type of the update. eg. team_name
    @param update_value: The value of the update. eg. "qa"
    """
    try:
        mongo_query = {USER_EMAIL.lower(): user_email}
        existing_user_object = users.find_one(mongo_query)
        if existing_user_object:
            newvalues = {"$set": {update_type: update_value}}
            # result = users.replace_one(existing_user_object, existing_user_object)
            result = users.update_one(mongo_query, newvalues)

            return True
    except:
        print("dsf")
        return False


def retrieve_teams_data():
    """
    This endpoint retrieves data for all the available teams
    """

    teams_objects = teams.find()
    teams_data = []
    if not teams_objects:
        return None
    else:
        for team_object in teams_objects:
            if team_object[AVAILABILITY]:
                del team_object["_id"]
                teams_data.append(team_object)
        return teams_data


def retrieve_invited_user(user_email: str):
    """
    @param user_email:  retrieve a returning user data
    @return:
    """
    mongo_query = {USER_EMAIL: user_email}
    user_object = invited_users.find_one(mongo_query)
    logger.info(f'found invited_user is: {user_object}')
    if not user_object:
        return None
    try:
        del user_object["_id"]
    except:
        logger.error(f'There was a problem here')
    return user_object


def delete_user(user_email: str = "", user_name: str = ""):
    """
    @param user_email:  deleting a user using his email
    @param user_name:  deleting a user using his user_name
    @return:
    """
    if user_email:
        myquery = {USER_EMAIL: user_email}
        newvalues = {"$set": {'availability': False}}
        result = users.update_one(myquery, newvalues)
    elif user_name:
        myquery = {USER_NAME.lower(): user_name}
        newvalues = {"$set": {'availability': False}}
        result = users.update_one(myquery, newvalues)
    else:
        myquery = {USER_EMAIL: user_email}
        newvalues = {"$set": {'availability': False}}
        result = users.update_one(myquery, newvalues)
    return result.raw_result['updatedExisting']


def delete_team(team_name: str = ""):
    """
    @param team_name:  deleting a team using its name
    @return:
    """
    myquery = {TEAM_NAME.lower(): team_name}
    newvalues = {"$set": {'availability': False}}
    result = teams.update_one(myquery, newvalues)
    return result.raw_result['updatedExisting']


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


def update_user_registration_status(user_email: str = "", registration_status: str = '') -> bool:
    """
    @param user_email: The dictionary with all the user data.
    @param registration_status: The dictionary with all the user data.
    """

    myquery = {"user_email": user_email}
    newvalues = {"$set": {'registration_status': registration_status}}
    result = users.update_one(myquery, newvalues)
    logger.info(f'users_data_object was updated properly')
    return result.raw_result['updatedExisting']


def is_users() -> bool:
    """
    This function checks if there are any users in the DB
    """
    if len(list(users.find())) > 0:
        return True
    else:
        return False


def is_admin(user_name: str = "") -> bool:
    """
    This function checks if the provided user is an admin
    """
    if not user_name:
        return False
    mongo_query = {USER_NAME.lower(): user_name}
    user_object = users.find_one(mongo_query)
    if user_object['user_type'] == ADMIN:
        return True
    else:
        return False


def check_user_type(user_email: str = "") -> str:
    """
    This function checks the user_type of provided email
    """
    mongo_query = {USER_EMAIL.lower(): user_email}
    user_object = users.find_one(mongo_query)
    if user_object:
        return user_object['user_type']
    else:
        return ''


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


def insert_aws_instances_object(aws_ec2_instances_object: list) -> bool:
    """
    @param aws_ec2_instances_object: The aws ec2 instances to save to DB
    """
    logger.info('is this on?')
    logger.info(f'{aws_ec2_instances_object}')
    try:
        for aws_ec2_instance in aws_ec2_instances_object:
            mongo_query = {'instance_name': asdict(aws_ec2_instance)[INSTANCE_NAME.lower()]}
            existing_data_object = aws_discovered_ec2_instances.find_one(mongo_query)
            if not existing_data_object:
                result = aws_discovered_ec2_instances.insert_one(asdict(aws_ec2_instance))
                logger.info(result.acknowledged)
                if result.inserted_id:
                    logger.info(f'aws_ec2_instance was inserted properly')
                else:
                    logger.error(f'aws_ec2_instance was not inserted properly')
        return True
    except:
        logger.error(f'aws_ec2_instance was not inserted properly')


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


def drop_discovered_clusters(cluster_type: str = '') -> bool:
    if cluster_type == GKE:
        gcp_discovered_gke_clusters.drop()
    elif cluster_type == EKS:
        aws_discovered_eks_clusters.drop()
    elif cluster_type == AKS:
        az_discovered_aks_clusters.drop()
    return True


def insert_discovered_gke_cluster_object(gke_cluster_object: dict) -> bool:
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


def update_discovered_gke_cluster_object(gke_cluster_object: dict) -> bool:
    """
    @param gke_cluster_object: The gke cluster list to update
    """
    logger.info(f'{gke_cluster_object}')
    try:
        mongo_query = {CLUSTER_NAME.lower(): gke_cluster_object[CLUSTER_NAME.lower()]}
        existing_data_object = gke_clusters.find_one(mongo_query)
        gke_cluster_object['user_name'] = existing_data_object['user_name']
        gke_cluster_object['expiration_timestamp'] = existing_data_object['expiration_timestamp']
        gke_cluster_object['human_expiration_timestamp'] = existing_data_object['human_expiration_timestamp']
        gke_cluster_object['kubeconfig'] = existing_data_object['kubeconfig']
        if existing_data_object:
            result = gke_clusters.replace_one(existing_data_object, gke_cluster_object)
            logger.info(f'aws_discovered_eks_clusters was updated properly')
            return result.raw_result['updatedExisting']
        else:
            result = gke_clusters.insert_one(gke_cluster_object)
            logger.info(result.acknowledged)
            if result.inserted_id:
                logger.info(f'gcp_discovered_gke_clusters was inserted properly')
                return True
            else:
                logger.error(f'gcp_discovered_gke_clusters was not inserted properly')
                return False
    except:
        logger.error(f'gcp_discovered_gke_clusters was not inserted properly')


def insert_gcp_vm_instances_object(gcp_vm_instances_object: list) -> bool:
    """
    @param gcp_vm_instances_object: The gcp vm instances object to save
    """
    try:
        if len(gcp_vm_instances_object) == 0:
            gcp_already_discovered_vm_instances_object = gcp_discovered_vm_instances.find()
            for gcp_discovered_vm_instance in gcp_already_discovered_vm_instances_object:
                myquery = {INSTANCE_NAME.lower(): gcp_discovered_vm_instance['instance_name']}
                newvalues = {"$set": {AVAILABILITY.lower(): False}}
                gcp_discovered_vm_instances.update_one(myquery, newvalues)
            return True
        else:
            for gcp_vm_instance in gcp_vm_instances_object:
                mongo_query = {'instance_name': asdict(gcp_vm_instance)[INSTANCE_NAME.lower()]}
                gcp_discovered_vm_instances_object = gcp_discovered_vm_instances.find_one(mongo_query)
                if not gcp_discovered_vm_instances_object:
                    result = gcp_discovered_vm_instances.insert_one(asdict(gcp_vm_instance))
                    logger.info(result.acknowledged)
                    if result.inserted_id:
                        logger.info(f'gcp_vm_instances_object was inserted properly')
                    else:
                        logger.error(f'gcp_vm_instances_object was not inserted properly')
                else:
                    myquery = {INSTANCE_NAME.lower(): gcp_discovered_vm_instances_object['instance_name']}
                    newvalues = {"$set": {AVAILABILITY.lower(): True}}
                    gcp_discovered_vm_instances.update_one(myquery, newvalues)
            return True
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


def insert_provider_data_object(providers_data_object: dict) -> bool:
    """
    @param providers_data_object: The data of the added provider
    """
    try:
        mongo_query = {'provider': providers_data_object['provider'], 'user_email': providers_data_object['user_email']}
        existing_providers_data_object = providers_data.find_one(mongo_query)
        if existing_providers_data_object:
            result = providers_data.replace_one(existing_providers_data_object, providers_data_object)
            logger.info(f'providers_data_object was updated properly')
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


def retrieve_provider_data_object(user_email: str, provider: str) -> Mapping[str, Any]:
    """
    @param user_email: The email of the user we fetch the provider data for.
    @param provider: The provider name.
    """
    mongo_query = {'user_email': user_email, 'provider': provider}
    providers_data_object = providers_data.find_one(mongo_query)
    if not providers_data_object:
        logger.info(f'There is no provider data for {provider} provider for {user_email} user_email')
        return {}
    del providers_data_object['_id']
    return providers_data_object


def insert_github_data_object(github_data_object: dict) -> bool:
    """
    @param github_data_object: The data of the added provider
    """
    try:
        user_email = github_data_object['user_email']
        mongo_query = {'user_email': user_email}
        current_github_data_object = github_data.find_one(mongo_query)
        if current_github_data_object:
            logger.info(f'A GitHub repository was already defined for user {user_email}')
            return True
        else:
            result = github_data.insert_one(github_data_object)
            if result.inserted_id:
                logger.info(f'github data was inserted properly')
                return True
            else:
                logger.error(f'github data was not inserted properly')
                return False
    except:
        logger.error(f'github data was not inserted properly')


def retrieve_github_data_object(user_email: str = '') -> dict:
    """
    """
    mongo_query = {'user_email': user_email}
    github_data_object = github_data.find_one(mongo_query)
    if not github_data_object:
        logger.info(f'There is no github data ')
        return {}
    del github_data_object['_id']
    return github_data_object

def retrieve_credentials_data_object(provider: str, user_email: str) -> dict:
    """
    """
    mongo_query = {PROVIDER: provider, USER_EMAIL: user_email}
    credentials_data_object = providers_data.find_one(mongo_query)
    if not credentials_data_object:
        logger.info(f'There is no github data ')
        return {}
    del credentials_data_object['_id']
    return credentials_data_object


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
            if "http" not in client_data_object['client_web_address']:
                client_data_object['client_web_address'] = 'https://' + client_data_object['client_web_address']
            result = clients_data.insert_one(client_data_object)
            if result.inserted_id:
                logger.info(f'client was inserted properly')
                return True
            else:
                logger.error(f'client was not inserted properly')
                return False
    except:
        logger.error(f'client data was not inserted properly')


def add_data_to_cluster(object_type: str, cluster_type: str = '', cluster_name: str = '', assigned_object: str = '',
                        user_name: str = '', client_name: str = '', discovered: bool = False):
    """

    @param object_type: The type of an object
    @param cluster_type: The type of the cluster to change the availability of
    @param assigned_object: The name of the object we want to assign to the cluster (user/client)
    @param cluster_name: The name of the cluster to set the availability of
    @param user_name: Name of the user we want to associate with the cluster
    @param client_name: Name of the client we want to associate with the cluster
    @param discovered: Signifies whether the cluster was discovered by Trolley agent.
    @return:
    """

    myquery = {CLUSTER_NAME.lower(): cluster_name}
    if assigned_object == USER:
        newvalues = {"$set": {USER_NAME.lower(): user_name}}
    elif assigned_object == CLIENT:
        newvalues = {"$set": {CLIENT_NAME.lower(): client_name}}
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


def add_data_to_instance(object_type: str, provider: str = '', instance_name: str = '', assigned_object: str = '',
                         user_name: str = '', client_name: str = ''):
    """

    @param object_type: The type of an object
    @param provider: The name of the provider
    @param instance_name: The name of the instance we assign the client for
    @param assigned_object: The name of the object we want to assign to the instance (user/client)
    @param user_name: Name of the user we want to associate with the cluster
    @param client_name: Name of the client we want to associate with the cluster
    @return:
    """

    myquery = {INSTANCE_NAME.lower(): instance_name}
    if assigned_object == USER:
        newvalues = {"$set": {USER_NAME.lower(): user_name}}
    elif assigned_object == CLIENT:
        newvalues = {"$set": {CLIENT_NAME.lower(): client_name.lower()}}
    if provider == GCP:
        result = gcp_discovered_vm_instances.update_one(myquery, newvalues)
    elif provider == AWS:
        result = aws_discovered_ec2_instances.update_one(myquery, newvalues)
    elif provider == AZ:
        result = az_discovered_vm_instances.update_one(myquery, newvalues)
    else:
        return True
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
            clients_data.update_one(mongo_query, newvalues)
            return True
        else:
            logger.error(f'client does not exist')
            return False
    except:
        logger.error(f'client data was not deleted properly')


def invite_user(user_data_object: dict) -> bool:
    """
    @param user_data_object: The client data to add
    """
    try:
        mongo_query = {'user_email': user_data_object['user_email']}
        existing_user_data_object = users.find_one(mongo_query)
        if existing_user_data_object:
            user_email = user_data_object['user_email']
            logger.warning(f'user {user_email} already exists in the system')
        else:
            user_data_object['registration_status'] = "invited"
            user_data_object['user_type'] = user_data_object['user_type']
            user_data_object['first_name'] = "none"
            user_data_object['last_name'] = "none"

            result = invited_users.insert_one(user_data_object)
            if result.inserted_id:
                logger.info(f'user was inserted properly')
                return True
            else:
                logger.error(f'user was not inserted properly')
                return False
    except:
        logger.error(f'client data was not inserted properly')


def insert_team(team_data_object: dict) -> bool:
    """
    @param team_data_object: The team data to add
    """
    try:
        mongo_query = {'team_name': team_data_object['team_name']}
        existing_team_data_object = teams.find_one(mongo_query)
        if existing_team_data_object:
            if existing_team_data_object[AVAILABILITY.lower()]:
                team_name = team_data_object['team_name']
                logger.warning(f'team {team_name} already exists in the system')
                return True
            if not existing_team_data_object[AVAILABILITY.lower()]:
                mongo_query = {TEAM_NAME.lower(): team_data_object[TEAM_NAME.lower()]}
                newvalues = {
                    "$set": {AVAILABILITY.lower(): True, TEAM_ADDITIONAL_INFO: team_data_object[TEAM_ADDITIONAL_INFO]}}
                teams.update_one(mongo_query, newvalues)
        else:
            team_data_object[AVAILABILITY] = True
            result = teams.insert_one(team_data_object)
            if result.inserted_id:
                logger.info(f'team was inserted properly')
                return True
            else:
                logger.error(f'team was not inserted properly')
                return False
    except:
        logger.error(f'team data was not inserted properly')
