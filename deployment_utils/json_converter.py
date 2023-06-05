import ast
from argparse import ArgumentParser, RawDescriptionHelpFormatter



def main(incoming_string: str = ''):
    encoded_content = ast.literal_eval(incoming_string)
    gcp_project_id = encoded_content['gcp_project_id']
    cluster_name = encoded_content['cluster_name']
    print(gcp_project_id)
    print(cluster_name)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--incoming_string', default='', type=str,
                        help='The stringified JSON of all the requested parameters')
    args = parser.parse_args()
    main(incoming_string=args.incoming_string)
