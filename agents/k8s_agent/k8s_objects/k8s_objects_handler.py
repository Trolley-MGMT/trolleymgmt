def fetch_namespaces_list(k8s_api) -> list:
    namespaces_list = []
    namespaces = k8s_api.list_namespace().items
    for namespace in namespaces:
        namespaces_list.append(namespace.metadata.name)
    return namespaces_list


def fetch_pods_list(k8s_api, namespaces_list) -> list:
    pods_list = []
    for namespace in namespaces_list:
        pods = k8s_api.list_namespaced_pod(namespace).items
        for pod in pods:
            pods_list.append({'namespace': namespace,
                              'pod': pod.metadata.name})
    return pods_list


def fetch_containers_list(k8s_api, namespaces_list: list = None) -> list:
    containers_list = []
    for namespace in namespaces_list:
        pods = k8s_api.list_namespaced_pod(namespace).items
        for pod in pods:
            if len(pod.spec.containers) > 1:
                for container in pod.spec.containers:
                    log = k8s_api.read_namespaced_pod_log(name=pod.metadata.name, container=container.name,
                                                          namespace=namespace)
                    containers_list.append({'namespace': namespace,
                                            'pod_name': pod.metadata.name,
                                            'container_name': container.name,
                                            'log': str(log)})
            else:
                log = k8s_api.read_namespaced_pod_log(name=pod.metadata.name,
                                                      namespace=namespace)
                containers_list.append({'namespace': namespace,
                                        'pod': pod.metadata.name,
                                        'container': pod.spec.containers[0].name,
                                        'log': str(log)})
    return containers_list


def fetch_deployments_list(apis_api, namespaces_list: '') -> list:
    deployments_list = []
    for namespace in namespaces_list:
        deployments = apis_api.list_namespaced_deployment(namespace)
        if len(deployments.items) > 0:
            if len(deployments.items) == 1:
                deployment_data = apis_api.read_namespaced_deployment(name=deployments.items[0].metadata.name,
                                                                      namespace=namespace)
                deployments_list.append({'namespace': namespace, 'deployment':
                    deployments.items[0].metadata.name,
                                         'deployment_data': str(deployment_data)})
            else:
                for deployment in deployments.items:
                    deployment_data = apis_api.read_namespaced_deployment(name=deployment.metadata.name,
                                                                          namespace=namespace)
                    deployments_list.append({'namespace': namespace,
                                             'deployment': deployment.metadata.name,
                                             'deployment_data': str(deployment_data)})
    return deployments_list


def fetch_daemonsets_list(apis_api, namespaces_list: '') -> list:
    daemonsets_list = []
    for namespace in namespaces_list:
        daemonsets = apis_api.list_namespaced_daemon_set(namespace)
        if len(daemonsets.items) > 0:
            if len(daemonsets.items) == 1:
                daemonset_data = apis_api.read_namespaced_daemon_set(name=daemonsets.items[0].metadata.name,
                                                                     namespace=namespace)
                daemonsets_list.append({'namespace': namespace, 'daemonsets':
                    daemonsets.items[0].metadata.name, 'daemonset_data': str(daemonset_data)})
            else:
                for daemonset in daemonsets.items:
                    daemonset_data = apis_api.read_namespaced_daemon_set(name=daemonset.metadata.name,
                                                                         namespace=namespace)
                    daemonsets_list.append({'namespace': namespace,
                                            'daemonsets': daemonset.metadata.name,
                                            'daemonset_data': str(daemonset_data)})
    return daemonsets_list


def fetch_services_list(k8s_api, namespaces_list: '') -> list:
    services_list = []
    for namespace in namespaces_list:
        services = k8s_api.list_namespaced_service(namespace)
        if len(services.items) > 0:
            if len(services.items) == 1:
                service_data = k8s_api.read_namespaced_service(name=services.items[0].metadata.name,
                                                               namespace=namespace)
                services_list.append({'namespace': namespace, 'deployment':
                    services.items[0].metadata.name,
                                      'service_data': str(service_data)})
            else:
                for service in services.items:
                    service_data = k8s_api.read_namespaced_service(name=service.metadata.name,
                                                                   namespace=namespace)
                    services_list.append({'namespace': namespace,
                                          'service': service.metadata.name,
                                          'service_data': str(service_data)})
    return services_list


def fetch_stateful_sets_list(apis_api, namespaces_list):
    stateful_sets_list = []
    for namespace in namespaces_list:
        stateful_sets = apis_api.list_namespaced_stateful_set(namespace)
        if len(stateful_sets.items) > 0:
            if len(stateful_sets.items) == 1:
                stateful_set_data = apis_api.read_namespaced_stateful_set(name=stateful_sets.items[0].metadata.name,
                                                                          namespace=namespace)
                stateful_sets_list.append({'namespace': namespace, 'stateful_set':
                    stateful_sets.items[0].metadata.name, 'stateful_set_data': str(stateful_set_data)})
            else:
                for stateful_set in stateful_sets.items:
                    stateful_set_data = apis_api.read_namespaced_stateful_set(name=stateful_set.metadata.name,
                                                                              namespace=namespace)
                    stateful_sets_list.append({'namespace': namespace,
                                               'stateful_set': stateful_set.metadata.name,
                                               'stateful_set_data': str(stateful_set_data)})
    return stateful_sets_list
