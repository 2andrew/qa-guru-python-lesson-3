import json
from http import HTTPStatus
from math import ceil

import pytest
import requests

from app.models.User import User
from tests.data_generators.UserMaker import UserGenerator


@pytest.fixture(scope="module")
def fill_test_data(app_url):
    with open("users.json") as f:
        test_data_users = json.load(f)
    api_users = []
    for user in test_data_users:
        response = requests.post(f"{app_url}/api/users/", json=user)
        api_users.append(response.json())

    user_ids = [user["id"] for user in api_users]

    yield user_ids

    for user_id in user_ids:
        requests.delete(f"{app_url}/api/users/{user_id}")


@pytest.fixture
def users(app_url):
    response = requests.get(f"{app_url}/api/users/")
    assert response.status_code == HTTPStatus.OK
    return response.json()


@pytest.fixture
def make_user(app_url):
    gen = UserGenerator(app_url)
    yield gen
    gen.cleanup()


@pytest.mark.usefixtures("fill_test_data")
def test_users(app_url):
    response = requests.get(f"{app_url}/api/users/")
    assert response.status_code == HTTPStatus.OK

    _users = response.json()["items"]
    for user in _users:
        User.model_validate(user)


@pytest.mark.usefixtures("fill_test_data")
def test_users_no_duplicates(users):
    users_ids = [user["id"] for user in users["items"]]
    assert len(users_ids) == len(set(users_ids))


@pytest.mark.usefixtures("fill_test_data")
@pytest.mark.parametrize("user_id", [1, 6, 12])
def test_user(app_url, user_id):
    response = requests.get(f"{app_url}/api/users/{user_id}")
    assert response.status_code == HTTPStatus.OK

    user = response.json()
    User.model_validate(user)


@pytest.mark.usefixtures("fill_test_data")
@pytest.mark.parametrize("user_id", [13])
def test_user_nonexistent_values(app_url, user_id):
    response = requests.get(f"{app_url}/api/users/{user_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.usefixtures("fill_test_data")
@pytest.mark.parametrize("user_id", [-1, 0, "fafaf"])
def test_user_invalid_values(app_url, user_id):
    response = requests.get(f"{app_url}/api/users/{user_id}")
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.usefixtures("fill_test_data")
@pytest.mark.parametrize("page, size",
                         [(1, 1), (1, 3), (1, 12), (1, 100),
                          (3, 1), (3, 4), (4, 3), (7, 1), (7, 2),
                          (12, 1), (7, 8), (98, 99)])
def test_app_pagination(app_url, page, size, users):
    response = requests.get(f"{app_url}/api/users/?page={page}&size={size}")
    assert response.status_code == HTTPStatus.OK

    body = response.json()

    total = users["total"]
    total_pages = ceil(total / size)

    assert body["total"] == total, "Invalid total"
    assert body["page"] == page, "Invalid page"
    assert body["size"] == size, "Invalid size"
    assert body["pages"] == total_pages, "Invalid amount of pages"

    assert len(body["items"]) <= size, "Invalid amount of items"

    start = (page - 1) * size
    end = start + size
    expected_items = users["items"][start:end] if start < total else []

    assert body["items"] == expected_items, "Items do not match expected slice"

    if page > total_pages:
        assert body["items"] == [], "Expected no items beyond the last page"

    if page == total_pages and total > 0:
        expected_last_count = total - size * (total_pages - 1)
        assert len(body["items"]) == expected_last_count, "Invalid amount of items on the last page"


def test_create_user(app_url, user_factory, make_user):
    payload = user_factory.user()
    created = make_user.create(payload)
    User.model_validate(created)

    assert {k: v for k, v in created.items() if k != "id"} == payload

    get_resp = requests.get(f"{app_url}/api/users/{created['id']}")
    assert get_resp.status_code == HTTPStatus.OK
    User.model_validate(get_resp.json())


def test_update_user(app_url, make_user, user_factory):
    user = make_user.create(user_factory.user())
    user_id = user["id"]

    update_payload = user_factory.user()

    resp = requests.patch(f"{app_url}/api/users/{user_id}", json=update_payload)
    assert resp.status_code == HTTPStatus.OK
    assert {k: v for k, v in resp.json().items() if k != "id"} == update_payload


def test_delete_user(app_url, make_user, user_factory):
    user = make_user.create(user_factory.user())
    user_id = user["id"]

    del_resp = requests.delete(f"{app_url}/api/users/{user_id}")
    assert del_resp.status_code == HTTPStatus.OK
    assert del_resp.json()["message"] == "User deleted"

    get_resp = requests.get(f"{app_url}/api/users/{user['id']}")
    assert get_resp.status_code == HTTPStatus.NOT_FOUND


def test_delete_user_not_found(app_url, make_user, user_factory):
    user = make_user.create(user_factory.user())
    user_id = user["id"]

    requests.delete(f"{app_url}/api/users/{user_id}")

    del_resp = requests.delete(f"{app_url}/api/users/{user_id}")
    assert del_resp.status_code == HTTPStatus.NOT_FOUND
    assert del_resp.json()["detail"] == f"User with id={user_id} not found"


@pytest.mark.parametrize(("method", "url"), [
    ("post", "/api/users/123"),
    ("delete", "/api/users/"),
    ("patch", "/api/users/"),
])
def test_method_not_allowed(app_url, method, url):
    func = getattr(requests, method)
    resp = func(f"{app_url}{url}")
    assert resp.status_code == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.parametrize("bad_id", [-1, 0])
def test_delete_user_invalid_id(app_url, bad_id):
    resp = requests.delete(f"{app_url}/api/users/{bad_id}")
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("bad_id", [-1, 0])
def test_update_user_invalid_id(app_url, user_factory, bad_id):
    payload = user_factory.user()
    resp = requests.patch(f"{app_url}/api/users/{bad_id}", json=payload)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_update_user_not_found(app_url, user_factory):
    payload = user_factory.user()
    resp = requests.patch(f"{app_url}/api/users/99999999", json=payload)
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize("missing", [
    ("email",), ("first_name",), ("last_name",), ("avatar",),
    ("email", "avatar"),
    ("email", "avatar", "first_name", "last_name")
])
def test_create_user_missing_fields(app_url, user_factory, missing):
    payload = user_factory.without(*missing)
    resp = requests.post(f"{app_url}/api/users/", json=payload)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_user_flow_create_read_update_delete(app_url, user_factory):
    create_resp = requests.post(f"{app_url}/api/users/", json=user_factory.user())
    assert create_resp.status_code == HTTPStatus.CREATED
    user = create_resp.json()
    user_id = user["id"]

    get_resp = requests.get(f"{app_url}/api/users/{user_id}")
    assert get_resp.status_code == HTTPStatus.OK
    User.model_validate(get_resp.json())

    update_payload = user_factory.user()
    patch_resp = requests.patch(f"{app_url}/api/users/{user_id}", json=update_payload)
    assert patch_resp.status_code == HTTPStatus.OK
    assert {k: v for k, v in patch_resp.json().items() if k != "id"} == update_payload

    del_resp = requests.delete(f"{app_url}/api/users/{user_id}")
    assert del_resp.status_code == HTTPStatus.OK
    assert del_resp.json()["message"] == "User deleted"

    confirm = requests.get(f"{app_url}/api/users/{user_id}")
    assert confirm.status_code == HTTPStatus.NOT_FOUND

@pytest.mark.parametrize("make_payload", ["with_bad_email", "with_bad_url"])
def test_create_user_bad_email_or_url(app_url, user_factory, make_payload):
    bad_payload = getattr(user_factory, make_payload)()
    resp = requests.post(f"{app_url}/api/users/", json=bad_payload)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
