import ast
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import platform

import yaml

from web.variables.variables import AWS, GCP, AZ

if 'Darwin' in platform.system():
    EKSCTL_DEPLOYMENT_FILE = f'{os.getcwd()}/eksctl_deployment_file.yaml'
else:
    EKSCTL_DEPLOYMENT_FILE = "/home/runner/eksctl_deployment_file.yaml"
    GITHUB_ACTIONS_ENV_FILE = os.environ.get('GITHUB_ENV', None)


def main(incoming_string: str = '', provider: str = ''):
    print(f'incoming_string is: {incoming_string}')
    encoded_content = ast.literal_eval(incoming_string)
    print(f'encoded content is: {encoded_content}')
    region_name = ''
    zone_name = ''
    gcp_project_id = ''
    gke_machine_type = ''
    image_type = ''
    eksctl_deployment_file = ''
    az_location_name = ''
    az_resource_group = ''
    az_subscription_id = ''
    az_machine_type = ''
    if provider == AWS:
        region_name = encoded_content['region_name']
        eksctl_deployment_file = encoded_content['eksctl_deployment_file']
        print(f'eksctl_object is: {eksctl_deployment_file}')
        file = open(EKSCTL_DEPLOYMENT_FILE, "w")
        yaml.dump(eksctl_deployment_file, file)
        file.close()
    elif provider == GCP:
        zone_name = encoded_content['zone_name']
        gcp_project_id = encoded_content['gcp_project_id']
        gke_machine_type = encoded_content['gke_machine_type']
        image_type = encoded_content['image_type']
        region_name = encoded_content['region_name']
    elif provider == AZ:
        az_location_name = encoded_content['az_location_name']
        az_resource_group = encoded_content['az_resource_group']
        az_subscription_id = encoded_content['az_subscription_id']
        az_machine_type = encoded_content['az_machine_type']
        print(f'az_location_nam is: {az_location_name}')
        print(f'az_resource_group is: {az_resource_group}')
        print(f'az_subscription_id is: {az_subscription_id}')
        print(f'az_machine_type is: {az_machine_type}')

    secret_key = encoded_content['secret_key']
    mongo_url = encoded_content['mongo_url']
    mongo_user = encoded_content['mongo_user']
    mongo_password = encoded_content['mongo_password']
    cluster_name = encoded_content['cluster_name']
    project_name = encoded_content['project_name']
    user_name = encoded_content['user_name']
    cluster_version = encoded_content['cluster_version']
    num_nodes = encoded_content['num_nodes']
    expiration_time = encoded_content['expiration_time']

    print(f'mongo_url is: {mongo_url}')
    print(f'mongo_user is: {mongo_user}')
    print(f'cluster_name is: {cluster_name}')
    print(f'project_name is: {project_name}')
    print(f'user_name is: {user_name}')
    print(f'cluster_version is: {cluster_version}')
    print(f'region_name is: {region_name}')
    print(f'zone_name is: {zone_name}')
    print(f'image_type is: {image_type}')
    print(f'num_nodes is: {num_nodes}')
    print(f'expiration_time is: {expiration_time}')

    if not 'Darwin' in platform.system():
        with open(GITHUB_ACTIONS_ENV_FILE, "w") as myfile:
            myfile.write(f"SECRET_KEY={secret_key}\n")
            myfile.write(f"PROJECT_NAME={project_name}\n")
            myfile.write(f"MONGO_URL={mongo_url}\n")
            myfile.write(f"MONGO_USER={mongo_user}\n")
            myfile.write(f"MONGO_PASSWORD={mongo_password}\n")
            myfile.write(f"CLUSTER_NAME={cluster_name}\n")
            myfile.write(f"USER_NAME={user_name}\n")
            myfile.write(f"CLUSTER_VERSION={cluster_version}\n")
            myfile.write(f"GCP_PROJECT_ID={gcp_project_id}\n")
            myfile.write(f"GKE_MACHINE_TYPE={gke_machine_type}\n")
            myfile.write(f"REGION_NAME={region_name}\n")
            myfile.write(f"ZONE_NAME={zone_name}\n")
            myfile.write(f"IMAGE_TYPE={image_type}\n")
            myfile.write(f"NUM_NODES={num_nodes}\n")
            myfile.write(f"AZ_LOCATION_NAME={az_location_name}\n")
            myfile.write(f"AZ_RESOURCE_GROUP={az_resource_group}\n")
            myfile.write(f"AZ_SUBSCRIPTION_ID={az_subscription_id}\n")
            myfile.write(f"AZ_MACHINE_TYPE={az_machine_type}\n")
            myfile.write(f"EKSCTL_DEPLOYMENT_FILE={eksctl_deployment_file}\n")
            myfile.write(f"EXPIRATION_TIME={expiration_time}\n")

        with open(GITHUB_ACTIONS_ENV_FILE, "r") as myfile:
            lines = myfile.readlines()
            print(lines)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--incoming_string', default='', type=str,
                        help='The stringified JSON of all the requested parameters')
    parser.add_argument('--provider', default='gcp', type=str, help='The Cloud Provider')
    args = parser.parse_args()
    main(incoming_string=args.incoming_string, provider=args.provider)
