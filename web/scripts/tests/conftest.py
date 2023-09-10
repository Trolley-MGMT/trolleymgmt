import pytest


def pytest_addoption(parser):
    parser.addoption("--aws-access-key-id", action="store", default=None, help="aws_access_key_id")
    parser.addoption("--aws-secret-access-key", action="store", default=None, help="aws_secret_access_key ")

@pytest.fixture
def aws_access_key_id(request):
    return request.config.getoption("--aws-access-key-id")

@pytest.fixture
def aws_secret_access_key(request):
    return request.config.getoption("--aws-secret-access-key")