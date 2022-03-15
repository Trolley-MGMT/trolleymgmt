import inspect
import json
import os

from jenkins import Jenkins
from flask import request, Response, app, Flask

from utils import random_string

from mongo_handler import config
from variables import TROLLEY_PROJECT_NAME, PROJECT_NAME, CLUSTER_NAME, CLUSTER_VERSION, ZONE_NAME, IMAGE_TYPE, \
    NUM_NODES, EXPIRATION_TIME, REGION_NAME, POST, GET

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

PROJECT_ID = config['DEFAULT']['project_id']
JENKINS_URL = 'http://' + config['DEFAULT']['jenkins_url'] + ':8080'
JENKINS_USER = config['DEFAULT']['jenkins_user']

JENKINS_PASSWORD = os.getenv('JENKINS_PASSWORD')
JENKINS_KUBERNETES_GKE_DEPLOYMENT_JOB_NAME = 'gke_deployment'
JENKINS_KUBERNETES_GKE_AUTOPILOT_DEPLOYMENT_JOB_NAME = 'gke_autopilot_deployment'


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
                                                   user_id: str = 'pavel',
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


@app.route('/trigger_kubernetes_deployment', methods=[POST])
def trigger_kubernetes_deployment():
    content = request.get_json()
    if content['cluster_type'] == 'gke':
        trigger_kubernetes_gke_build_jenkins(**content)
        function_name = inspect.stack()[0][3]
        print(f'A request for {function_name} was requested with the following parameters: {content}')
    elif content['cluster_type'] == 'gke_autopilot':
        trigger_kubernetes_gke_autopilot_build_jenkins(**content)
    return Response(json.dumps('OK'), status=200, mimetype='application/json')


@app.route('/healthz', methods=[GET, POST])
def healthz():
    print('A request was received')
    return Response(json.dumps('OK'), status=200, mimetype='application/json')


app.run(host='0.0.0.0', port=8081, debug=True)
# app.run(host='0.0.0.0', port=8081, debug=True, ssl_context=('certs/cert.pem', 'certs/key.pem'))
