import json
import logging
import os
import platform
import sys
from subprocess import PIPE, run

import yaml
from kubernetes import config

TROLLEY_SERVER_URL = os.environ.get('TROLLEY_SERVER_URL', 'https://something.eu.ngrok.io')
CLUSTER_NAME = os.environ.get('CLUSTER_NAME', 'pavelzagalsky-gke-qjeigibl')
ZONE_NAME = os.environ.get('ZONE_NAME', 'us-east1-b')
PROJECT_NAME = os.environ.get('PROJECT_NAME', 'trolley-361905')
CLUSTER_TYPE = os.environ.get('CLUSTER_TYPE', 'gke')
MONGO_USER = os.environ.get('MONGO_USER', 'pavelzagalsky-gke-qjeigibl')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', 'password')
MONGO_URL = os.environ.get('MONGO_URL', 'localhost')
KUBECONFIG_PATH = os.environ.get('KUBECONFIG_PATH', '/home/runner/.kube/config')

if 'macOS' in platform.platform():
    home_path = f'{os.getcwd()}'
    deployment_yaml_path_ = "/".join(home_path.split("/")[:-1])
else:
    home_path = '/home/runner/work'
    print(f'home_path is: {home_path}')
    print(f'trolley_deployment_path is: {home_path}')
    deployment_yaml_path_ = "/".join(home_path.split("/"))
    print(f'deployment_yaml_path is: {deployment_yaml_path_}')

log_file_name = 'agent_main.log'
deployment_yaml_path = f'{deployment_yaml_path_}/agents/k8s_agent/agent_deployment_yamls'
print(f'deployment_yaml_path is: {deployment_yaml_path}')
base_trolley_agent_full_path = f'{deployment_yaml_path}/full_agent_deployment.yml'
print(f'base_trolley_agent_full_path is: {base_trolley_agent_full_path}')
edited_trolley_agent_full_path = f'{deployment_yaml_path}/edited_agent_deployment.yml'
print(f'edited_trolley_agent_full_path is: {edited_trolley_agent_full_path}')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"{home_path}/{log_file_name}"),
        logging.StreamHandler(sys.stdout)
    ]
)

logging.info(f'deployment_yaml_path_ is {deployment_yaml_path_}')
logging.info(f'deployment_yaml_path is {deployment_yaml_path}')
logging.info(f'base_trolley_agent_full_path is {base_trolley_agent_full_path}')
logging.info(f'edited_trolley_agent_full_path is {edited_trolley_agent_full_path}')
logging.info(os.getcwd())
logging.info(os.listdir())


def main():
    kubeconfig_gen_command = f'gcloud container clusters get-credentials {CLUSTER_NAME} ' \
                             f'--region {ZONE_NAME} --project {PROJECT_NAME}'

    logging.info(f'Running kubeconfig creation command {kubeconfig_gen_command}')
    result = run(kubeconfig_gen_command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    if result.returncode > 0:
        logging.error(f'A problem occurred: {result.stderr}')
        sys.exit()
    else:
        logging.info(f'{kubeconfig_gen_command} command ran successfully: {result.stdout}')
    try:
        config.load_kube_config(KUBECONFIG_PATH)
    except config.config_exception:
        raise Exception("Could not configure kubernetes python client")
    stream = open(base_trolley_agent_full_path, "r")
    deployment_yamls = yaml.load_all(stream, yaml.FullLoader)

    # Find a better way to handle this monstrosity
    deployments_string = ''
    for deployment_yaml in deployment_yamls:
        if deployment_yaml['kind'] == 'Deployment':
            for env_value in deployment_yaml['spec']['template']['spec']['containers'][0]['env']:
                if env_value['name'] == 'SERVER_URL':
                    deployment_yaml['spec']['template']['spec']['containers'][0]['env'][2]['value'] = TROLLEY_SERVER_URL
                if env_value['name'] == 'CLUSTER_NAME':
                    deployment_yaml['spec']['template']['spec']['containers'][0]['env'][3]['value'] = CLUSTER_NAME
                if env_value['name'] == 'CLUSTER_TYPE':
                    deployment_yaml['spec']['template']['spec']['containers'][0]['env'][5]['value'] = CLUSTER_TYPE
                if env_value['name'] == 'MONGO_USER':
                    deployment_yaml['spec']['template']['spec']['containers'][0]['env'][7]['value'] = MONGO_USER
                if env_value['name'] == 'MONGO_PASSWORD':
                    deployment_yaml['spec']['template']['spec']['containers'][0]['env'][8]['value'] = MONGO_PASSWORD
                if env_value['name'] == 'MONGO_URL':
                    deployment_yaml['spec']['template']['spec']['containers'][0]['env'][9]['value'] = MONGO_URL
                if env_value['name'] == 'PROJECT_NAME':
                    deployment_yaml['spec']['template']['spec']['containers'][0]['env'][10]['value'] = \
                        PROJECT_NAME.split('-')[0]
        deployment_string = json.dumps(deployment_yaml)
        deployments_string += f'---\n{deployment_string}\n'
    with open(edited_trolley_agent_full_path, 'w') as f:
        f.write(deployments_string)
    command = f'kubectl apply -f {edited_trolley_agent_full_path}'
    result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    if result.returncode > 0:
        logging.error(f'A problem occurred: {result.stderr}')
        sys.exit()
    else:
        logging.info(f'{command} command ran successfully: {result.stdout}')
    logging.info(result)


if __name__ == '__main__':
    main()
