import codecs
import sys
import time

from dotenv import load_dotenv
import inspect
import json
import logging
import os
import datetime
from functools import wraps
from threading import Thread

from dataclasses import asdict

from cryptography.fernet import Fernet
from flask import request, Response, Flask, session, redirect, url_for, render_template, jsonify
from flask_caching import Cache
from itsdangerous import URLSafeTimedSerializer
from jwt import encode, InvalidTokenError
from PIL import Image
import yaml
from werkzeug.datastructures import FileStorage
from werkzeug.security import generate_password_hash, check_password_hash

DOCKER_ENV = os.getenv('DOCKER_ENV', False)

log_file_name = 'trolley_server.log'
if DOCKER_ENV:
    log_file_path = f'/var/log/{log_file_name}'
else:
    log_file_path = f'{os.getcwd()}/{log_file_name}'

logger = logging.getLogger(__name__)

file_handler = logging.FileHandler(log_file_path)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers
)

project_folder = os.path.expanduser(os.getcwd())
load_dotenv(os.path.join(project_folder, '.env'))
EMAIL_AUTHENTICATION = os.getenv('MAIL_AUTHENTICATION', False)
GMAIL_USER = os.getenv('GMAIL_USER', "trolley_user")
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD', "trolley_password")
PROJECT_NAME = os.getenv('PROJECT_NAME', "trolley-dev")
MONGO_URL = os.getenv('MONGO_URL', 'localhost')
MONGO_USER = os.getenv('MONGO_USER', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'yes')

logger.info(f'App runs in the DOCKER_ENV: {DOCKER_ENV}')
logger.info(os.environ)

import mongo_handler.mongo_utils
from cluster_operations import ClusterOperation
from mongo_handler.mongo_objects import UserObject, GithubObject, ProviderObject, InfracostObject
from variables.variables import POST, GET, EKS, \
    APPLICATION_JSON, CLUSTER_TYPE, GKE, AKS, DELETE, USER_NAME, REGIONS_LIST, \
    ZONES_LIST, GKE_VERSIONS_LIST, GKE_IMAGE_TYPES, LOCATIONS_DICT, \
    CLUSTER_NAME, AWS, PROVIDER, GCP, AZ, PUT, OK, FAILURE, OBJECT_TYPE, CLUSTER, INSTANCE, TEAM_NAME, ZONE_NAMES, \
    REGION_NAME, CLIENT_NAME, AVAILABILITY, GCP_PROJECT_ID, GITHUB_REPOSITORY, GITHUB_ACTIONS_TOKEN, \
    LOCATION_NAME, DISCOVERED, AZ_RESOURCE_GROUP, MACHINE_SERIES, INFRACOST_TOKEN, GOOGLE_CREDS_JSON, AWS_ACCESS_KEY_ID, \
    AWS_SECRET_ACCESS_KEY, AZURE_CREDENTIALS

from __init__ import __version__
from mail_handler import MailSender
from utils import random_string, apply_yaml, check_settings_keys
from scripts import gcp_discovery_script, aws_discovery_script, az_discovery_script

secret_key = os.getenv('SECRET_KEY')
encoded_secret_key = secret_key.encode()
crypter = Fernet(encoded_secret_key)

cache = Cache()
app = Flask(__name__, template_folder='templates')
cache.init_app(app, config={'CACHE_TYPE': 'SimpleCache'})

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SECURITY_PASSWORD_SALT'] = 'salty_balls'
app.config['UPLOAD_FOLDER'] = ''
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


def generate_confirmation_token(email) -> str:
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600) -> str:
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return "Fail"
    return email


def user_registration(first_name: str = '', last_name: str = '', password: str = '',
                      user_email: str = '', user_type: str = 'user', team_name: str = '',
                      profile_image_filename: str = '',
                      confirmation_url: str = '', registration_status: str = '') -> bool:
    """
    This function registers a new user into the DB
    """
    if not mongo_handler.mongo_utils.is_users():
        # If there are no users in the DB and this is the first registration, the user will be assigned as an admin user
        # and as a part of the IT Team
        user_type = 'admin'
        team_name = 'it'
        content = {TEAM_NAME: team_name, AVAILABILITY: True, "team_additional_info": "it folks"}
        mongo_handler.mongo_utils.insert_team(content)
    user_name = f'{first_name.lower()}-{last_name.lower()}'
    hashed_password = generate_password_hash(password, method='sha256')
    profile_image_id = mongo_handler.mongo_utils.insert_file(profile_image_filename)
    if mongo_handler.mongo_utils.retrieve_user(user_email):
        mongo_handler.mongo_utils.delete_user(user_email=user_email)
    user_object = UserObject(first_name=first_name, last_name=last_name, user_name=user_name, user_email=user_email,
                             team_name=team_name, hashed_password=hashed_password, confirmation_url=confirmation_url,
                             registration_status=registration_status, user_type=user_type,
                             profile_image_filename=f'static/img/{profile_image_filename}', availability=True,
                             profile_image_id=profile_image_id, created_timestamp=int(time.time()))
    if mongo_handler.mongo_utils.insert_user(asdict(user_object)):
        if 'trolley' in profile_image_filename:
            return True
        return True
    else:
        return False


def encode_provider_details(content: dict) -> ProviderObject:
    encoded_aws_access_key_id = crypter.encrypt(str.encode(content[AWS_ACCESS_KEY_ID]))
    encoded_aws_secret_access_key = crypter.encrypt(str.encode(content[AWS_SECRET_ACCESS_KEY]))
    encoded_google_creds_json = crypter.encrypt(str.encode(content[GOOGLE_CREDS_JSON]))
    encoded_azure_credentials = crypter.encrypt(str.encode(content[AZURE_CREDENTIALS]))
    provider_object = ProviderObject(provider=content[PROVIDER], aws_access_key_id=encoded_aws_access_key_id,
                                     aws_secret_access_key=encoded_aws_secret_access_key,
                                     azure_credentials=encoded_azure_credentials,
                                     google_creds_json=encoded_google_creds_json, user_email=content['user_email'],
                                     created_timestamp=int(time.time()))
    return provider_object


def encode_github_details(content: dict) -> GithubObject:
    github_actions_token = crypter.encrypt(str.encode(content['github_actions_token']))
    github_object = GithubObject(github_actions_token=github_actions_token,
                                 github_repository=content['github_repository'],
                                 user_email=content['user_email'], created_timestamp=int(time.time()))
    return github_object


def encode_infracost_details(content: dict) -> InfracostObject:
    infracost_token = crypter.encrypt(str.encode(content['infracost_token']))
    infracost_object = InfracostObject(infracost_token=infracost_token,
                                       user_email=content['user_email'], created_timestamp=int(time.time()))
    return infracost_object


def login_processor(user_email: str = "", password: str = "", new: bool = False) -> tuple:
    user_agent = request.headers.get('User-Agent')
    if request.headers.get('request-source') == 'kubernetes':
        return '', ''
    logger.info(f'The request comes from {user_agent} user agent')
    if new:
        session.pop('x-access-token', None)
        session.pop('user_email', None)
        session.pop('user_password', None)
    if not user_email and not password:
        try:
            user_email = session['user_email']
            password = session['user_password']
        except:
            user_email = request.form['user_email']
            password = request.form['user_password']
    logger.info(f'The request comes with {user_email} email')
    user_object = mongo_handler.mongo_utils.retrieve_user(user_email)
    session["registration_status"] = user_object['registration_status']
    if not user_object:
        logger.error('failed here')
        return '', {'user_email': user_email}
    session['user_email'] = user_email
    session['user_password'] = password
    logger.info(f'user_email is: {user_email}')
    try:
        session['first_name'] = user_object['first_name'].capitalize()
    except:
        logger.error('failed here')
        redirect(url_for('login',
                         failure_message=f'username or password were not found in the system '
                                         f' please try again'))
    if not user_email or not password:
        logger.error(f'no user_email or password were found')
        return render_template('login.html',
                               failure_message=f'{user_email} was not found in the system '
                                               f'or you provided a wrong password, please try again')
    try:
        if check_password_hash(user_object['hashed_password'], password):
            try:
                token = encode(
                    {'user_id': str(user_object['_id']),
                     'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=1440)},
                    app.config['SECRET_KEY'])
            except InvalidTokenError as error:
                logger.error(error)
                logger.info(f'Failed to create a token')
                token = ''
            session['x-access-token'] = token
            return token, user_object
        else:
            logger.error('The hashed password is incorrect')
            return '', user_object
    except:
        logger.error(f'The hashed password is incorrect')
        redirect(url_for('login',
                         failure_message=f'username or password were not found in the system '
                                         f' please try again'))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            login_processor()
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f'login_processor has failed with {e}')
            return render_template('login.html')

    return decorated_function


def validate_provider_data(content: dict) -> bool:
    try:
        retrieved_content = mongo_handler.mongo_utils.retrieve_provider_data_object(provider=content[PROVIDER],
                                                                                    user_email=content['user_email'],
                                                                                    decrypted=True)
        if content[PROVIDER] == AWS:
            try:
                if content[AWS_ACCESS_KEY_ID] and content[AWS_SECRET_ACCESS_KEY]:
                    return True
            except Exception as e:
                logger.warning(f'Requested content did not have the credentials. Checking the DB: {e}')
                if not retrieved_content[AWS_ACCESS_KEY_ID] or not retrieved_content[AWS_SECRET_ACCESS_KEY]:
                    return False
                else:
                    return True
        elif content[PROVIDER] == AZ:
            try:
                if content[AZURE_CREDENTIALS]:
                    return True
            except Exception as e:
                logger.warning(f'Requested content did not have the credentials. Checking the DB: {e}')
                if not retrieved_content[AZURE_CREDENTIALS]:
                    return False
                else:
                    return True
        elif content[PROVIDER] == GCP:
            try:
                if content[GOOGLE_CREDS_JSON]:
                    return True
            except Exception as e:
                logger.warning(f'Requested content did not have the credentials. Checking the DB: {e}')
                if not retrieved_content[GOOGLE_CREDS_JSON]:
                    return False
                else:
                    return True

    except Exception as e:
        logger.error(f"There was a problem validating provider data with error: {e}")


def render_page(page_name: str = '', cluster_name: str = '', client_name: str = ''):
    try:
        token, user_object = login_processor()
        base64_data = codecs.encode(user_object['profile_image'].read(), 'base64')
        is_login_pass = True
    except:
        is_login_pass = False
    if is_login_pass:
        data = {'user_name': user_object['user_name'], 'first_name': user_object['first_name'],
                'cluster_name': cluster_name, 'client_name': client_name, 'version': __version__}
        profile_image = base64_data.decode('utf-8')
        return render_template(page_name, data=data, image=profile_image)
    else:
        return render_template('login.html')


def aws_caching(user_email: str, project_name: str, aws_access_key_id: str, aws_secret_access_key: str,
                github_repository: str, github_actions_token: str, infracost_token: str) -> bool:
    """
    This endpoint triggers a EKS Cluster deployment using a GitHub Action
    """

    content = {'project_name': project_name, AWS_ACCESS_KEY_ID: aws_access_key_id,
               AWS_SECRET_ACCESS_KEY: aws_secret_access_key,
               GITHUB_REPOSITORY: github_repository, GITHUB_ACTIONS_TOKEN: github_actions_token,
               INFRACOST_TOKEN: infracost_token,
               'mongo_password': os.getenv('MONGO_PASSWORD'),
               'mongo_url': os.getenv('MONGO_URL'), 'mongo_user': os.getenv('MONGO_USER')}
    if not github_repository or not github_actions_token:
        github_data = mongo_handler.mongo_utils.retrieve_github_data_object(user_email)
        if not github_data:
            logger.warning(f'No github data for {user_email} user was found. AWS caching will not start')
            return True
        try:
            github_actions_token_decrypted = crypter.decrypt(github_data['github_actions_token']).decode("utf-8")
            github_repository = github_data['github_repository']
            content['github_repository'] = github_repository
            content['github_actions_token'] = github_actions_token_decrypted
        except Exception as e:
            logger.error(f'problem decrypting github_actions_token_decrypted with error {e}')
            return False
    if not infracost_token:
        infracost_token_data = mongo_handler.mongo_utils.retrieve_infracost_data_object(user_email)
        if not infracost_token_data:
            logger.warning(f'No infracost data for {user_email} user was found. AWS caching will start without Infracost data')
        else:
            try:
                infracost_token_decrypted = crypter.decrypt(infracost_token_data['infracost_token']).decode("utf-8")
                content['infracost_token'] = infracost_token_decrypted
            except Exception as e:
                logger.error(f'problem decrypting infracost_token_decrypted with error {e}')
                return False
    cluster_operation = ClusterOperation(**content)
    if cluster_operation.trigger_aws_caching():
        return True
    else:
        return False


def az_caching(user_email: str, project_name: str, azure_credentials: str, github_repository: str,
               github_actions_token: str, infracost_token: str) -> bool:
    """
    This endpoint triggers an AZ Cluster deployment using a GitHub Action
    """

    content = {'project_name': project_name, AZURE_CREDENTIALS: azure_credentials,
               GITHUB_REPOSITORY: github_repository, GITHUB_ACTIONS_TOKEN: github_actions_token,
               INFRACOST_TOKEN: infracost_token,
               'mongo_password': os.getenv('MONGO_PASSWORD'),
               'mongo_url': os.getenv('MONGO_URL'), 'mongo_user': os.getenv('MONGO_USER')}
    if not github_repository or not github_actions_token:
        github_data = mongo_handler.mongo_utils.retrieve_github_data_object(user_email)
        if not github_data:
            logger.warning(f'No github data for {user_email} user was found. AZ caching will not start')
            return True
        try:
            github_actions_token_decrypted = crypter.decrypt(github_data['github_actions_token']).decode("utf-8")
            github_repository = github_data['github_repository']
            content['github_repository'] = github_repository
            content['github_actions_token'] = github_actions_token_decrypted
        except Exception as e:
            logger.error(f'problem decrypting github_actions_token_decrypted with error {e}')
            return False
    if not infracost_token:
        infracost_token_data = mongo_handler.mongo_utils.retrieve_infracost_data_object(user_email)
        if not infracost_token_data:
            logger.warning(
                f'No infracost data for {user_email} user was found. AZ caching will start without Infracost data')
        else:
            try:
                infracost_token_decrypted = crypter.decrypt(infracost_token_data['infracost_token']).decode("utf-8")
                content['infracost_token'] = infracost_token_decrypted
            except Exception as e:
                logger.error(f'problem decrypting infracost_token_decrypted with error {e}')
                return False
    cluster_operation = ClusterOperation(**content)
    if cluster_operation.trigger_az_caching():
        return True
    else:
        return False


def gcp_caching(user_email: str, project_name: str, google_creds_json: str, github_repository: str,
                github_actions_token: str, infracost_token: str) -> bool:
    """
    This endpoint triggers a GCP Caching Action using a GitHub Action
    """
    content = {'project_name': project_name, GOOGLE_CREDS_JSON: google_creds_json,
               GITHUB_REPOSITORY: github_repository, GITHUB_ACTIONS_TOKEN: github_actions_token,
               INFRACOST_TOKEN: infracost_token,
               'mongo_password': os.getenv('MONGO_PASSWORD'),
               'mongo_url': os.getenv('MONGO_URL'), 'mongo_user': os.getenv('MONGO_USER')}
    if not github_repository or not github_actions_token:
        github_data = mongo_handler.mongo_utils.retrieve_github_data_object(user_email)
        if not github_data:
            logger.warning(f'No github data for {user_email} user was found. GCP caching will not start')
            return True
        try:
            github_actions_token_decrypted = crypter.decrypt(github_data['github_actions_token']).decode("utf-8")
            github_repository = github_data['github_repository']
            content['github_repository'] = github_repository
            content['github_actions_token'] = github_actions_token_decrypted
        except Exception as e:
            logger.error(f'problem decrypting github_actions_token_decrypted with error {e}')
            return False
    if not infracost_token:
        infracost_token_data = mongo_handler.mongo_utils.retrieve_infracost_data_object(user_email)
        if not infracost_token_data:
            logger.warning(f'No infracost data for {user_email} user was found. GCP caching will start without Infracost data')
        else:
            try:
                infracost_token_decrypted = crypter.decrypt(infracost_token_data['infracost_token']).decode("utf-8")
                content['infracost_token'] = infracost_token_decrypted
            except Exception as e:
                logger.error(f'problem decrypting infracost_token_decrypted with error {e}')
                return False
    cluster_operation = ClusterOperation(**content)
    if cluster_operation.trigger_gcp_caching():
        return True
    else:
        return False


@app.route('/get_clusters_data', methods=[GET])
@login_required
def get_clusters_data():
    """
    Ths endpoint allows providing basic clusters data that was gathered upon the clusters' creation.
    """
    cluster_type = request.args.get(CLUSTER_TYPE)
    client_name = request.args.get(CLIENT_NAME.lower())
    user_name = request.args.get(USER_NAME.lower())
    if user_name == 'null':
        user_name = ''
    clusters_list = mongo_handler.mongo_utils.retrieve_available_clusters(cluster_type, client_name, user_name)
    clusters_decrypted = []
    for cluster in clusters_list:
        try:
            kubeconfig_decrypted = crypter.decrypt(cluster['kubeconfig']).decode("utf-8")
            cluster['kubeconfig'] = kubeconfig_decrypted
        except Exception as e:
            logger.warning(f'Cluster did not have encrypted kubeconfig: {e}')
        clusters_decrypted.append(cluster)
    if len(clusters_decrypted) == 0:
        return jsonify([]), 200
    else:
        return Response(json.dumps(clusters_list), status=200, mimetype=APPLICATION_JSON)


@app.route('/get_instances_data', methods=[GET])
@login_required
def get_instances_data():
    """
    Ths endpoint allows providing basic instances data that was gathered.
    """
    provider_type = request.args.get(PROVIDER)
    client_name = request.args.get(CLIENT_NAME.lower())
    user_name = request.args.get(USER_NAME.lower())
    instances_list = mongo_handler.mongo_utils.retrieve_instances(provider_type, client_name, user_name)
    return Response(json.dumps(instances_list), status=200, mimetype=APPLICATION_JSON)


@app.route('/get_agent_cluster_data', methods=[GET])
@login_required
def get_agent_cluster_data():
    """
    This endpoint allows providing an additional cluster data that is being collected by the deployed Trolley Agent
    """
    cluster_name = request.args.get(CLUSTER_NAME.lower())
    cluster_object = mongo_handler.mongo_utils.retrieve_agent_cluster_details(cluster_name)
    return Response(json.dumps(cluster_object), status=200, mimetype=APPLICATION_JSON)


@app.route('/trigger_cloud_provider_discovery', methods=[POST])
@login_required
def trigger_cloud_provider_discovery():
    """
    This endpoint allows triggering a cloud provider discovery
    """
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    if AWS in content[PROVIDER]:
        if content[OBJECT_TYPE] == CLUSTER:
            Thread(target=aws_discovery_script.main, args=(False, False, False, True)).start()
        if content[OBJECT_TYPE] == INSTANCE:
            Thread(target=aws_discovery_script.main, args=(False, False, True, False)).start()
    elif GCP in content[PROVIDER]:
        if content[OBJECT_TYPE] == CLUSTER:
            Thread(target=gcp_discovery_script.main, args=(False, False, False, True, session['user_email'])).start()
        if content[OBJECT_TYPE] == INSTANCE:
            Thread(target=gcp_discovery_script.main, args=(False, False, True, False, session['user_email'])).start()
    elif 'az' in content[PROVIDER]:
        if content[OBJECT_TYPE] == CLUSTER:
            Thread(target=az_discovery_script.main, args=(True, session['user_email'])).start()
    return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)


@app.route('/deploy_yaml_on_cluster', methods=[POST])
@login_required
def deploy_yaml_on_cluster():
    """
    This endpoint allows delivering a custom deployment using a YAML that was provided for a cluster
    """
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    with open('trolley_service.yaml', "r") as f:
        yaml_content = f.read().strip()
    deployment_yaml = yaml.safe_load(yaml_content)
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    if apply_yaml(content[CLUSTER_TYPE], content[CLUSTER_NAME.lower()], deployment_yaml):
        return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
    else:
        return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)


@app.route('/deploy_trolley_agent_on_cluster', methods=[POST])
@login_required
def deploy_trolley_agent_on_cluster():
    """
    This endpoint allows triggering a Trolley Agent deployment on a cluster
    """
    content = request.get_json()
    content['mongo_password'] = os.getenv('MONGO_PASSWORD')
    content['mongo_url'] = os.getenv('MONGO_URL')
    content['mongo_user'] = os.getenv('MONGO_USER')
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    cluster_operation = ClusterOperation(**content)
    if cluster_operation.trigger_trolley_agent_deployment_github_action():
        return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
    else:
        return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)


@app.route('/trigger_gke_deployment', methods=[POST])
@login_required
def trigger_gke_deployment():
    """
    This endpoint triggers a GKE Cluster deployment
    """
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    user_name = content['user_name']
    cluster_name = f'{user_name}-{GKE}-{random_string(8)}'
    gcp_project_id = json.loads(content[GOOGLE_CREDS_JSON])['project_id']
    content[GCP_PROJECT_ID] = gcp_project_id
    content['cluster_name'] = cluster_name
    content['project_name'] = PROJECT_NAME
    content['mongo_url'] = MONGO_URL
    content['mongo_user'] = MONGO_USER
    content['mongo_password'] = MONGO_PASSWORD
    cluster_operation = ClusterOperation(**content)
    if cluster_operation.trigger_gke_build_github_action():
        return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
    else:
        return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)


@app.route('/trigger_eks_deployment', methods=[POST])
@login_required
def trigger_eks_deployment():
    """
    This endpoint triggers an EKS Cluster deployment
    """
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    user_name = content['user_name']
    cluster_name = f'{user_name}-{EKS}-{random_string(8)}'
    content['secret_key'] = secret_key
    content['cluster_name'] = cluster_name
    content['project_name'] = PROJECT_NAME
    content['mongo_url'] = MONGO_URL
    content['mongo_user'] = MONGO_USER
    content['mongo_password'] = MONGO_PASSWORD
    cluster_operation = ClusterOperation(**content)
    cluster_operation.build_eksctl_object()
    if cluster_operation.trigger_eks_build_github_action():
        return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
    else:
        return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)


@app.route('/trigger_aks_deployment', methods=[POST])
@login_required
def trigger_aks_deployment():
    """
    This endpoint allows a AKS Cluster deployment
    """
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    user_name = content['user_name']
    cluster_name = f'{user_name}-{AKS}-{random_string(8)}'
    content['cluster_name'] = cluster_name
    content['project_name'] = PROJECT_NAME
    content['mongo_url'] = MONGO_URL
    content['mongo_user'] = MONGO_USER
    content['mongo_password'] = MONGO_PASSWORD
    content['az_subscription_id'] = json.loads(content[AZURE_CREDENTIALS])['subscriptionId']
    content['az_machine_type'] = "standard_" + content['az_machine_type'].lower()
    cluster_operation = ClusterOperation(**content)
    if cluster_operation.trigger_aks_build_github_action():
        return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)


# @app.route('/delete_expired_clusters', methods=[DELETE])
# @login_required
# def delete_expired_clusters():
#     """
#     Ths endpoint allows deletion of clusters that passed their expiration time
#     """
#     content = request.get_json()
#     expired_clusters_list = mongo_handler.mongo_utils.retrieve_expired_clusters(cluster_type=content['cluster_type'])
#     for expired_cluster in expired_clusters_list:
#         delete_gke_cluster(cluster_name=expired_cluster['cluster_name'])
#         time.sleep(5)
#         mongo_handler.mongo_utils.set_cluster_availability(cluster_type=content['cluster_type'],
#                                                            cluster_name=content['cluster_name'],
#                                                            availability=False)
#     return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)


@app.route('/delete_cluster', methods=[DELETE])
@login_required
def delete_cluster():
    """
    This request deletes a selected cluster
    """
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    content['project_name'] = PROJECT_NAME
    content['mongo_url'] = MONGO_URL
    content['mongo_user'] = MONGO_USER
    content['mongo_password'] = MONGO_PASSWORD
    if content[CLUSTER_TYPE] == GKE:
        pass
    elif content[CLUSTER_TYPE] == EKS:
        pass
    elif content[CLUSTER_TYPE] == AKS:
        content['az_subscription_id'] = json.loads(content[AZURE_CREDENTIALS])['subscriptionId']
        az_resource_group = \
            mongo_handler.mongo_utils.retrieve_cluster_details(content[CLUSTER_TYPE], content[CLUSTER_NAME.lower()],
                                                               content[DISCOVERED])['az_resource_group']
        content[AZ_RESOURCE_GROUP] = az_resource_group
    cluster_operations = ClusterOperation(**content)
    if content[CLUSTER_TYPE] == GKE:
        cluster_operations.delete_gke_cluster()
    elif content[CLUSTER_TYPE] == EKS:
        cluster_operations.delete_eks_cluster()
    elif content[CLUSTER_TYPE] == AKS:
        cluster_operations.delete_aks_cluster()
    return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)


@app.route('/insert_cluster_data', methods=[POST])
@login_required
def insert_cluster_data():
    """
    This endpoint inserts data provided by a Trolley Agent
    """
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested')
    if content['agent_type'] == 'k8s':
        if mongo_handler.mongo_utils.insert_cluster_data_object(content):
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    elif content['agent_type'] == 'aws':
        if mongo_handler.mongo_utils.insert_cluster_data_object(content):
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)


@app.route('/trigger_provider_sync', methods=[GET, POST])
@login_required
def trigger_provider_sync():
    if request.method == POST:
        user_email = session['user_email']
        content = request.get_json()
        provider = content[PROVIDER]
        credentials_data = mongo_handler.mongo_utils.retrieve_provider_data_object(user_email, provider, decrypted=True)
        infracost_data = mongo_handler.mongo_utils.retrieve_infracost_data_object(user_email, decrypted=True)
        github_data = mongo_handler.mongo_utils.retrieve_github_data_object(user_email, decrypted=True)
        if provider == AWS:
            if aws_caching(user_email=user_email, project_name=PROJECT_NAME,
                           aws_access_key_id=credentials_data[AWS_ACCESS_KEY_ID],
                           aws_secret_access_key=credentials_data[AWS_SECRET_ACCESS_KEY],
                           github_repository=github_data[GITHUB_REPOSITORY],
                           github_actions_token=github_data[GITHUB_ACTIONS_TOKEN],
                           infracost_token=infracost_data[INFRACOST_TOKEN]):
                return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
            else:
                return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
        elif provider == AZ:
            if az_caching(user_email=user_email, project_name=PROJECT_NAME,
                          azure_credentials=credentials_data[AZURE_CREDENTIALS],
                          github_repository=github_data[GITHUB_REPOSITORY],
                          github_actions_token=github_data[GITHUB_ACTIONS_TOKEN],
                          infracost_token=infracost_data[INFRACOST_TOKEN]):
                return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
            else:
                return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
        elif provider == GCP:
            if gcp_caching(user_email=user_email, project_name=PROJECT_NAME,
                           google_creds_json=credentials_data[GOOGLE_CREDS_JSON],
                           github_repository=github_data[GITHUB_REPOSITORY],
                           github_actions_token=github_data[GITHUB_ACTIONS_TOKEN],
                           infracost_token=infracost_data[INFRACOST_TOKEN]):
                return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
            else:
                return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
        return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)


@app.route('/settings', methods=[GET, POST])
@login_required
def settings():
    """
    This endpoint saves Trolley settings and initiates a cloud scan if the provided credentials are correct
    """
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested')
    try:
        user_email = session['user_email']
    except Exception as e:
        logger.error(f'Trouble fetching user_email using a session. error: {e}')
        user_email = ''
    if request.method == POST:
        content = request.get_json()
        content['user_email'] = session['user_email']
        cluster_operation = ClusterOperation(**content)
        if content['github_repository'] and content['github_actions_token']:
            if cluster_operation.github_check():
                encoded_github_details = encode_github_details(content)
                mongo_handler.mongo_utils.insert_github_data_object(asdict(encoded_github_details))
            else:
                return Response(json.dumps('Failure to authenticate with GitHub'), status=400, mimetype=APPLICATION_JSON)
        if content['infracost_token']:
            if cluster_operation.infracost_check():
                encoded_infracost_token = encode_infracost_details(content)
                mongo_handler.mongo_utils.insert_infracost_data_object(asdict(encoded_infracost_token))

        # TODO find a better way to implement
        settings_keys = check_settings_keys(content)
        if validate_provider_data(content):
            if content[PROVIDER] == GCP and GOOGLE_CREDS_JSON in settings_keys:
                credentials = content[GOOGLE_CREDS_JSON]
                gcp_project_id = json.loads(credentials)['project_id']
                content[GCP_PROJECT_ID] = gcp_project_id
                encoded_provider_details = encode_provider_details(content)
                try:
                    mongo_handler.mongo_utils.insert_provider_data_object(asdict(encoded_provider_details))
                except Exception as e:
                    logger.error(f'Failed to insert the data provider with error: {e}')
                if gcp_caching(user_email, PROJECT_NAME, content[GOOGLE_CREDS_JSON],
                               github_repository=content[GITHUB_REPOSITORY],
                               github_actions_token=content[GITHUB_ACTIONS_TOKEN],
                               infracost_token=content[INFRACOST_TOKEN]):
                    return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
                else:
                    return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
            elif content[PROVIDER] == AWS \
                    and AWS_ACCESS_KEY_ID in settings_keys and AWS_SECRET_ACCESS_KEY in settings_keys:
                encoded_provider_details = encode_provider_details(content)
                try:
                    mongo_handler.mongo_utils.insert_provider_data_object(asdict(encoded_provider_details))
                except Exception as e:
                    logger.error(f'Failed to insert the data provider with error: {e}')
                if aws_caching(user_email, PROJECT_NAME, content[AWS_ACCESS_KEY_ID],
                               content[AWS_SECRET_ACCESS_KEY],
                               github_repository=content[GITHUB_REPOSITORY],
                               github_actions_token=content[GITHUB_ACTIONS_TOKEN],
                               infracost_token=content[INFRACOST_TOKEN]):
                    return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
                else:
                    return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
            elif content[PROVIDER] == AZ and AZURE_CREDENTIALS in settings_keys:
                encoded_provider_details = encode_provider_details(content)
                try:
                    mongo_handler.mongo_utils.insert_provider_data_object(asdict(encoded_provider_details))
                except Exception as e:
                    logger.error(f'Failed to insert the data provider with error: {e}')
                if az_caching(user_email, PROJECT_NAME, content[AZURE_CREDENTIALS],
                              github_repository=content[GITHUB_REPOSITORY],
                              github_actions_token=content[GITHUB_ACTIONS_TOKEN],
                              infracost_token=content[INFRACOST_TOKEN]):
                    return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
                else:
                    return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
            else:
                return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
    elif request.method == GET:
        github_data = mongo_handler.mongo_utils.retrieve_github_data_object(user_email)
        infracost_data = mongo_handler.mongo_utils.retrieve_infracost_data_object(user_email)
        aws_credentials_data = mongo_handler.mongo_utils.retrieve_credentials_data_object(provider=AWS,
                                                                                          user_email=user_email)
        az_credentials_data = mongo_handler.mongo_utils.retrieve_credentials_data_object(provider=AZ,
                                                                                         user_email=user_email)
        gcp_credentials_data = mongo_handler.mongo_utils.retrieve_credentials_data_object(provider=GCP,
                                                                                          user_email=user_email)
        try:
            github_actions_token_decrypted = crypter.decrypt(github_data['github_actions_token']).decode("utf-8")
            github_repository = github_data['github_repository']
        except Exception as e:
            github_actions_token_decrypted = ""
            github_repository = ""
            logger.warning(f'problem decrypting github_actions_token_decrypted with error {e}')

        try:
            infracost_token_decrypted = crypter.decrypt(infracost_data['infracost_token']).decode("utf-8")
        except Exception as e:
            infracost_token_decrypted = ""
            logger.warning(f'problem decrypting infracost_token_decrypted with error {e}')
        try:
            aws_access_key_id = crypter.decrypt(aws_credentials_data[AWS_ACCESS_KEY_ID]).decode("utf-8")
            aws_secret_access_key = crypter.decrypt(aws_credentials_data[AWS_SECRET_ACCESS_KEY]).decode("utf-8")
        except Exception as e:
            aws_access_key_id = ""
            aws_secret_access_key = ""
            logger.warning(f'problem decrypting aws credentials with error {e}')
        try:
            azure_credentials = crypter.decrypt(az_credentials_data[AZURE_CREDENTIALS]).decode("utf-8")
        except Exception as e:
            azure_credentials = ""
            logger.warning(f'problem decrypting azure credentials with error {e}')
        try:
            google_creds_json = crypter.decrypt(gcp_credentials_data[GOOGLE_CREDS_JSON]).decode("utf-8")
        except Exception as e:
            google_creds_json = ""
            logger.warning(f'problem decrypting google credentials with error {e}')

        return jsonify({AWS_ACCESS_KEY_ID: aws_access_key_id,
                        AWS_SECRET_ACCESS_KEY: aws_secret_access_key,
                        AZURE_CREDENTIALS: azure_credentials,
                        GOOGLE_CREDS_JSON: google_creds_json,
                        'github_actions_token': github_actions_token_decrypted,
                        'infracost_token': infracost_token_decrypted,
                        'github_repository': github_repository})


@app.route('/clients', methods=[GET, POST, PUT, DELETE])
@login_required
def client():
    """
    This endpoint adds/gets and deletes a client data
    """
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested')
    if request.method == POST:
        content = request.get_json()
        if mongo_handler.mongo_utils.add_client_data_object(content):
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    elif request.method == PUT:
        content = request.get_json()
        if content[OBJECT_TYPE] == CLUSTER:
            if mongo_handler.mongo_utils.add_data_to_cluster(**content):
                return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
            else:
                return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
        elif content[OBJECT_TYPE] == INSTANCE:
            if mongo_handler.mongo_utils.add_data_to_instance(**content):
                return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
            else:
                return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    elif request.method == DELETE:
        content = request.get_json()
        if mongo_handler.mongo_utils.delete_client(**content):
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    elif request.method == GET:
        client_names = mongo_handler.mongo_utils.retrieve_clients_data()
        return jsonify(sorted(client_names, key=lambda d: d['client_name']))


@app.route('/users', methods=[GET, POST, PUT, DELETE])
@login_required
def users():
    """
    This endpoint adds/gets a new user
    """
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested')
    if request.method == POST:
        content = request.get_json()
        if mongo_handler.mongo_utils.invite_user(content):
            mail_message = MailSender(content['user_email'])
            mail_message.send_invitation_mail()
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    elif request.method == GET:
        logged_user_name = request.args.get('logged_user_name')
        logger.info(f'logged_user_name is {logged_user_name}')
        users_data = mongo_handler.mongo_utils.retrieve_users_data(logged_user_name)
        return jsonify(sorted(users_data, key=lambda d: d['user_name']))
    elif request.method == DELETE:
        content = request.get_json()
        user_name = content[USER_NAME.lower()]
        users_data = mongo_handler.mongo_utils.delete_user(user_name=user_name)
        return jsonify(users_data)


@app.route('/teams', methods=[GET, POST, PUT, DELETE])
@login_required
def teams():
    """
    This endpoint adds and gets teams
    """
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested')
    if request.method == POST:
        content = request.get_json()
        if mongo_handler.mongo_utils.insert_team(content):
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    elif request.method == GET:
        teams_data = mongo_handler.mongo_utils.retrieve_teams_data()
        return jsonify(sorted(teams_data, key=lambda d: d['team_name']))
    elif request.method == DELETE:
        content = request.get_json()
        team_name = content[TEAM_NAME.lower()]
        if mongo_handler.mongo_utils.delete_team(team_name=team_name):
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)


@app.route('/healthz', methods=[GET, POST])
def healthz():
    logger.info('A request was received')
    return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)


@app.route('/', methods=[GET, POST])
def root():
    return render_page('index.html')


@app.route('/index', methods=[GET, POST])
def index():
    return render_page('index.html')


@app.route('/fetch_regions', methods=[GET])
@login_required
def fetch_regions():
    cluster_type = request.args.get(CLUSTER_TYPE)
    logger.info(f'A request to fetch regions for {cluster_type} has arrived')
    if cluster_type == AKS:
        regions = mongo_handler.mongo_utils.retrieve_cache(cache_type=LOCATIONS_DICT, provider=AKS)
        return jsonify(regions), 200
    elif cluster_type == GKE:
        regions = mongo_handler.mongo_utils.retrieve_cache(cache_type=REGIONS_LIST, provider=GKE)
    elif cluster_type == EKS:
        regions = mongo_handler.mongo_utils.retrieve_cache(cache_type=REGIONS_LIST, provider=EKS)
    else:
        regions = mongo_handler.mongo_utils.retrieve_cache(cache_type=REGIONS_LIST, provider=GKE)
    if len(regions) == 0:
        return jsonify("Regions data was not found"), 200
    else:
        return jsonify(sorted(regions)), 200


@app.route('/fetch_kubernetes_versions', methods=[GET])
@login_required
def fetch_kubernetes_versions():
    cluster_type = request.args.get(CLUSTER_TYPE.lower())
    location_name = request.args.get(LOCATION_NAME.lower())
    logger.info(f'A request to fetch kubernetes versions for {cluster_type} and {location_name} location has arrived')
    kubernetes_versions_list = mongo_handler.mongo_utils.retrieve_kubernetes_versions(location_name=location_name,
                                                                                      provider=cluster_type)
    if len(kubernetes_versions_list) == 0:
        return jsonify("kubernetes_versions_list data was not found"), 200
    else:
        return kubernetes_versions_list


@app.route('/fetch_machine_series', methods=[GET])
@login_required
def fetch_machine_series():
    cluster_type = request.args.get(CLUSTER_TYPE)
    region_name = request.args.get(REGION_NAME.lower())
    logger.info(f'A request to fetch machine series for {cluster_type} has arrived')
    machine_series = mongo_handler.mongo_utils.retrieve_machine_series(region_name=region_name,
                                                                       cluster_type=cluster_type)
    return jsonify(sorted(machine_series))


@app.route('/fetch_machine_types', methods=[GET])
@login_required
def fetch_machine_types():
    cluster_type = request.args.get(CLUSTER_TYPE)
    machine_series = request.args.get(MACHINE_SERIES.lower())
    region_name = request.args.get(REGION_NAME.lower())
    logger.info(f'A request to fetch machine types for {cluster_type} has arrived')
    machine_types = mongo_handler.mongo_utils.retrieve_machine_types(machine_series=machine_series,
                                                                     cluster_type=cluster_type, region_name=region_name)
    if machine_types:
        return Response(json.dumps(machine_types), status=200, mimetype=APPLICATION_JSON)
    else:
        return jsonify([]), 200


@app.route('/fetch_zones', methods=[GET])
@login_required
def fetch_zones():
    cluster_type = request.args.get(CLUSTER_TYPE)
    region_name = request.args.get(REGION_NAME.lower())
    logger.info(f'A request to fetch zones for {cluster_type} has arrived')
    zones_list = []
    if cluster_type == AKS:
        return jsonify('')
    elif cluster_type == GKE:
        gke_zones = mongo_handler.mongo_utils.retrieve_cache(cache_type=ZONES_LIST, provider=GKE)
        for zone in gke_zones:
            if region_name in zone:
                zones_list.append(zone)
        return jsonify(zones_list)
    elif cluster_type == EKS:
        eks_zones = mongo_handler.mongo_utils.retrieve_cache(cache_type=ZONES_LIST, provider=EKS)
        available_eks_zones = []
        for eks_zone in eks_zones:
            if region_name in eks_zone:
                available_eks_zones.append(eks_zone)
        return jsonify(available_eks_zones)


@app.route('/fetch_subnets', methods=[GET])
@login_required
def fetch_subnets():
    cluster_type = request.args.get(CLUSTER_TYPE)
    zone_names = request.args.get(ZONE_NAMES.lower())
    logger.info(f'A request to fetch zone_names for {cluster_type} has arrived')
    if cluster_type == AKS:
        return jsonify('')
    elif cluster_type == GKE:
        return jsonify('')
    elif cluster_type == EKS:
        subnets = []
        subnets_dict = mongo_handler.mongo_utils.retrieve_cache(cache_type='subnets_dict', provider=EKS)
        for subnet in subnets_dict:
            if subnet in zone_names:
                subnets.append(subnets_dict[subnet])
        if len(subnets[0]) < 1:
            return jsonify([f'No subnets were found for {zone_names} zones'])
        else:
            return jsonify(subnets)


@app.route('/fetch_client_name_per_cluster', methods=[GET])
@login_required
def fetch_client_name_per_cluster():
    cluster_type = request.args.get(CLUSTER.lower())
    cluster_name = request.args.get(CLUSTER_NAME.lower())
    client_names = mongo_handler.mongo_utils.retrieve_client_per_cluster_name(cluster_type, cluster_name)
    return jsonify(client_names)


@app.route('/fetch_gke_versions', methods=[GET])
@login_required
def fetch_gke_versions():
    gke_versions_list = mongo_handler.mongo_utils.retrieve_cache(cache_type=GKE_VERSIONS_LIST, provider=GKE)
    return jsonify(gke_versions_list)


# @app.route('/fetch_aks_versions', methods=[GET])
# # @login_required
# def fetch_aks_versions():
#     location_name = request.args.get(LOCATION_NAME.lower())
#     logger.info(f'A request to fetch kubernetes versions for {location_name} location has arrived')
#     kubernetes_versions_list = mongo_handler.mongo_utils.retrieve_kubernetes_versions(location_name=location_name, provider=AKS)
#     if len(kubernetes_versions_list) == 0:
#         return jsonify("kubernetes_versions_list data was not found"), 200
#     else:
#         return kubernetes_versions_list

@app.route('/fetch_gke_image_types', methods=[GET])
@login_required
def fetch_gke_image_types():
    logger.info(f'A request to fetch available GKE image types has arrived')
    gke_image_types_list = mongo_handler.mongo_utils.retrieve_cache(cache_type=GKE_IMAGE_TYPES, provider=GKE)
    return jsonify(gke_image_types_list)


@app.route('/fetch_az_resource_groups', methods=[GET])
# @login_required
def fetch_az_resource_groups():
    logger.info(f'A request to fetch available EKS resource groups has arrived')
    location = request.args.get(LOCATION_NAME.lower())
    az_resource_groups = mongo_handler.mongo_utils.retrieve_az_resource_groups(location=location)
    if az_resource_groups:
        return jsonify(az_resource_groups), 200
    else:
        return jsonify([]), 200


@app.route('/register', methods=[GET, POST])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        first_name = request.form['first_name'].lower()
        last_name = request.form['last_name'].lower()
        user_email = request.form['user_email']
        if '@' not in user_email:
            return render_template('register.html',
                                   error_message=f'Dear {first_name}, your email was not entered correctly. '
                                                 f'Please try again')
        invited_user = mongo_handler.mongo_utils.retrieve_invited_user(user_email)
        try:
            user_type = invited_user['user_type']
        except:
            user_type = 'user'
        if not user_type:
            user_type = 'user'
        if invited_user:
            team_name = invited_user['team_name']
        else:
            team_name = 'none'
        password = request.form['password']
        if 'image' not in request.files['file'].mimetype:
            image_file_name = 'thumbnail_trolley_small.png'
        else:
            cur_dir = os.getcwd()
            if " " in first_name:
                first_name = first_name.replace(" ", "_")
            if " " in last_name:
                last_name = last_name.replace(" ", "_")
            profile_image = request.files['file']
            image_extension = profile_image.mimetype.split('/')[1]
            image_file_name = f'thumbnail_{first_name}_{last_name}.{image_extension}'
            thumbnail_file_path = f'{cur_dir}/static/img/{image_file_name}'
            logger.info(f'Saving the thumbnail in {thumbnail_file_path} path')
            full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file_name)
            full_thumbnail_file_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_file_path)
            logger.info(f'Or maybe saving the thumbnail in {full_thumbnail_file_path} full_thumbnail_file_path')
            FileStorage(profile_image.save(full_file_path))
            image = Image.open(full_file_path)
            new_image = image.resize((192, 192))
            new_image.save(full_thumbnail_file_path)

        if not first_name:
            return render_template('register.html',
                                   error_message=f'Dear {first_name}, your first name was not entered correctly. '
                                                 f'Please try again')
        if not last_name:
            return render_template('register.html',
                                   error_message=f'Dear {first_name}, your last name was not entered correctly. '
                                                 f'Please try again')
        if not password:
            return render_template('register.html',
                                   error_message=f'Dear {first_name}, your password was not entered correctly. '
                                                 f'Please try again')
        else:
            if not mongo_handler.mongo_utils.retrieve_user(user_email):
                token = generate_confirmation_token(user_email)
                logger.info(f'token is: {token}')
                confirmation_url = str(url_for('confirmation_email', token=token, _external=True))
                logger.info(f'confirmation_url is: {confirmation_url}')
                if EMAIL_AUTHENTICATION:
                    mail_message = MailSender(user_email, confirmation_url)
                    try:
                        mail_message.send_confirmation_mail()
                    except Exception as e:
                        logger.error(f'Failed to send an email due to {e} error to {user_email}')

                if user_registration(first_name, last_name, password, user_email, user_type, team_name, image_file_name,
                                     confirmation_url, registration_status='pending'):
                    return render_template('confirmation.html', email=user_email, url=confirmation_url)
                else:
                    return render_template('confirmation.html', email=user_email, url=confirmation_url)
            else:
                return render_template('register.html',
                                       error_message=f'Dear {first_name}, your email was already registered. '
                                                     f'Please try again')


@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')


@app.route('/confirm/<token>')
def confirmation_email(token):
    user_email = confirm_token(token)
    if user_email:
        mongo_handler.mongo_utils.update_user_registration_status(user_email=user_email,
                                                                  registration_status='confirmed')

        return redirect(url_for('login'))


@app.route('/login', methods=[GET, POST])
@login_required
def login():
    if request.method == 'POST':
        token, user_object = login_processor(new=True)
        base64_data = codecs.encode(user_object['profile_image'].read(), 'base64')
        profile_image = base64_data.decode('utf-8')
        if token:
            user_email = user_object['user_email']
            user_type = mongo_handler.mongo_utils.check_user_type(user_email)
            data = {'user_name': user_object['user_name'], 'first_name': user_object['first_name'],
                    'user_type': user_type, 'version': __version__}
            logger.info(f'data content is: {data}')
            return render_template('index.html', data=data, image=profile_image)
        else:
            user_email = user_object['user_email']
            logger.info(f'user_email is: {user_email}')
            return render_template('login.html',
                                   error_message=f'Dear {user_email}, your password was not entered correctly. '
                                                 f'Please try again')
    message = request.args.get('message')
    logger.info(f'a login request was received with {message} message')
    if session['registration_status'] != 'confirmed':
        first_name = session['first_name']
        user_email = session['user_email']
        token = generate_confirmation_token(user_email)
        confirm_url = str(url_for('confirmation_email', token=token, _external=True))
        mail_message = MailSender(user_email, confirm_url)
        mail_message.send_confirmation_mail()
        mongo_handler.mongo_utils.update_user(user_email, update_type="confirmation_url", update_value=confirm_url)
        return render_template('login.html',
                               error_message=f'Dear {first_name}! '
                                             f'A confirmation mail was sent to {user_email} and was not confirmed. '
                                             f'Sending you another one!')
    elif session['registration_status'] == 'confirmed':
        return render_template('index.html')


@app.route('/build-eks-clusters', methods=[GET, POST])
@login_required
def build_eks_clusters():
    return render_page('build-eks-clusters.html')


@app.route('/build-aks-clusters', methods=[GET, POST])
@login_required
def build_aks_clusters():
    return render_page('build-aks-clusters.html')


@app.route('/build-gke-clusters', methods=[GET, POST])
@login_required
def build_gke_clusters():
    return render_page('build-gke-clusters.html')


@app.route('/manage-eks-clusters', methods=[GET, POST])
@login_required
def manage_eks_clusters():
    return render_page('manage-eks-clusters.html')


@app.route('/manage-aks-clusters', methods=[GET, POST])
@login_required
def manage_aks_clusters():
    return render_page('manage-aks-clusters.html')


@app.route('/manage-gke-clusters', methods=[GET, POST])
@login_required
def manage_gke_clusters():
    return render_page('manage-gke-clusters.html')


@app.route('/manage-aws-ec2-instances', methods=[GET, POST])
@login_required
def manage_aws_ec2_instances():
    return render_page('manage-aws-ec2-instances.html')


@app.route('/manage-gcp-vm-instances', methods=[GET, POST])
@login_required
def manage_gcp_vm_instances():
    return render_page('manage-gcp-vm-instances.html')


@app.route('/manage-az-vm-instances', methods=[GET, POST])
@login_required
def manage_az_vm_instances():
    return render_page('manage-az-vm-instances.html')


@app.route('/manage-settings', methods=[GET, POST])
@login_required
def manage_settings():
    return render_page('manage-settings.html')


@app.route('/clusters-data', methods=[GET])
@login_required
def clusters_data():
    try:
        cluster_name = request.values['cluster_name']
    except:
        cluster_name = 'nothing'
    return render_page('clusters-data.html', cluster_name=cluster_name)


@app.route('/manage-users', methods=[GET, POST])
@login_required
def manage_users():
    return render_page('manage-users.html')


@app.route('/manage-teams', methods=[GET, POST])
@login_required
def manage_teams():
    return render_page('manage-teams.html')


@app.route('/manage-clients', methods=[GET, POST])
@login_required
def manage_clients():
    return render_page('manage-clients.html')


@app.route('/client-data', methods=[GET, POST])
@login_required
def client_data():
    try:
        client_name = request.values['client_name']
    except:
        client_name = 'nothing'
    return render_page('client-data.html', client_name=client_name)


@app.route('/namespaces-data', methods=[GET, POST])
@login_required
def namespaces_data():
    cluster_name = request.values['cluster_name']
    return render_page('namespaces-data.html', cluster_name=cluster_name)


@app.route('/products-dashboards', methods=[GET, POST])
@login_required
def products_dashboards():
    return render_page('products-dashboards.html')


@app.route('/events-dashboards', methods=[GET, POST])
@login_required
def events_dashboards():
    return render_page('events-dashboards.html')


@app.route('/logout', methods=[GET, POST])
@login_required
def logout():
    session.pop('x-access-token', None)
    session.pop('user_email', None)
    session.pop('user_password', None)
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
    # app.run(host='0.0.0.0', port=8080, debug=True)
