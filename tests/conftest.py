import os

import dotenv
import pytest

from tests.factories.UserFactory import UserFactory


@pytest.fixture(scope="session", autouse=True)
def envs():
    dotenv.load_dotenv()


@pytest.fixture(scope="session")
def app_url():
    return os.getenv("APP_URL")

@pytest.fixture(scope="module")
def user_factory():
    return UserFactory()
