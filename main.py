import inspect
import json
import os

from jenkins import Jenkins
from flask import request, Response, Flask

from utils import random_string

from mongo_handler import config
from variables import TROLLEY_PROJECT_NAME, PROJECT_NAME, CLUSTER_NAME, CLUSTER_VERSION, ZONE_NAME, IMAGE_TYPE, \
    NUM_NODES, EXPIRATION_TIME, REGION_NAME, POST, GET, VERSION, AKS_LOCATION, AKS_VERSION, HELM_INSTALLS, EKS, \
    APPLICATION_JSON

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

PROJECT_ID = config['DEFAULT']['project_id']
JENKINS_URL = 'http://' + config['DEFAULT']['jenkins_url'] + ':8080'
JENKINS_USER = config['DEFAULT']['jenkins_user']

JENKINS_PASSWORD = os.getenv('JENKINS_PASSWORD')
JENKINS_KUBERNETES_GKE_DEPLOYMENT_JOB_NAME = 'gke_deployment'
JENKINS_KUBERNETES_GKE_AUTOPILOT_DEPLOYMENT_JOB_NAME = 'gke_autopilot_deployment'
JENKINS_EKS_DEPLOYMENT_JOB_NAME = 'eks_deployment'
JENKINS_AKS_DEPLOYMENT_JOB_NAME = 'aks_deployment'


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
        print(f'Job number {job_id - 1} was triggered on {JENKINS_KUBERNETES_GKE_DEPLOYMENT_JOB_NAME}')
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
        print(f'Job number {job_id - 1} was triggered on {JENKINS_KUBERNETES_GKE_AUTOPILOT_DEPLOYMENT_JOB_NAME}')

        return 'OK'
    except:
        return 'fail'


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
        print(f'Job number {job_id - 1} was triggered on {JENKINS_EKS_DEPLOYMENT_JOB_NAME}')
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
        print(f'Job number {job_id - 1} was triggered on {JENKINS_AKS_DEPLOYMENT_JOB_NAME}')
        return 'OK'
    except:
        return 'fail'


@app.route('/trigger_kubernetes_deployment', methods=[POST])
def trigger_kubernetes_deployment():
    content = request.get_json()
    if content['cluster_type'] == 'gke':
        trigger_kubernetes_gke_build_jenkins(**content)
        function_name = inspect.stack()[0][3]
        print(f'A request for {function_name} was requested with the following parameters: {content}')
    elif content['cluster_type'] == 'gke_autopilot':
        trigger_kubernetes_gke_autopilot_build_jenkins(**content)
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


@app.route('/trigger_eks_deployment', methods=[POST])
def trigger_eks_deployment():
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    print(f'A request for {function_name} was requested with the following parameters: {content}')
    trigger_eks_build_jenkins(**content)
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


@app.route('/trigger_aks_deployment', methods=[POST])
def trigger_aks_deployment():
    content = request.get_json()
    function_name = inspect.stack()[0][3]
    print(f'A request for {function_name} was requested with the following parameters: {content}')
    trigger_aks_build_jenkins(**content)
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


@app.route('/healthz', methods=[GET, POST])
def healthz():
    print('A request was received')
    return Response(json.dumps('OK'), status=200, mimetype=APPLICATION_JSON)


app.run(host='0.0.0.0', port=8081, debug=True)
# app.run(host='0.0.0.0', port=8081, debug=True, ssl_context=('certs/cert.pem', 'certs/key.pem'))
