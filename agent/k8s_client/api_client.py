import getpass
import logging

import kubernetes.config
from kubernetes.client import ApiClient

KUBECONFIG_TEMP_PATH = f'/Users/{getpass.getuser()}/.kube/temp_config'

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
logger = logging.getLogger()
log_path = '/var/log/'
file_name = 'agent_main.log'
fileHandler = logging.FileHandler(f"{log_path}/{file_name}")
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)


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
                logger.error(f'Error loading incluster configuration')
        if self.debug_mode:
            clusters_contexts, _ = kubernetes.config.list_kube_config_contexts()
            for cluster_context in clusters_contexts:
                if cluster_context['name'] == self.context_name:
                    logger.info(f'Loading configuration for {self.context_name} context name')
                    api_client = kubernetes.config.new_client_from_config(context=self.context_name)
                    return api_client
            api_client = kubernetes.config.new_client_from_config(config_file=KUBECONFIG_TEMP_PATH)
            return api_client
        kubernetes.config.load_incluster_config()
        return ApiClient()
