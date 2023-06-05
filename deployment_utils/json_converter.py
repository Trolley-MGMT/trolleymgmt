import ast
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter


GITHUB_ACTIONS_ENV_FILE = os.getenv('GITHUB_ENV')



def main(incoming_string: str = ''):
    encoded_content = ast.literal_eval(incoming_string)
    gcp_project_id = encoded_content['gcp_project_id']
    cluster_name = encoded_content['cluster_name']
    user_name = encoded_content['user_name']
    cluster_version = encoded_content['cluster_version']
    gke_machine_type = encoded_content['gke_machine_type']
    region_name = encoded_content['region_name']
    zone_name = encoded_content['zone_name']
    image_type = encoded_content['image_type']
    num_nodes = encoded_content['num_nodes']
    expiration_time = encoded_content['expiration_time']
    print(f'gcp_project_id is: {gcp_project_id}')
    print(f'cluster_name is: {cluster_name}')
    print(f'user_name is: {user_name}')
    print(f'cluster_version is: {cluster_version}')
    print(f'gke_machine_type is: {gke_machine_type}')
    print(f'region_name is: {region_name}')
    print(f'zone_name is: {zone_name}')
    print(f'image_type is: {image_type}')
    print(f'num_nodes is: {num_nodes}')
    print(f'expiration_time is: {expiration_time}')

    with open(GITHUB_ACTIONS_ENV_FILE, "w") as myfile:
        myfile.write(f"GCP_PROJECT_ID={gcp_project_id}")

    with open(GITHUB_ACTIONS_ENV_FILE, "r") as myfile:
        lines = myfile.readlines()
        print(lines)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--incoming_string', default='', type=str,
                        help='The stringified JSON of all the requested parameters')
    args = parser.parse_args()
    main(incoming_string=args.incoming_string)