import ast
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from web.variables.variables import AWS, GCP

GITHUB_ACTIONS_ENV_FILE = os.environ.get('GITHUB_ENV', None)


def main(incoming_string: str = '', provider: str = ''):
    encoded_content = ast.literal_eval(incoming_string)
    eks_zones = ''
    eks_subnets = ''
    gcp_project_id = ''
    gke_machine_type = ''
    if provider == AWS:
        aws_access_key_id = encoded_content['aws_access_key_id']
        aws_secret_access_key = encoded_content['aws_secret_access_key']
        eks_zones = encoded_content['eks_zones']
        eks_subnets = encoded_content['eks_subnets']
        print(f'aws_access_key_id is: {aws_access_key_id}')
        print(f'aws_secret_access_key is: {aws_secret_access_key}')
        print(f'eks_zones is: {eks_zones}')
        print(f'eks_subnets is: {eks_subnets}')
    elif provider == GCP:
        gcp_project_id = encoded_content['gcp_project_id']
        gke_machine_type = encoded_content['gke_machine_type']
        print(f'gke_machine_type is: {gke_machine_type}')
        print(f'gcp_project_id is: {gcp_project_id}')

    cluster_name = encoded_content['cluster_name']
    user_name = encoded_content['user_name']
    cluster_version = encoded_content['cluster_version']
    region_name = encoded_content['region_name']
    zone_name = encoded_content['zone_name']
    image_type = encoded_content['image_type']
    num_nodes = encoded_content['num_nodes']
    expiration_time = encoded_content['expiration_time']
    print(f'cluster_name is: {cluster_name}')
    print(f'user_name is: {user_name}')
    print(f'cluster_version is: {cluster_version}')
    print(f'region_name is: {region_name}')
    print(f'zone_name is: {zone_name}')
    print(f'image_type is: {image_type}')
    print(f'num_nodes is: {num_nodes}')
    print(f'expiration_time is: {expiration_time}')

    with open(GITHUB_ACTIONS_ENV_FILE, "w") as myfile:
        myfile.write(f"GCP_PROJECT_ID={gcp_project_id}\n")
        myfile.write(f"CLUSTER_NAME={cluster_name}\n")
        myfile.write(f"USER_NAME={user_name}\n")
        myfile.write(f"CLUSTER_VERSION={cluster_version}\n")
        myfile.write(f"GKE_MACHINE_TYPE={gke_machine_type}\n")
        myfile.write(f"REGION_NAME={region_name}\n")
        myfile.write(f"ZONE_NAME={zone_name}\n")
        myfile.write(f"EKS_ZONES={eks_zones}\n")
        myfile.write(f"EKS_SUBNETS={eks_subnets}\n")
        myfile.write(f"IMAGE_TYPE={image_type}\n")
        myfile.write(f"NUM_NODES={num_nodes}\n")
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
