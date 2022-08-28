from argparse import ArgumentParser, RawDescriptionHelpFormatter

from mongo_handler.mongo_utils import set_cluster_availability


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--cluster_type', default='gke', type=str, help='Type of the cluster built')
    parser.add_argument('--cluster_name', default='gke', type=str, help='Name of the cluster to delete')
    parser.add_argument('--availability', choices=('True', 'False'), help='Select cluster\'s availability')
    args = parser.parse_args()
    print(f'Settings {args.cluster_name} cluster on {args.cluster_type} cloud to {args.availability} availability')
    set_cluster_availability(cluster_type=args.cluster_type, cluster_name=args.cluster_name,
                             availability=args.availability)
