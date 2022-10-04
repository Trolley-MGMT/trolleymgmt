import logging
from dataclasses import asdict

from web.mongo_handler.mongo_objects import AgentsDataObject
from web.mongo_handler.mongo_utils import insert_agents_data_object

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('../agent_operations.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def insert_agent_data(cluster_name: str = None, context_name: str = None, namespaces: list = None,
                      deployments: list = None, stateful_sets: list = None, pods: list = None,
                      containers: list = None, daemonsets: list = None, services: list = None):
    agents_data_object = AgentsDataObject(cluster_name=cluster_name, context_name=context_name, namespaces=namespaces,
                                          deployments=deployments, stateful_sets=stateful_sets, pods=pods,
                                          containers=containers, daemonsets=daemonsets, services=services)
    if insert_agents_data_object(asdict(agents_data_object)):
        logger.info('Agent data inserted successfully')
    else:
        logger.info('Agent data did not get inserted')
