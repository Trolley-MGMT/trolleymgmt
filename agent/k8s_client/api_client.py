import kubernetes.config
from kubernetes.client import ApiClient


class K8sApiClient:
    def __init__(self, debug_mode: bool, cluster_name: str):
        self.cluster_name = cluster_name
        self.debug_mode = debug_mode

    def fetch_api_client(self) -> ApiClient:
        if self.debug_mode:
            clusters_contexts, _ = kubernetes.config.list_kube_config_contexts()
            for cluster_context in clusters_contexts:
                if cluster_context['name'] == self.cluster_name:
                    api_client = kubernetes.config.new_client_from_config(context=self.cluster_name)
                    return api_client
        kubernetes.config.load_incluster_config()
        return ApiClient()
