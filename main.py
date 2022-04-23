import inspect
import json
import logging
import os
from subprocess import PIPE, run
import time
import datetime
import jwt

from jenkins import Jenkins
from flask import request, Response, Flask, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from utils import random_string

from mongo_handler import config, set_cluster_availability, retrieve_expired_clusters, retrieve_available_clusters, \
    insert_user, retrieve_user
from mongo_objects import UserObject
from variables import TROLLEY_PROJECT_NAME, PROJECT_NAME, CLUSTER_NAME, CLUSTER_VERSION, ZONE_NAME, IMAGE_TYPE, \
    NUM_NODES, EXPIRATION_TIME, REGION_NAME, POST, GET, VERSION, AKS_LOCATION, AKS_VERSION, HELM_INSTALLS, EKS, \
    APPLICATION_JSON, CLUSTER_TYPE, GKE, AKS, DELETE, GCP, USER_NAME

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

PROJECT_ID = config['DEFAULT']['project_id']
JENKINS_URL = 'http://' + config['DEFAULT']['jenkins_url'] + ':8080'
JENKINS_USER = config['DEFAULT']['jenkins_user']

JENKINS_PASSWORD = os.getenv('JENKINS_PASSWORD')
JENKINS_KUBERNETES_GKE_DEPLOYMENT_JOB_NAME = 'gke_deployment'
JENKINS_KUBERNETES_GKE_AUTOPILOT_DEPLOYMENT_JOB_NAME = 'gke_autopilot_deployment'
JENKINS_DELETE_GKE_JOB = 'delete_gke_cluster'
JENKINS_EKS_DEPLOYMENT_JOB_NAME = 'eks_deployment'
JENKINS_DELETE_EKS_JOB = 'delete_eks_cluster'
JENKINS_AKS_DEPLOYMENT_JOB_NAME = 'aks_deployment'
JENKINS_DELETE_AKS_JOB = 'delete_aks_cluster'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('trolley.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info(f'The selected project_id is: {PROJECT_ID}')
logger.info(f'The selected jenkins_url is: {JENKINS_URL}')
logger.info(f'The selected jenkins_user is: {JENKINS_USER}')
logger.info(f'The selected jenkins_password is: {JENKINS_PASSWORD}')


def user_registration(first_name: str = '', last_name: str = '', password: str = '',
                      user_email: str = '', team_name: str = '') -> bool:
    """"""
    hashed_password = generate_password_hash(password, method='sha256')
    user_object = UserObject(first_name=first_name, last_name=last_name, user_email=user_email,
                             team_name=team_name, hashed_password=hashed_password)
    user_object = user_object.to_dict()
    if insert_user(user_object=user_object):
        return True
    else:
        return False


def login_processor(user_email: str = "", password: str = "", new: bool = False):
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
    user_obj = retrieve_user(user_email)
    logger.info(f'user_obj is: {user_obj}')
    if not user_obj:
        return False, user_email
    session['user_email'] = user_email
    session['user_password'] = password
    try:
        session['first_name'] = user_obj['first_name'].capitalize()
    except:
        redirect(url_for('login',
                         failure_message=f'username or password were not found in the system '
                                         f' please try again'))
    if not user_email or not password:
        return render_template('login.html',
                               failure_message=f'{user_email} was not found in the system '
                                               f'or you provided a wrong password, please try again')
    try:
        if check_password_hash(user_obj['hashed_password'], password):
            logger.info(f'The hashed password is correct')
            try:
                token = jwt.encode(
                    {'user_id': str(user_obj['_id']),
                     'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=1440)},
                    app.config['SECRET_KEY'])
            except:
                logger.info(f'Failed to create a token')
                token = ''
            # decoded_token = token.decode("utf-8")
            session['x-access-token'] = token
            logger.info(f'The decoded token is: {token}')
            return token, user_email
        else:
            logger.info(f'The hashed password is incorrect')
            return False, user_email
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


def trigger_kubernetes_gke_build_jenkins(cluster_type: str = '',
                                         project_name: str = TROLLEY_PROJECT_NAME,
                                         user_id: str = 'pavel',
                                         cluster_version: str = '',
                                         zone: str = '',
                                         image_type: str = '',
                                         num_nodes: int = '',
                                         expiration_time: int = ''):
    server = Jenkins(url=JENKINS_URL, username=JENKINS_USER, password=JENKINS_PASSWORD)
    try:
        from utils import random_string
        job_id = server.build_job(name=JENKINS_KUBERNETES_GKE_DEPLOYMENT_JOB_NAME, parameters={
            PROJECT_NAME: project_name,
            CLUSTER_NAME: f'{user_id}-gke-{random_string(5)}',
            CLUSTER_VERSION: cluster_version,
            ZONE_NAME: zone,
            IMAGE_TYPE: image_type,
            NUM_NODES: num_nodes,
            EXPIRATION_TIME: expiration_time
        })
        logger.info(f'Job number {job_id - 1} was triggered on {JENKINS_KUBERNETES_GKE_DEPLOYMENT_JOB_NAME}')
        return 'OK'
    except:
        return 'fail'


def trigger_kubernetes_gke_autopilot_build_jenkins(cluster_type: str = '',
                                                   project_name: str = TROLLEY_PROJECT_NAME,
                                                   user_id: str = 'lior',
                                                   region: str = '', expiration_time: int = ''):
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
    zones_list = []
    command = f'aws ec2 describe-availability-zones --region {eks_location}'
    logger.info(f'Running a {command} command')
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    result_parsed = json.loads(result.stdout)
    availability_zones = result_parsed['AvailabilityZones']
    for availability_zone in availability_zones:
        zones_list.append(availability_zone['ZoneName'])
    return ','.join(zones_list)


def trigger_eks_build_jenkins(
        user_id: str = 'lior',
        version: str = '1.21',
        num_nodes: int = 3,
        expiration_time: int = 4):
    server = Jenkins(url=JENKINS_URL, username=JENKINS_USER, password=JENKINS_PASSWORD)
    try:
        job_id = server.build_job(name=JENKINS_EKS_DEPLOYMENT_JOB_NAME, parameters={
            CLUSTER_NAME: f'{user_id}-{EKS}-{random_string(5)}',
            VERSION: version,
            NUM_NODES: num_nodes,
            EXPIRATION_TIME: expiration_time
        })
        logger.info(f'Job number {job_id - 1} was triggered on {JENKINS_EKS_DEPLOYMENT_JOB_NAME}')
        return 'OK'
    except:
        return 'fail'


def trigger_aks_build_jenkins(
        user_id: str = '',
        num_nodes: int = '',
        kubernetes_version: str = '',
        aks_location: str = '',
        expiration_time: int = '',
        helm_installs: list = ''):
    if helm_installs:
        helm_installs_string = ','.join(helm_installs)
    else:
        helm_installs_string = ''
    aks_version = fetch_aks_version(kubernetes_version=kubernetes_version)
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


def delete_gke_cluster(cloud_provider: str = '', cluster_type: str = '', cluster_name: str = '', region: str = ''):
    server = Jenkins(url=JENKINS_URL, username=JENKINS_USER, password=JENKINS_PASSWORD)
    try:
        job_id = server.build_job(name=JENKINS_DELETE_GKE_JOB, parameters={
            CLUSTER_NAME: cluster_name,
            REGION_NAME: region,
        })
        logger.info(f'Job number {job_id - 1} was triggered on {JENKINS_DELETE_GKE_JOB}')
        return 'OK'
    except:
        return 'fail'


def delete_eks_cluster(cluster_name: str = '', region: str = '', cloud_provider: str = '', cluster_type: str = ''):
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
    server = Jenkins(url=JENKINS_URL, username=JENKINS_USER, password=JENKINS_PASSWORD)
    try:
        job_id = server.build_job(name=JENKINS_DELETE_AKS_JOB, parameters={
            CLUSTER_NAME: cluster_name,
        })
        logger.info(f'Job number {job_id - 1} was triggered on {JENKINS_DELETE_AKS_JOB}')
        return 'OK'
    except:
        return 'fail'


@app.route('/get_clusters_data', methods=[GET])
def get_clusters_data():
    cluster_type = request.args.get(CLUSTER_TYPE)
    user_name = request.args.get(USER_NAME)
    clusters_list = retrieve_available_clusters(cluster_type, user_name)
    return Response(json.dumps(clusters_list), status=200, mimetype=APPLICATION_JSON)


@app.route('/trigger_kubernetes_deployment', methods=[POST])
def trigger_kubernetes_deployment():
    content = request.get_json()
    if content['cluster_type'] == 'gke':
        trigger_kubernetes_gke_build_jenkins(**content)
        function_name = inspect.stack()[0][3]
        logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    elif content['cluster_type'] == 'gke_autopilot':
        trigger_kubernetes_gke_autopilot_build_jenkins(**content)
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


@app.route('/trigger_eks_deployment', methods=[POST])
def trigger_eks_deployment():
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    logger.info(f'A request for {function_name} was requested with the following parameters: {content}')
    trigger_eks_build_jenkins(**content)
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
        delete_gke_cluster(cloud_provider=GCP, cluster_name=expired_cluster['cluster_name'],
                           region=expired_cluster['zone_name'])
        # why only gke here
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
        delete_gke_cluster(**content)
        set_cluster_availability(cluster_type=content['cluster_type'], cluster_name=content['cluster_name'],
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


app.run(host='0.0.0.0', port=8081, debug=True)
# app.run(host='0.0.0.0', port=8081, debug=True, ssl_context=('certs/cert.pem', 'certs/key.pem'))
