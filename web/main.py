import inspect
import json
import logging
import os
import time
import datetime
import jwt
import configparser
import platform
from dataclasses import asdict
from subprocess import PIPE, run
from distutils import util

import requests
from jenkins import Jenkins
from flask import request, Response, Flask, session, redirect, url_for, render_template, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from utils import random_string

from mongo_handler.mongo_utils import set_cluster_availability, retrieve_expired_clusters, retrieve_available_clusters, \
    insert_user, retrieve_user, retrieve_cluster_details, retrieve_gke_cache
from mongo_handler.mongo_objects import UserObject
from variables.variables import TROLLEY_PROJECT_NAME, PROJECT_NAME, CLUSTER_NAME, CLUSTER_VERSION, ZONE_NAME, IMAGE_TYPE, \
    NUM_NODES, EXPIRATION_TIME, REGION_NAME, POST, GET, VERSION, AKS_LOCATION, AKS_VERSION, HELM_INSTALLS, EKS, \
    APPLICATION_JSON, CLUSTER_TYPE, GKE, AKS, DELETE, USER_NAME, MACOS, EKS_LOCATION, EKS_ZONES, REGIONS_LIST, \
    ZONES_LIST, HELM_INSTALLS_LIST, GKE_VERSIONS_LIST, GKE_IMAGE_TYPES

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

CUR_DIR = os.getcwd()
PROJECT_ROOT = "/".join(CUR_DIR.split('/'))
config = configparser.ConfigParser()
config_ini_file = "/".join(PROJECT_ROOT.split("/")[:-1]) + "/config.ini"
config.read(config_ini_file)

# if MACOS in platform.platform():
#     config.read(f'{PROJECT_ROOT}/config.ini')
#     HELM_COMMAND = '/opt/homebrew/bin/helm'
#
# else:
#     config.read(f'{CUR_DIR}/config.ini')
#     HELM_COMMAND = '/snap/bin/helm'

AKS_LOCATIONS_COMMAND = 'az account list-locations'
GKE_ZONES_COMMAND = 'gcloud compute zones list --format json'
GKE_REGIONS_COMMAND = 'gcloud compute regions list --format json'
EKS_REGIONS_COMMAND = 'aws ec2 describe-regions'
EKS_AVAILABILITY_ZONES_COMMAND = 'aws ec2 describe-availability-zones'
EKS_SUBNETS_COMMAND = 'aws ec2 describe-subnets'
AWS_VPCS_COMMAND = 'aws ec2 describe-vpcs --region'
GKE_VERSIONS_COMMAND = 'gcloud container get-server-config --zone='

PROJECT_ID = config['DEFAULT']['project_id']
JENKINS_URL = 'http://' + config['DEFAULT']['jenkins_url'] + ':8080'
JENKINS_USER = config['DEFAULT']['jenkins_user']
JENKINS_PASSWORD = os.getenv('JENKINS_PASSWORD')
GITHUB_ACTION_TOKEN = os.getenv('GITHUB_ACTION_TOKEN')
JENKINS_KUBERNETES_GKE_DEPLOYMENT_JOB_NAME = 'gke_deployment'
JENKINS_KUBERNETES_GKE_AUTOPILOT_DEPLOYMENT_JOB_NAME = 'gke_autopilot_deployment'
JENKINS_DELETE_GKE_JOB = 'delete_gke_cluster'
JENKINS_EKS_DEPLOYMENT_JOB_NAME = 'eks_deployment'
JENKINS_DELETE_EKS_JOB = 'delete_eks_cluster'
JENKINS_AKS_DEPLOYMENT_JOB_NAME = 'aks_deployment'
JENKINS_DELETE_AKS_JOB = 'delete_aks_cluster'

GITHUB_ACTION_REQUEST_HEADER = {
    'Content-type': 'application/json',
    'Accept': 'application / vnd.github.everest - preview + json',
    'Authorization': f'token {GITHUB_ACTION_TOKEN}'
}
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('../trolley.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info(f'The selected project_id is: {PROJECT_ID}')
logger.info(f'The selected jenkins_url is: {JENKINS_URL}')
logger.info(f'The selected jenkins_user is: {JENKINS_USER}')
logger.info(f'The selected jenkins_password is: {JENKINS_PASSWORD}')
logger.info(f'The current directory is: {CUR_DIR}')
logger.info(f'The content of the directory is: {os.listdir(CUR_DIR)}')


def user_registration(first_name: str = '', last_name: str = '', password: str = '',
                      user_email: str = '', team_name: str = '') -> bool:
    """"""
    user_name = f'{first_name.lower()}{last_name.lower()}'
    hashed_password = generate_password_hash(password, method='sha256')
    user_object = UserObject(first_name=first_name, last_name=last_name, user_name=user_name, user_email=user_email,
                             team_name=team_name, hashed_password=hashed_password)
    if insert_user(asdict(user_object)):
        return True
    else:
        return False


def login_processor(user_email: str = "", password: str = "", new: bool = False) -> tuple:
    user_agent = request.headers.get('User-Agent')
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
    logger.info(f'The request is being done with: {user_email} user')
    user_object = retrieve_user(user_email)
    logger.info(f'user_obj is: {user_object}')
    if not user_object:
        return '', {'user_email': user_email}
    session['user_email'] = user_email
    session['user_password'] = password
    try:
        session['first_name'] = user_object['first_name'].capitalize()
    except:
        redirect(url_for('login',
                         failure_message=f'username or password were not found in the system '
                                         f' please try again'))
    if not user_email or not password:
        return render_template('login.html',
                               failure_message=f'{user_email} was not found in the system '
                                               f'or you provided a wrong password, please try again')
    try:
        if check_password_hash(user_object['hashed_password'], password):
            logger.info(f'The hashed password is correct')
            try:
                token = jwt.encode(
                    {'user_id': str(user_object['_id']),
                     'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=1440)},
                    app.config['SECRET_KEY'])
            except:
                logger.info(f'Failed to create a token')
                token = ''
            # decoded_token = token.decode("utf-8")
            session['x-access-token'] = token
            logger.info(f'The decoded token is: {token}')
            return token, user_object
        else:
            logger.info(f'The hashed password is incorrect')
            return '', user_object
    except:
        redirect(url_for('login',
                         failure_message=f'username or password were not found in the system '
                                         f' please try again'))


def fetch_aks_version(kubernetes_version: str = '') -> str:
    if kubernetes_version == '1.22':
        aks_version = '1.22.4'
    elif kubernetes_version == '1.21':
        aks_version = '1.21.7'
    elif kubernetes_version == '1.20':
        aks_version = '1.20.13'
    elif kubernetes_version == '1.19':
        aks_version = '1.19.13'
    else:
        aks_version = '1.22.4'
    return aks_version


def retrieve_aws_availability_zones(region_name):
    command = f'{EKS_AVAILABILITY_ZONES_COMMAND} --region {region_name}'
    logger.info(f'Running a {command} command')
    print(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    availability_zones = json.loads(result.stdout)
    print(f'availability_zones list is: {availability_zones}')
    zones_list = []
    for zone in availability_zones['AvailabilityZones']:
        if not zone['ZoneName'] == 'us-east-1e':
            zones_list.append(zone['ZoneName'])
    return zones_list


def retrieve_aws_subnets(availability_zone: str = ''):
    command = f'{EKS_SUBNETS_COMMAND} --filters "Name=availability-zone","Values={availability_zone}"'
    logger.info(f'Running a {command} command')
    print(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    availability_zones = json.loads(result.stdout)
    print(f'availability_zones list is: {availability_zones}')
    subnets_list = []
    if availability_zones['Subnets']:
        for zone in availability_zones['Subnets']:
            subnets_list.append(zone['SubnetId'])
        return subnets_list
    else:
        return [f'No subnets were found for {availability_zone} zone']


def trigger_gke_build_github_action(user_name: str = '',
                                    version: str = '',
                                    gke_region: str = '',
                                    gke_zone: str = '',
                                    image_type: str = '',
                                    num_nodes: int = '',
                                    helm_installs: list = '',
                                    expiration_time: int = ''):
    cluster_name = f'{user_name}-gke-{random_string(5)}'
    json_data = {
        "event_type": "gke-build-api-trigger",
        "client_payload": {"cluster_name": cluster_name,
                           "cluster_version": version,
                           "zone_name": gke_zone,
                           "region_name": gke_region,
                           "num_nodes": num_nodes}
    }

    response = requests.post('https://api.github.com/repos/LiorYardeni/trolley/dispatches',
                             headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)
    print(response)


def trigger_kubernetes_gke_build_jenkins(project_name: str = TROLLEY_PROJECT_NAME,
                                         user_name: str = '',
                                         version: str = '',
                                         gke_region: str = '',
                                         gke_zone: str = '',
                                         image_type: str = '',
                                         num_nodes: int = '',
                                         helm_installs: list = '',
                                         expiration_time: int = ''):
    """
    this functions trigger jenkins job to build GKE cluster.
    @param project_name: Your project name, change or add a global variable in variables.
    @param user_name:
    @param version: single select scrolldown from realtime generated versions list
    @param gke_region:
    @param gke_zone:
    @param image_type:
    @param num_nodes:
    @param helm_installs:
    @param expiration_time: set a default to make sure no cluster is left running.
    @return:
    """
    server = Jenkins(url=JENKINS_URL, username=JENKINS_USER, password=JENKINS_PASSWORD)
    try:
        from utils import random_string
        job_id = server.build_job(name=JENKINS_KUBERNETES_GKE_DEPLOYMENT_JOB_NAME, parameters={
            PROJECT_NAME: project_name,
            CLUSTER_NAME: f'{user_name}-gke-{random_string(5)}',
            USER_NAME: user_name,
            CLUSTER_VERSION: version,
            REGION_NAME: gke_region,
            ZONE_NAME: gke_zone,
            IMAGE_TYPE: image_type,
            NUM_NODES: num_nodes,
            HELM_INSTALLS: ",".join(helm_installs),
            EXPIRATION_TIME: expiration_time
        })
        logger.info(f'Job number {job_id - 1} was triggered on {JENKINS_KUBERNETES_GKE_DEPLOYMENT_JOB_NAME}')
        return 'OK'
    except:
        return 'fail'


def trigger_kubernetes_gke_autopilot_build_jenkins(project_name: str = TROLLEY_PROJECT_NAME,
                                                   user_id: str = 'lior',
                                                   region: str = '', expiration_time: int = ''):
    """

    @param project_name: Your project name, change or add a global variable in variables.
    @param user_id:
    @param region:
    @param expiration_time:
    @return:
    """
    server = Jenkins(url=JENKINS_URL, username=JENKINS_USER, password=JENKINS_PASSWORD)
    try:
        job_id = server.build_job(name=JENKINS_KUBERNETES_GKE_AUTOPILOT_DEPLOYMENT_JOB_NAME, parameters={
            PROJECT_NAME: project_name,
            CLUSTER_NAME: f'{user_id}-gke-{random_string(5)}',
            REGION_NAME: region,
            EXPIRATION_TIME: expiration_time
        })
        logger.info(f'Job number {job_id - 1} was triggered on {JENKINS_KUBERNETES_GKE_AUTOPILOT_DEPLOYMENT_JOB_NAME}')

        return 'OK'
    except:
        return 'fail'


def get_eks_zones(eks_location: str = '') -> str:
    """
    Retrieve EKS zones from server, show them in a list
    @param eks_location:
    @return:
    """
    zones_list = []
    command = f'aws ec2 describe-availability-zones --region {eks_location}'
    logger.info(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    result_parsed = json.loads(result.stdout)
    availability_zones = result_parsed['AvailabilityZones']
    for availability_zone in availability_zones:
        zones_list.append(availability_zone['ZoneName'])
    return ','.join(zones_list)


def trigger_eks_build_github_action(user_name: str = '',
                                    version: str = '',
                                    eks_location: str = '',
                                    eks_zones: list = None,
                                    eks_subnets: list = None,
                                    image_type: str = '',
                                    num_nodes: int = '',
                                    helm_installs: list = '',
                                    expiration_time: int = ''):
    cluster_name = f'{user_name}-gke-{random_string(5)}'
    json_data = {
        "event_type": "eks-build-api-trigger",
        "client_payload": {"cluster_name": cluster_name,
                           "cluster_version": version,
                           "region_name": eks_location,
                           "zone_names": ",".join(eks_zones),
                           "num_nodes": num_nodes,
                           "subnets": ",".join(eks_subnets)}
    }
    response = requests.post('https://api.github.com/repos/LiorYardeni/trolley/dispatches',
                             headers=GITHUB_ACTION_REQUEST_HEADER, json=json_data)
    print(response)


def trigger_eks_build_jenkins(
        user_id: str = '',
        version: str = '',
        num_nodes: int = '',
        expiration_time: int = '4',
        eks_location: str = '',
        helm_installs: list = None):
    """

    @param user_id:
    @param version: single select scrolldown from realtime generated versions list
    @param num_nodes:
    @param expiration_time: set a default to make sure no cluster is left running.
    @param eks_location:
    @param helm_installs:
    @return:
    """
    if not helm_installs:
        helm_installs = '.'
    eks_zones = get_eks_zones(eks_location)
    print(f'The list of retrieved eks_zones is: {eks_zones}')
    server = Jenkins(url=JENKINS_URL, username=JENKINS_USER, password=JENKINS_PASSWORD)
    try:
        job_id = server.build_job(name=JENKINS_EKS_DEPLOYMENT_JOB_NAME, parameters={
            CLUSTER_NAME: f'{user_id}-{EKS}-{random_string(5)}',
            VERSION: version,
            NUM_NODES: num_nodes,
            EXPIRATION_TIME: expiration_time,
            HELM_INSTALLS: helm_installs,
            EKS_LOCATION: eks_location,
            EKS_ZONES: eks_zones
        })
        logger.info(f'Job number {job_id - 1} was triggered on {JENKINS_EKS_DEPLOYMENT_JOB_NAME}')
        return 'OK'
    except:
        return 'fail'


def trigger_aks_build_jenkins(
        user_id: str = '',
        num_nodes: int = '',
        version: str = '',
        aks_location: str = '',
        expiration_time: int = '',
        helm_installs: list = ''):
    """

    @param user_id:
    @param num_nodes:
    @param version:
    @param aks_location:
    @param expiration_time:
    @param helm_installs:
    @return:
    """
    if helm_installs:
        helm_installs_string = ','.join(helm_installs)
    else:
        helm_installs_string = '.'
    aks_version = fetch_aks_version(kubernetes_version=version)
    server = Jenkins(url=JENKINS_URL, username=JENKINS_USER, password=JENKINS_PASSWORD)
    try:
        job_id = server.build_job(name=JENKINS_AKS_DEPLOYMENT_JOB_NAME, parameters={
            CLUSTER_NAME: f'{user_id}-aks-{random_string(5)}',
            NUM_NODES: num_nodes,
            AKS_VERSION: aks_version,
            AKS_LOCATION: aks_location,
            EXPIRATION_TIME: expiration_time,
            HELM_INSTALLS: helm_installs_string
        })
        logger.info(f'Job number {job_id - 1} was triggered on {JENKINS_AKS_DEPLOYMENT_JOB_NAME}')
        return 'OK'
    except:
        return 'fail'


def delete_gke_cluster(cluster_name: str = ''):
    """
    @param cluster_name: from built clusters list
    @return:
    """
    server = Jenkins(url=JENKINS_URL, username=JENKINS_USER, password=JENKINS_PASSWORD)
    gke_cluster_details = retrieve_cluster_details(cluster_type=GKE, cluster_name=cluster_name)
    gke_cluster_zone = gke_cluster_details[ZONE_NAME.lower()]
    try:
        job_id = server.build_job(name=JENKINS_DELETE_GKE_JOB, parameters={
            CLUSTER_NAME: cluster_name,
            ZONE_NAME: gke_cluster_zone,
        })
        logger.info(f'Job number {job_id - 1} was triggered on {JENKINS_DELETE_GKE_JOB}')
        return 'OK'
    except:
        return 'fail'


def delete_eks_cluster(cluster_name: str = '', region: str = '', cloud_provider: str = '', cluster_type: str = ''):
    """

    @param cluster_name: from built clusters list
    @param region: required param for deletion command
    @param cloud_provider: GCP/Azure/AWS #why
    @param cluster_type:
    @return:
    """
    server = Jenkins(url=JENKINS_URL, username=JENKINS_USER, password=JENKINS_PASSWORD)
    try:
        job_id = server.build_job(name=JENKINS_DELETE_EKS_JOB, parameters={
            CLUSTER_NAME: cluster_name,
            REGION_NAME: region,
        })
        logger.info(f'Job number {job_id - 1} was triggered on {JENKINS_DELETE_EKS_JOB}')
        return 'OK'
    except:
        return 'fail'


def delete_aks_cluster(cluster_name: str = '', cluster_type: str = ''):
    """

    @param cluster_name: from built clusters list
    @param cluster_type: required param for deletion command
    @return:
    """
    server = Jenkins(url=JENKINS_URL, username=JENKINS_USER, password=JENKINS_PASSWORD)
    try:
        job_id = server.build_job(name=JENKINS_DELETE_AKS_JOB, parameters={
            CLUSTER_NAME: cluster_name,
        })
        logger.info(f'Job number {job_id - 1} was triggered on {JENKINS_DELETE_AKS_JOB}')
        return 'OK'
    except:
        return 'fail'


def render_page(page_name: str = ''):
    try:
        token, user_object = login_processor()
        is_login_pass = True
    except:
        is_login_pass = False
    if is_login_pass:
        data = {'user_name': user_object['user_name'], 'first_name': user_object['first_name']}
        return render_template(page_name, data=data)
    else:
        return render_template('login.html')


@app.route('/get_clusters_data', methods=[GET])
def get_clusters_data():
    cluster_type = request.args.get(CLUSTER_TYPE)
    user_name = request.args.get(USER_NAME.lower())
    clusters_list = retrieve_available_clusters(cluster_type, user_name)
    return Response(json.dumps(clusters_list), status=200, mimetype=APPLICATION_JSON)


@app.route('/trigger_kubernetes_deployment', methods=[POST])
def trigger_kubernetes_deployment():
    content = request.get_json()
    if content['cluster_type'] == 'gke':
        del content['cluster_type']
        trigger_gke_build_github_action(**content)
        # trigger_kubernetes_gke_build_jenkins(**content)
        function_name = inspect.stack()[0][3]
        logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    elif content['cluster_type'] == 'gke_autopilot':
        del content['cluster_type']
        trigger_kubernetes_gke_autopilot_build_jenkins(**content)
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


@app.route('/trigger_eks_deployment', methods=[POST])
def trigger_eks_deployment():
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    trigger_eks_build_github_action(**content)
    # trigger_eks_build_jenkins(**content)
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


@app.route('/trigger_aks_deployment', methods=[POST])
def trigger_aks_deployment():
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    trigger_aks_build_jenkins(**content)
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


@app.route('/delete_expired_clusters', methods=[DELETE])
def delete_expired_clusters(GCP=None):
    content = request.get_json()
    expired_clusters_list = retrieve_expired_clusters(cluster_type=content['cluster_type'])
    for expired_cluster in expired_clusters_list:
        delete_gke_cluster(cluster_name=expired_cluster['cluster_name'])
        time.sleep(5)
        set_cluster_availability(cluster_type=content['cluster_type'], cluster_name=content['cluster_name'],
                                 availability=False)
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


@app.route('/delete_cluster', methods=[DELETE])
def delete_cluster():
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    if content[CLUSTER_TYPE] == GKE:
        del content[CLUSTER_TYPE]
        delete_gke_cluster(**content)
        set_cluster_availability(cluster_type=GKE, cluster_name=content['cluster_name'],
                                 availability=False)
    elif content[CLUSTER_TYPE] == EKS:
        delete_eks_cluster(**content)
        set_cluster_availability(cluster_type=content['cluster_type'], cluster_name=content['cluster_name'],
                                 availability=False)
    elif content[CLUSTER_TYPE] == AKS:
        delete_aks_cluster(**content)
        set_cluster_availability(cluster_type=content['cluster_type'], cluster_name=content['cluster_name'],
                                 availability=False)
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


@app.route('/healthz', methods=[GET, POST])
def healthz():
    logger.info('A request was received')
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


@app.route('/', methods=[GET, POST])
def root():
    return render_page('index.html')


@app.route('/index', methods=[GET, POST])
def index():
    return render_page('index.html')


@app.route('/fetch_regions', methods=[GET])
def fetch_regions():
    cluster_type = request.args.get("cluster_type")
    logger.info(f'A request to fetch regions for {cluster_type} has arrived')
    if cluster_type == AKS:
        command = AKS_LOCATIONS_COMMAND
        logger.info(f'Running a {command} command')
        print(f'Running a {command} command')
        result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
        regions_list = json.loads(result.stdout)
        print(f'regions_list is: {regions_list}')
        return jsonify(regions_list)
    elif cluster_type == GKE:
        gke_regions = retrieve_gke_cache(gke_cache_type=REGIONS_LIST)
        return jsonify(gke_regions)
    elif cluster_type == EKS:
        command = EKS_REGIONS_COMMAND
        logger.info(f'Running a {command} command')
        print(f'Running a {command} command')
        result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
        regions_list = json.loads(result.stdout)
        print(f'regions_list is: {regions_list}')
        for key, value in regions_list.items():
            return jsonify(value)


@app.route('/fetch_zones', methods=[GET])
def fetch_zones():
    cluster_type = request.args.get("cluster_type")
    region_name = request.args.get("region_name")
    logger.info(f'A request to fetch zones for {cluster_type} has arrived')
    zones_list = []
    if cluster_type == AKS:
        return jsonify('')
    elif cluster_type == GKE:
        gke_zones = retrieve_gke_cache(gke_cache_type=ZONES_LIST)
        for zone in gke_zones:
            if region_name in zone:
                zones_list.append(zone)
        return jsonify(zones_list)
    elif cluster_type == EKS:
        aws_availability_zones = retrieve_aws_availability_zones(region_name)
        return jsonify(aws_availability_zones)


@app.route('/fetch_subnets', methods=[GET])
def fetch_subnets():
    cluster_type = request.args.get("cluster_type")
    zone_names = request.args.get("zone_names")
    logger.info(f'A request to fetch zone_names for {cluster_type} has arrived')
    if cluster_type == AKS:
        return jsonify('')
    elif cluster_type == GKE:
        return jsonify('')
    elif cluster_type == EKS:
        aws_availability_zones = retrieve_aws_subnets(zone_names)
        return jsonify(aws_availability_zones)


@app.route('/fetch_helm_installs', methods=[GET, POST])
def fetch_helm_installs():
    names = bool(util.strtobool(request.args.get("names")))
    logger.info(f'A request to fetch helm installs for {names} names has arrived')
    helm_installs_list = retrieve_gke_cache(gke_cache_type=HELM_INSTALLS_LIST)
    return jsonify(helm_installs_list)


@app.route('/fetch_gke_versions', methods=[GET])
def fetch_gke_versions():
    gke_versions_list = retrieve_gke_cache(gke_cache_type=GKE_VERSIONS_LIST)
    return jsonify(gke_versions_list)


@app.route('/fetch_gke_image_types', methods=[GET])
def fetch_gke_image_types():
    logger.info(f'A request to fetch available GKE image types has arrived')
    gke_image_types_list = retrieve_gke_cache(gke_cache_type=GKE_IMAGE_TYPES)
    return jsonify(gke_image_types_list)


@app.route('/fetch_aws_vpcs', methods=[GET])
def fetch_aws_vpcs():
    aws_region = request.args.get('aws_region')
    logger.info(f'A request to fetch available VPCs for {aws_region} region has arrived')
    aws_vpcs_names = []
    command = AWS_VPCS_COMMAND + ' ' + aws_region
    logger.info(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    aws_vpcs = json.loads(result.stdout)
    for key, value in aws_vpcs.items():
        for vpc in value:
            aws_vpcs_names.append(vpc['VpcId'])
        return jsonify(aws_vpcs_names)


@app.route('/register', methods=[GET, POST])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        return render_template('login.html',
                               error_message='Registration is closed at the moment')
        # first_name = request.form['first_name']
        # last_name = request.form['last_name']
        # user_email = request.form['user_email']
        # team_name = request.form['team_name']
        # password = request.form['password']
        # if not first_name:
        #     return render_template('register.html',
        #                            error_message=f'Dear {first_name}, your first name was not entered correctly. '
        #                                          f'Please try again')
        # if not last_name:
        #     return render_template('register.html',
        #                            error_message=f'Dear {first_name}, your last name was not entered correctly. '
        #                                          f'Please try again')
        # if not first_name:
        #     return render_template('register.html',
        #                            error_message=f'Your first name was not entered correctly. Please try again')
        # if not password:
        #     return render_template('register.html',
        #                            error_message=f'Dear {first_name}, your password was not entered correctly. '
        #                                          f'Please try again')
        # else:
        #     if not retrieve_user(user_email):
        #         user_registration(first_name, last_name, password, user_email, team_name)
        #     else:
        #         return render_template('register.html',
        #                                error_message=f'Dear {first_name}, your email was already registered. '
        #                                              f'Please try again')
        #     return render_template('login.html',
        #                            error_message=f'Dear {first_name}, your password was not entered correctly. '
        #                                          f'Please try again')


@app.route('/login', methods=[GET, POST])
def login():
    message = request.args.get('message')
    if message is None:
        message = ''
    if request.method == 'GET':
        return render_template('login.html', failure_message=message)
    if request.method == 'POST':
        token, user_object = login_processor(new=True)
        if token:
            data = {'user_name': user_object['user_name'], 'first_name': user_object['first_name']}
            return render_template('index.html', data=data)
        else:
            user_email = user_object['user_email']
            return render_template('login.html',
                                   error_message=f'Dear {user_email}, your password was not entered correctly. '
                                                 f'Please try again')


@app.route('/build-eks-clusters', methods=[GET, POST])
def build_eks_clusters():
    return render_page('build-eks-clusters.html')


@app.route('/build-aks-clusters', methods=[GET, POST])
def build_aks_clusters():
    return render_page('build-aks-clusters.html')


@app.route('/build-gke-clusters', methods=[GET, POST])
def build_gke_clusters():
    return render_page('build-gke-clusters.html')


@app.route('/manage-eks-clusters', methods=[GET, POST])
def manage_eks_clusters():
    return render_page('manage-eks-clusters.html')


@app.route('/manage-aks-clusters', methods=[GET, POST])
def manage_aks_clusters():
    return render_page('manage-aks-clusters.html')


@app.route('/manage-gke-clusters', methods=[GET, POST])
def manage_gke_clusters():
    return render_page('manage-gke-clusters.html')


@app.route('/logout', methods=[GET, POST])
def logout():
    session.pop('x-access-token', None)
    session.pop('user_email', None)
    session.pop('user_password', None)
    return redirect(url_for('login'))


app.run(host='0.0.0.0', port=8081, debug=True)
# app.run(host='0.0.0.0', port=8081, debug=True, ssl_context=('certs/cert.pem', 'certs/key.pem'))
