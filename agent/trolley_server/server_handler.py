import json
from dataclasses import asdict

from requests import post


class ServerRequest:
    def __init__(self, debug_mode: bool = True, timeout: int = 60, agent_data: any = None, operation: str = None,
                 server_url: str = None):
        self.debug_mode = debug_mode
        self.timeout = timeout
        self.agent_data = agent_data
        self.operation = operation
        self.server_url = server_url

    @staticmethod
    def build_request_url(self):
        if self.debug_mode:
            return f'http://localhost:8081/{self.operation}'
        else:
            return f'{self.server_url}/{self.operation}'

    def send_server_request(self):
        request_url = self.build_request_url(self)
        post(url=request_url, json=asdict(self.agent_data))
