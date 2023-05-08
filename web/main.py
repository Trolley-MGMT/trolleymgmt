import codecs
import inspect
import json
import logging
import os
import time
import datetime
from functools import wraps
from threading import Thread

from dataclasses import asdict
from distutils import util

from cryptography.fernet import Fernet
from flask import request, Response, Flask, session, redirect, url_for, render_template, jsonify
from itsdangerous import URLSafeTimedSerializer
from jwt import encode, InvalidTokenError
from PIL import Image
import yaml
from werkzeug.datastructures import FileStorage
from werkzeug.security import generate_password_hash, check_password_hash

import web.mongo_handler.mongo_utils
from web.mongo_handler.mongo_objects import UserObject, DeploymentYAMLObject
from web.variables.variables import POST, GET, EKS, \
    APPLICATION_JSON, CLUSTER_TYPE, GKE, AKS, DELETE, USER_NAME, MACOS, REGIONS_LIST, \
    ZONES_LIST, HELM_INSTALLS_LIST, GKE_VERSIONS_LIST, GKE_IMAGE_TYPES, HELM, LOCATIONS_DICT, \
    CLUSTER_NAME, AWS, PROVIDER, GCP, AZ, PUT, OK, FAILURE, OBJECT_TYPE, CLUSTER, INSTANCE, TEAM_NAME, ZONE_NAMES, \
    NAMES, REGION_NAME, CLIENT_NAME
from web.cluster_operations import trigger_gke_build_github_action, trigger_eks_build_github_action, \
    trigger_aks_build_github_action, delete_gke_cluster, delete_eks_cluster, delete_aks_cluster, \
    trigger_trolley_agent_deployment_github_action
from web.mail_handler import MailSender
from web.utils import random_string, apply_yaml
from web.mongo_handler.mongo_objects import ProviderObject
from web.scripts import gcp_discovery_script, aws_discovery_script

key = os.getenv('SECRET_KEY').encode()
crypter = Fernet(key)

REGISTRATION = False

log_file_name = 'server.log'
log_file_path = f'{os.getcwd()}/{log_file_name}'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(log_file_path)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

GMAIL_USER = os.getenv('GMAIL_USER', "trolley_user")
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD', "trolley_password")

app = Flask(__name__, template_folder='templates')

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


def yaml_to_dict(content) -> dict:
    full_deployment_yaml = content['deployment_yaml']
    deployment_yaml_dict = []
    if '---' in full_deployment_yaml:
        deployments_list = full_deployment_yaml.split('---')
        for deployment in deployments_list:
            single_deployment = yaml.safe_load(deployment)
            deployment_yaml_dict.append(single_deployment)
    else:
        deployment_yaml_dict = yaml.safe_load(full_deployment_yaml)
    return deployment_yaml_dict


def deployment_yaml_object_handling(content) -> DeploymentYAMLObject:
    return DeploymentYAMLObject(content['cluster_type'], content['cluster_name'], yaml_to_dict(content))


def user_registration(first_name: str = '', last_name: str = '', password: str = '',
                      user_email: str = '', team_name: str = '', profile_image_filename: str = '',
                      confirmation_url: str = '', registration_status: str = '') -> bool:
    """
    This function registers a new user into the DB
    """
    if not web.mongo_handler.mongo_utils.is_users():
        user_type = 'admin'
    else:
        user_type = 'user'
    user_name = f'{first_name.lower()}-{last_name.lower()}'
    hashed_password = generate_password_hash(password, method='sha256')
    profile_image_id = web.mongo_handler.mongo_utils.insert_file(profile_image_filename)
    if web.mongo_handler.mongo_utils.retrieve_user(user_email):
        web.mongo_handler.mongo_utils.delete_user(user_email=user_email)
    user_object = UserObject(first_name=first_name, last_name=last_name, user_name=user_name, user_email=user_email,
                             team_name=team_name, hashed_password=hashed_password, confirmation_url=confirmation_url,
                             registration_status=registration_status, user_type=user_type,
                             profile_image_filename=f'static/img/{profile_image_filename}', availability=True,
                             profile_image_id=profile_image_id)
    if web.mongo_handler.mongo_utils.insert_user(asdict(user_object)):
        if 'trolley' in profile_image_filename:
            return True
        return True
    else:
        return False


def encode_provider_details(content: dict) -> ProviderObject:
    encoded_aws_access_key_id = crypter.encrypt(str.encode(content['aws_access_key_id']))
    encoded_aws_secret_access_key = crypter.encrypt(str.encode(content['aws_secret_access_key']))
    encoded_google_creds_json = crypter.encrypt(str.encode(content['google_creds_json']))
    encoded_azure_credentials = crypter.encrypt(str.encode(content['azure_credentials']))
    provider_object = ProviderObject(provider=content[PROVIDER], aws_access_key_id=encoded_aws_access_key_id,
                                     aws_secret_access_key=encoded_aws_secret_access_key,
                                     azure_credentials=encoded_azure_credentials,
                                     google_creds_json=encoded_google_creds_json, user_email=content['user_email'])
    return provider_object


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
    user_object = web.mongo_handler.mongo_utils.retrieve_user(user_email)
    logger.info(f'user_object is: {user_object}')
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
    if content[PROVIDER] == AWS:
        if not content['aws_access_key_id'] or not content['aws_secret_access_key']:
            return False
        else:
            return True
    elif content[PROVIDER] == GCP:
        if not content['google_creds_json']:
            return False
        else:
            return True
    elif content[PROVIDER] == AZ:
        if not content['azure_credentials']:
            return False
        else:
            return True


def render_page(page_name: str = '', cluster_name: str = '', client_name: str = ''):
    try:
        token, user_object = login_processor()
        base64_data = codecs.encode(user_object['profile_image'].read(), 'base64')
        is_login_pass = True
    except:
        is_login_pass = False
    if is_login_pass:
        data = {'user_name': user_object['user_name'], 'first_name': user_object['first_name'],
                'cluster_name': cluster_name, 'client_name': client_name}
        profile_image = base64_data.decode('utf-8')
        return render_template(page_name, data=data, image=profile_image)
    else:
        return render_template('login.html')


@app.route('/get_clusters_data', methods=[GET])
@login_required
def get_clusters_data():
    """
    Ths endpoint allows providing basic clusters data that was gathered upon the clusters' creation.
    """
    cluster_type = request.args.get(CLUSTER_TYPE)
    client_name = request.args.get(CLIENT_NAME.lower())
    user_name = request.args.get(USER_NAME.lower())
    clusters_list = web.mongo_handler.mongo_utils.retrieve_available_clusters(cluster_type, client_name, user_name)
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
    instances_list = web.mongo_handler.mongo_utils.retrieve_instances(provider_type, client_name, user_name)
    return Response(json.dumps(instances_list), status=200, mimetype=APPLICATION_JSON)


@app.route('/get_agent_cluster_data', methods=[GET])
@login_required
def get_agent_cluster_data():
    """
    This endpoint allows providing an additional cluster data that is being collected by the deployed Trolley Agent
    """
    cluster_name = request.args.get(CLUSTER_NAME.lower())
    cluster_object = web.mongo_handler.mongo_utils.retrieve_agent_cluster_details(cluster_name)
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
    if trigger_trolley_agent_deployment_github_action(**content):
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
    content['cluster_name'] = cluster_name
    if trigger_gke_build_github_action(**content):
        return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        # deployment_yaml_object = deployment_yaml_object_handling(content)
    # else:
    #     return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    # if web.mongo_handler.mongo_utils.insert_deployment_yaml(asdict(deployment_yaml_object)):
    #     return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
    # else:
    #     return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)


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
    content['cluster_name'] = cluster_name
    if trigger_eks_build_github_action(**content):
        return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        # deployment_yaml_object = deployment_yaml_object_handling(content)
    # else:
    #     return Response(json.dumps(response.text), status=400, mimetype=APPLICATION_JSON)
    # if web.mongo_handler.mongo_utils.insert_deployment_yaml(asdict(deployment_yaml_object)):
    #     return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
    # else:
    #     return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)


@app.route('/trigger_aks_deployment', methods=[POST])
@login_required
def trigger_aks_deployment():
    """
    This endpoint allows an AKS Cluster deployment
    """
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    user_name = content['user_name']
    cluster_name = f'{user_name}-{AKS}-{random_string(8)}'
    content['cluster_name'] = cluster_name
    if trigger_aks_build_github_action(**content):
        return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
    # if trigger_aks_build_github_action(**content):
    #     deployment_yaml_object = deployment_yaml_object_handling(content)
    # else:
    #     return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    # if web.mongo_handler.mongo_utils.insert_deployment_yaml(asdict(deployment_yaml_object)):
    #     return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
    # else:
    #     return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)


@app.route('/delete_expired_clusters', methods=[DELETE])
@login_required
def delete_expired_clusters():
    """
    Ths endpoint allows deletion of clusters that passed their expiration time
    """
    content = request.get_json()
    expired_clusters_list = web.mongo_handler.mongo_utils.retrieve_expired_clusters(cluster_type=content['cluster_type'])
    for expired_cluster in expired_clusters_list:
        delete_gke_cluster(cluster_name=expired_cluster['cluster_name'])
        time.sleep(5)
        web.mongo_handler.mongo_utils.set_cluster_availability(cluster_type=content['cluster_type'],
                                                           cluster_name=content['cluster_name'],
                                                           availability=False)
    return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)


@app.route('/delete_cluster', methods=[DELETE])
@login_required
def delete_cluster():
    """
    This request deletes a selected cluster
    """
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    if content[CLUSTER_TYPE] == GKE:
        del content[CLUSTER_TYPE]
        delete_gke_cluster(**content)
        web.mongo_handler.mongo_utils.set_cluster_availability(cluster_type=GKE,
                                                           cluster_name=content['cluster_name'],
                                                           discovered=content['discovered'],
                                                           availability=False)
    elif content[CLUSTER_TYPE] == EKS:
        del content[CLUSTER_TYPE]
        delete_eks_cluster(**content)
        web.mongo_handler.mongo_utils.set_cluster_availability(cluster_type=EKS,
                                                           cluster_name=content['cluster_name'],
                                                           discovered=content['discovered'],
                                                           availability=False)
    elif content[CLUSTER_TYPE] == AKS:
        del content[CLUSTER_TYPE]
        delete_aks_cluster(**content)
        web.mongo_handler.mongo_utils.set_cluster_availability(cluster_type=AKS,
                                                           cluster_name=content['cluster_name'],
                                                           discovered=content['discovered'],
                                                           availability=False)
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
        if web.mongo_handler.mongo_utils.insert_cluster_data_object(content):
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    elif content['agent_type'] == 'aws':
        if web.mongo_handler.mongo_utils.insert_cluster_data_object(content):
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)


@app.route('/provider', methods=[GET, POST])
@login_required
def provider():
    """
    This endpoint adds a provider data
    """
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested')
    content['user_email'] = session['user_email']
    if validate_provider_data(content):
        encoded_provider_details = encode_provider_details(content)
        if web.mongo_handler.mongo_utils.insert_provider_data_object(asdict(encoded_provider_details)):
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    else:
        return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)


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
        if web.mongo_handler.mongo_utils.add_client_data_object(content):
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    elif request.method == PUT:
        content = request.get_json()
        if content[OBJECT_TYPE] == CLUSTER:
            if web.mongo_handler.mongo_utils.add_data_to_cluster(**content):
                return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
            else:
                return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
        elif content[OBJECT_TYPE] == INSTANCE:
            if web.mongo_handler.mongo_utils.add_data_to_instance(**content):
                return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
            else:
                return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    elif request.method == DELETE:
        content = request.get_json()
        if web.mongo_handler.mongo_utils.delete_client(**content):
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    elif request.method == GET:
        client_names = web.mongo_handler.mongo_utils.retrieve_clients_data()
        return jsonify(sorted(client_names, key=lambda d: d['client_name']))


# @app.route('/fetch_clients_data', methods=[GET])
# @login_required
# def fetch_clients_data():
#     client_names = web.mongo_handler.mongo_utils.retrieve_clients_data()
#     return jsonify(client_names)


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
        if web.mongo_handler.mongo_utils.invite_user(content):
            mail_message = MailSender(content['user_email'])
            mail_message.send_invitation_mail()
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    elif request.method == GET:
        logged_user_name = request.args.get('logged_user_name')
        logger.info(f'logged_user_name is {logged_user_name}')
        users_data = web.mongo_handler.mongo_utils.retrieve_users_data(logged_user_name)
        logger.info(f'users_data is: {users_data}')
        return jsonify(sorted(users_data, key=lambda d: d['user_name']))
    elif request.method == DELETE:
        content = request.get_json()
        user_name = content[USER_NAME.lower()]
        users_data = web.mongo_handler.mongo_utils.delete_user(user_name=user_name)
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
        if web.mongo_handler.mongo_utils.insert_team(content):
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    elif request.method == GET:
        teams_data = web.mongo_handler.mongo_utils.retrieve_teams_data()
        return jsonify(sorted(teams_data, key=lambda d: d['team_name']))
    elif request.method == DELETE:
        content = request.get_json()
        team_name = content[TEAM_NAME.lower()]
        if web.mongo_handler.mongo_utils.delete_team(team_name=team_name):
            return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
        else:
            return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)

        # return jsonify(users_data)
        # users_object = web.mongo_handler.mongo_utils.retrieve_users_data()
        # return Response(json.dumps(users_object), status=200, mimetype=APPLICATION_JSON)

    # elif request.method == PUT:
    #     if content[OBJECT_TYPE] == CLUSTER:
    #         if web.mongo_handler.mongo_utils.add_client_to_cluster(**content):
    #             return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
    #         else:
    #             return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    #     elif content['object_type'] == 'instance':
    #         if web.mongo_handler.mongo_utils.add_client_to_instance(**content):
    #             return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
    #         else:
    #             return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)
    # elif request.method == DELETE:
    #     if web.mongo_handler.mongo_utils.delete_client(**content):
    #         return Response(json.dumps(OK), status=200, mimetype=APPLICATION_JSON)
    #     else:
    #         return Response(json.dumps(FAILURE), status=400, mimetype=APPLICATION_JSON)


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
        regions = web.mongo_handler.mongo_utils.retrieve_cache(cache_type=LOCATIONS_DICT, provider=AKS)
    elif cluster_type == GKE:
        regions = web.mongo_handler.mongo_utils.retrieve_cache(cache_type=REGIONS_LIST, provider=GKE)
    elif cluster_type == EKS:
        regions = web.mongo_handler.mongo_utils.retrieve_cache(cache_type=REGIONS_LIST, provider=EKS)
    else:
        regions = web.mongo_handler.mongo_utils.retrieve_cache(cache_type=REGIONS_LIST, provider=GKE)
    if len(regions) == 0:
        return jsonify("Regions data was not found"), 400
    else:
        return jsonify(regions), 200


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
        gke_zones = web.mongo_handler.mongo_utils.retrieve_cache(cache_type=ZONES_LIST, provider=GKE)
        for zone in gke_zones:
            if region_name in zone:
                zones_list.append(zone)
        return jsonify(zones_list)
    elif cluster_type == EKS:
        eks_zones = web.mongo_handler.mongo_utils.retrieve_cache(cache_type=ZONES_LIST, provider=EKS)
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
        subnets_dict = web.mongo_handler.mongo_utils.retrieve_cache(cache_type='subnets_dict', provider=EKS)
        for subnet in subnets_dict:
            if subnet in zone_names:
                subnets.append(subnets_dict[subnet])
        if len(subnets[0]) < 1:
            return jsonify([f'No subnets were found for {zone_names} zones'])
        else:
            return jsonify(subnets)


@app.route('/fetch_helm_installs', methods=[GET, POST])
@login_required
def fetch_helm_installs():
    names = bool(util.strtobool(request.args.get(NAMES)))
    logger.info(f'A request to fetch helm installs for {names} names has arrived')
    helm_installs_list = web.mongo_handler.mongo_utils.retrieve_cache(cache_type=HELM_INSTALLS_LIST, provider=HELM)
    return jsonify(helm_installs_list)


@app.route('/fetch_client_name_per_cluster', methods=[GET])
@login_required
def fetch_client_name_per_cluster():
    cluster_type = request.args.get(CLUSTER.lower())
    cluster_name = request.args.get(CLUSTER_NAME.lower())
    client_names = web.mongo_handler.mongo_utils.retrieve_client_per_cluster_name(cluster_type, cluster_name)
    return jsonify(client_names)


@app.route('/fetch_gke_versions', methods=[GET])
@login_required
def fetch_gke_versions():
    gke_versions_list = web.mongo_handler.mongo_utils.retrieve_cache(cache_type=GKE_VERSIONS_LIST, provider=GKE)
    return jsonify(gke_versions_list)


@app.route('/fetch_gke_image_types', methods=[GET])
@login_required
def fetch_gke_image_types():
    logger.info(f'A request to fetch available GKE image types has arrived')
    gke_image_types_list = web.mongo_handler.mongo_utils.retrieve_cache(cache_type=GKE_IMAGE_TYPES, provider=GKE)
    return jsonify(gke_image_types_list)


@app.route('/register', methods=[GET, POST])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        first_name = request.form['first_name'].lower()
        last_name = request.form['last_name'].lower()
        user_email = request.form['user_email']
        invited_user = web.mongo_handler.mongo_utils.retrieve_invited_user(user_email)
        if invited_user:
            team_name = invited_user['team_name']
        else:
            team_name = "none"
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
            full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file_name)
            full_thumbnail_file_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_file_path)
            FileStorage(profile_image.save(full_file_path))
            image = Image.open(full_file_path)
            new_image = image.resize((192, 192))
            new_image.save(full_thumbnail_file_path)

        # if not REGISTRATION:
        #     return render_template('login.html',
        #                            error_message='Registration is closed at the moment')
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
            if not web.mongo_handler.mongo_utils.retrieve_user(user_email):
                token = generate_confirmation_token(user_email)
                confirmation_url = str(url_for('confirmation_email', token=token, _external=True))
                print(f'confirmation_url is: {confirmation_url}')

                mail_message = MailSender(user_email, confirmation_url)
                mail_message.send_confirmation_mail()

                if user_registration(first_name, last_name, password, user_email, team_name, image_file_name,
                                     confirmation_url, registration_status='pending'):
                    return render_template('confirmation.html', email=user_email)
                    # return render_template('login.html',
                    #                        error_message=f'Dear {first_name.capitalize()}, '
                    #                                      f'Welcome to {PROJECT_NAME.capitalize()}!')
                else:
                    return render_template('confirmation.html', email=user_email)
                    # return render_template('login.html',
                    #                        error_message=f'Dear {first_name.capitalize()}, '
                    #                                      f'your password was not entered correctly. '
                    #                                      f'Please try again')
                # return render_template('confirmation.html', email=user_email)
                # if user_registration(first_name, last_name, password, user_email, team_name, file_path):
                #     return render_template('login.html',
                #                            error_message=f'Dear {first_name.capitalize()}, '
                #                                          f'Welcome to {PROJECT_NAME.capitalize()}!')
                # else:
                #     return render_template('login.html',
                #                            error_message=f'Dear {first_name.capitalize()}, '
                #                                          f'your password was not entered correctly. '
                #                                          f'Please try again')
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
        web.mongo_handler.mongo_utils.update_user_registration_status(user_email=user_email,
                                                                  registration_status='confirmed')

        return redirect(url_for('login'))


@app.route('/login', methods=[GET, POST])
@login_required
def login():
    message = request.args.get('message')
    logger.info(f'a login request was received with {message} message')
    if session['registration_status'] != 'confirmed':
        first_name = session['first_name']
        user_email = session['user_email']
        token = generate_confirmation_token(user_email)
        confirm_url = str(url_for('confirmation_email', token=token, _external=True))
        mail_message = MailSender(user_email, confirm_url)
        mail_message.send_confirmation_mail()
        web.mongo_handler.mongo_utils.update_user(user_email, update_type="confirmation_url", update_value=confirm_url)
        return render_template('login.html',
                               error_message=f'Dear {first_name}! '
                                             f'A confirmation mail was sent to {user_email} and was not confirmed. '
                                             f'Sending you another one!')

    if message is None:
        message = ''
    if request.method == 'GET':
        logger.info(f'message is: {message}')
        return render_template('login.html', failure_message=message)
    if request.method == 'POST':
        token, user_object = login_processor(new=True)
        base64_data = codecs.encode(user_object['profile_image'].read(), 'base64')
        profile_image = base64_data.decode('utf-8')
        if token:
            user_email = user_object['user_email']
            user_type = web.mongo_handler.mongo_utils.check_user_type(user_email)
            data = {'user_name': user_object['user_name'], 'first_name': user_object['first_name'], 'user_type': user_type}
            logger.info(f'data content is: {data}')
            return render_template('index.html', data=data, image=profile_image)
        else:
            user_email = user_object['user_email']
            logger.info(f'user_email is: {user_email}')
            return render_template('login.html',
                                   error_message=f'Dear {user_email}, your password was not entered correctly. '
                                                 f'Please try again')


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


@app.route('/settings', methods=[GET, POST])
@login_required
def settings():
    return render_page('settings.html')


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
    app.run(host='0.0.0.0', debug=True)
