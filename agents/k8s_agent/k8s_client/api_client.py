import getpass
import logging
import os
import platform
import sys

import kubernetes.config
from kubernetes.client import ApiClient

KUBECONFIG_TEMP_PATH = f'/Users/{getpass.getuser()}/.kube/temp_config'

if 'macOS' in platform.platform():
    log_path = f'{os.getcwd()}'
    file_name = 'agent_main.log'
else:
    log_path = '/var/log/'
    file_name = 'agent_main.log'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"{log_path}/{file_name}"),
        logging.StreamHandler(sys.stdout)
    ]
)


class K8sApiClient:
    def __init__(self, debug_mode: bool, in_cluster_mode: bool, cluster_name: str, context_name: str):
        self.cluster_name = cluster_name
        self.context_name = context_name
        self.debug_mode = debug_mode
        self.in_cluster_mode = in_cluster_mode

    def fetch_api_client(self) -> ApiClient:
        if self.in_cluster_mode:
            try:
                kubernetes.config.load_incluster_config()
                return ApiClient()
            except kubernetes.config.ConfigException:
                logging.error(f'Error loading incluster configuration')
        else:
            clusters_contexts, _ = kubernetes.config.list_kube_config_contexts()
            for cluster_context in clusters_contexts:
                if cluster_context['name'] == self.context_name:
                    logging.info(f'Loading configuration for {self.context_name} context name')
                    api_client = kubernetes.config.new_client_from_config(context=self.context_name)
                    return api_client
            api_client = kubernetes.config.new_client_from_config(config_file=KUBECONFIG_TEMP_PATH)
            return api_client
