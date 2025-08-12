
from http import HTTPStatus

import requests

def test_availability(app_url):
    response = requests.get(f"{app_url}/status/")
    assert response.status_code == HTTPStatus.OK
    is_users_loaded = response.json()['users']
    assert is_users_loaded is True
