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

from flask import request, Response, Flask, session, redirect, url_for, render_template, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from mongo_handler.mongo_utils import set_cluster_availability, retrieve_expired_clusters, retrieve_available_clusters, \
    insert_user, retrieve_user, retrieve_gke_cache
from mongo_handler.mongo_objects import UserObject
from variables.variables import POST, GET, EKS, \
    APPLICATION_JSON, CLUSTER_TYPE, GKE, AKS, DELETE, USER_NAME, MACOS, REGIONS_LIST, \
    ZONES_LIST, HELM_INSTALLS_LIST, GKE_VERSIONS_LIST, GKE_IMAGE_TYPES
from web.cluster_operations import trigger_gke_build_github_action, trigger_eks_build_github_action, \
    trigger_aks_build_github_action, delete_gke_cluster, delete_eks_cluster, delete_aks_cluster

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

CUR_DIR = os.getcwd()
PROJECT_ROOT = "/".join(CUR_DIR.split('/'))
config = configparser.ConfigParser()
config_ini_file = "/".join(PROJECT_ROOT.split("/")[:-1]) + "/config.ini"
config.read(config_ini_file)

AKS_LOCATIONS_COMMAND = 'az account list-locations'
EKS_REGIONS_COMMAND = 'aws ec2 describe-regions'
EKS_AVAILABILITY_ZONES_COMMAND = 'aws ec2 describe-availability-zones'
EKS_SUBNETS_COMMAND = 'aws ec2 describe-subnets'
AWS_VPCS_COMMAND = 'aws ec2 describe-vpcs --region'

if MACOS in platform.platform():
    CUR_DIR = os.getcwd()
    PROJECT_ROOT = "/".join(CUR_DIR.split('/'))
    print(f'current directory is: {PROJECT_ROOT}')
    config = configparser.ConfigParser()
    config_ini_file = "/".join(PROJECT_ROOT.split("/")[:-1]) + "/config.ini"
    print(f'config ini file location is: {config_ini_file}')
    config.read(config_ini_file)
    MONGO_URL = config['DEFAULT']['jenkins_url']
    JENKINS_USER = config['DEFAULT']['jenkins_user']
    HELM_COMMAND = '/opt/homebrew/bin/helm'
    JENKINS_URL = 'http://' + config['DEFAULT']['jenkins_url'] + ':8080'
else:
    MONGO_URL = os.environ['MONGO_URL']
    JENKINS_USER = os.environ['JENKINS_USER']
    PROJECT_NAME = os.environ['PROJECT_NAME']
    MONGO_PASSWORD = os.environ['MONGO_PASSWORD']
    MONGO_USER = os.environ['MONGO_USER']
    JENKINS_URL = ''

JENKINS_PASSWORD = os.getenv('JENKINS_PASSWORD')
JENKINS_KUBERNETES_GKE_DEPLOYMENT_JOB_NAME = 'gke_deployment'
JENKINS_KUBERNETES_GKE_AUTOPILOT_DEPLOYMENT_JOB_NAME = 'gke_autopilot_deployment'
JENKINS_EKS_DEPLOYMENT_JOB_NAME = 'eks_deployment'
JENKINS_AKS_DEPLOYMENT_JOB_NAME = 'aks_deployment'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('../trolley.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
        function_name = inspect.stack()[0][3]
        logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    elif content['cluster_type'] == 'gke_autopilot':
        del content['cluster_type']
        # trigger_gke_autopilot_build_github_action(**content) # TBA
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


@app.route('/trigger_eks_deployment', methods=[POST])
def trigger_eks_deployment():
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    trigger_eks_build_github_action(**content)
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


@app.route('/trigger_aks_deployment', methods=[POST])
def trigger_aks_deployment():
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    trigger_aks_build_github_action(**content)
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


@app.route('/delete_expired_clusters', methods=[DELETE])
def delete_expired_clusters():
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
