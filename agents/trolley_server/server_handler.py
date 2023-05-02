import logging
import os
import platform
import sys
from dataclasses import asdict

from requests import post, exceptions

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


class ServerRequest:
    def __init__(self, debug_mode: bool = True, timeout: int = 60, cluster_data: any = None, operation: str = None,
                 server_url: str = None):
        self.debug_mode = debug_mode
        self.timeout = timeout
        self.cluster_data = cluster_data
        self.operation = operation
        self.server_url = server_url

    @staticmethod
    def build_request_url(self):
        if self.debug_mode:
            return f'http://localhost:8081/{self.operation}'
        else:
            return f'{self.server_url}/{self.operation}'

    def send_server_request(self):
        headers = {'request-source': 'kubernetes'}
        request_url = self.build_request_url(self)
        try:
            post(url=request_url, json=asdict(self.cluster_data), headers=headers)
        except exceptions.RequestException as e:
            logging.error(f'post request failed with the following message: {e}')
