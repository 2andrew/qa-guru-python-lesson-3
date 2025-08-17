import pytest

from tests.constants import USERS_PREFIX, STATUS_PREFIX
from tests.utils.base_session import BaseSession
from tests.utils.config import Server


@pytest.fixture(scope='session')
def user_client(env):
    with BaseSession(base_url=f"{Server(env).user_service}{USERS_PREFIX}") as session:
        yield session

@pytest.fixture(scope='session')
def status_client(env):
    with BaseSession(base_url=f"{Server(env).user_service}{STATUS_PREFIX}") as session:
        yield session
