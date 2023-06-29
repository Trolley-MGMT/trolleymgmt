import logging
import os
import sys
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from web.cluster_operations import ClusterOperation
from web.mongo_handler.mongo_utils import retrieve_expired_clusters, set_cluster_availability
from web.cluster_operations__ import delete_gke_cluster, delete_aks_cluster, delete_eks_cluster
from web.variables.variables import GKE, AKS, EKS, CLUSTER_NAME, USER_NAME, ZONE_NAME

DOCKER_ENV = os.getenv('DOCKER_ENV', False)

log_file_name = 'server.log'
if DOCKER_ENV:
    log_file_path = f'/var/log/{log_file_name}'
else:
    log_file_path = f'{os.getcwd()}/{log_file_name}'

logger = logging.getLogger(__name__)

file_handler = logging.FileHandler(filename=log_file_path)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers
)


def delete_clusters(cluster_type: str):
    expired_clusters_list = retrieve_expired_clusters(cluster_type=cluster_type)
    logger.info(f'clusters to expire: {expired_clusters_list}')
    for expired_cluster in expired_clusters_list:
        content = {CLUSTER_NAME: expired_cluster[CLUSTER_NAME],
                   USER_NAME: expired_cluster[USER_NAME],
                   ZONE_NAME: expired_cluster[ZONE_NAME]}
        cluster_operations = ClusterOperation(**content)
        print(f'expiring {expired_cluster} cluster')
        if cluster_type == GKE:
            cluster_operations.delete_gke_cluster()
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
