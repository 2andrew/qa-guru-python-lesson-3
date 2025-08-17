import dotenv
import pytest

from tests.factories.UserFactory import UserFactory

pytest_plugins = ['fixture_sessions']


@pytest.fixture(scope="session", autouse=True)
def envs():
    dotenv.load_dotenv()


def pytest_addoption(parser):
    parser.addoption("--env", default="dev")


@pytest.fixture(scope="session")
def env(request):
    return request.config.getoption("--env")

@pytest.fixture(scope="module")
def user_factory():
    return UserFactory()
