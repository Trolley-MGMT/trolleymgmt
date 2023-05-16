import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from web.mongo_handler.mongo_utils import retrieve_expired_clusters, set_cluster_availability
from web.cluster_operations__ import delete_gke_cluster, delete_aks_cluster, delete_eks_cluster
from web.variables.variables import GKE, AKS, EKS


def delete_clusters(cluster_type: str):
    expired_clusters_list = retrieve_expired_clusters(cluster_type=cluster_type)
    print(f'clusters to expire: {expired_clusters_list}')
    for expired_cluster in expired_clusters_list:
        print(f'expiring {expired_cluster} cluster')
        if cluster_type == GKE:
            delete_gke_cluster(cluster_name=expired_cluster['cluster_name'])
        elif cluster_type == AKS:
            delete_aks_cluster(cluster_name=expired_cluster['cluster_name'])
        elif cluster_type == EKS:
            delete_eks_cluster(cluster_name=expired_cluster['cluster_name'])
        time.sleep(5)
        set_cluster_availability(cluster_type=cluster_type, cluster_name=expired_cluster['cluster_name'],
                                 availability=False)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--cluster_type', default='gke', type=str, help='Type of the cluster built')
    args = parser.parse_args()
    delete_clusters(cluster_type=args.cluster_type)
