import json
from http import HTTPStatus
from math import ceil
from pathlib import Path

import pytest

from app.models.User import User
from tests.data_generators.UserMaker import UserGenerator


@pytest.fixture(scope="session")
def fill_test_data(user_client):
    root = Path(__file__).resolve().parent.parent
    data_path = root / "users.json"
    with data_path.open(encoding="utf-8") as f:
        test_data_users = json.load(f)
    api_users = []
    for user in test_data_users:
        response = user_client.post(json=user)
        api_users.append(response.json())

    user_ids = [user["id"] for user in api_users]

    yield user_ids

    for user_id in user_ids:
        user_client.delete(f"{user_id}")


@pytest.fixture
def users(user_client):
    response = user_client.get()
    return response.json()


@pytest.fixture
def make_user(user_client):
    gen = UserGenerator(user_client)
    yield gen
    gen.cleanup()


@pytest.mark.usefixtures("fill_test_data")
def test_users(user_client):
    response = user_client.get()

    _users = response.json()["items"]
    for user in _users:
        User.model_validate(user)


@pytest.mark.usefixtures("fill_test_data")
def test_users_no_duplicates(users):
    users_ids = [user["id"] for user in users["items"]]
    assert len(users_ids) == len(set(users_ids))


@pytest.mark.usefixtures("fill_test_data")
@pytest.mark.parametrize("idx", [0, 5, 11])
def test_user(user_client, fill_test_data, idx):
    user_id = fill_test_data[idx]
    response = user_client.get(f"{user_id}")

    user = response.json()
    User.model_validate(user)


@pytest.mark.usefixtures("fill_test_data")
def test_user_nonexistent_values(user_client, fill_test_data):
    user_id = max(fill_test_data) + 1
    user_client.get(f"{user_id}", expected_status=HTTPStatus.NOT_FOUND)


@pytest.mark.usefixtures("fill_test_data")
@pytest.mark.parametrize("user_id", [-1, 0, "fafaf"])
def test_user_invalid_values(user_client, user_id):
    user_client.get(f"{user_id}", expected_status=HTTPStatus.UNPROCESSABLE_ENTITY)


@pytest.mark.usefixtures("fill_test_data")
@pytest.mark.parametrize("page, size",
                         [(1, 1), (1, 3), (1, 12), (1, 100),
                          (3, 1), (3, 4), (4, 3), (7, 1), (7, 2),
                          (12, 1), (7, 8), (98, 99)])
def test_app_pagination(user_client, page, size, users):
    response = user_client.get(f"?page={page}&size={size}")

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


def test_create_user(user_client, user_factory, make_user):
    payload = user_factory.user()
    created = make_user.create(payload)
    User.model_validate(created)

    assert {k: v for k, v in created.items() if k != "id"} == payload

    get_resp = user_client.get(f"{created['id']}")
    User.model_validate(get_resp.json())


def test_update_user(user_client, make_user, user_factory):
    user = make_user.create(user_factory.user())
    user_id = user["id"]

    update_payload = user_factory.user()

    resp = user_client.patch(f"{user_id}", json=update_payload)
    assert {k: v for k, v in resp.json().items() if k != "id"} == update_payload


def test_delete_user(user_client, make_user, user_factory):
    user = make_user.create(user_factory.user())
    user_id = user["id"]

    del_resp = user_client.delete(f"{user_id}")
    assert del_resp.json()["message"] == "User deleted"

    user_client.get(f"{user['id']}", expected_status=HTTPStatus.NOT_FOUND)


def test_delete_user_not_found(user_client, make_user, user_factory):
    user = make_user.create(user_factory.user())
    user_id = user["id"]

    user_client.delete(f"{user_id}")

    del_resp = user_client.delete(f"{user_id}", expected_status=HTTPStatus.NOT_FOUND)
    assert del_resp.json()["detail"] == f"User with id={user_id} not found"


@pytest.mark.parametrize(("method", "url"), [
    ("post", "123"),
    ("delete", ""),
    ("patch", ""),
])
def test_method_not_allowed(user_client, method, url):
    func = getattr(user_client, method)
    func(path=f"{url}", json={}, expected_status=HTTPStatus.METHOD_NOT_ALLOWED)


@pytest.mark.parametrize("bad_id", [-1, 0])
def test_delete_user_invalid_id(user_client, bad_id):
    user_client.delete(f"{bad_id}", expected_status=HTTPStatus.UNPROCESSABLE_ENTITY)


@pytest.mark.parametrize("bad_id", [-1, 0])
def test_update_user_invalid_id(user_client, user_factory, bad_id):
    payload = user_factory.user()
    user_client.patch(f"{bad_id}", json=payload, expected_status=HTTPStatus.UNPROCESSABLE_ENTITY)


def test_update_user_not_found(user_client, user_factory):
    payload = user_factory.user()
    user_client.patch("99999999", json=payload, expected_status=HTTPStatus.NOT_FOUND)


@pytest.mark.parametrize("missing", [
    ("email",), ("first_name",), ("last_name",), ("avatar",),
    ("email", "avatar"),
    ("email", "avatar", "first_name", "last_name")
])
def test_create_user_missing_fields(user_client, user_factory, missing):
    payload = user_factory.without(*missing)
    user_client.post(json=payload, expected_status=HTTPStatus.UNPROCESSABLE_ENTITY)


def test_user_flow_create_read_update_delete(user_client, user_factory):
    create_resp = user_client.post(json=user_factory.user())
    user = create_resp.json()
    user_id = user["id"]

    get_resp = user_client.get(f"{user_id}")
    User.model_validate(get_resp.json())

    update_payload = user_factory.user()
    patch_resp = user_client.patch(f"{user_id}", json=update_payload)
    assert {k: v for k, v in patch_resp.json().items() if k != "id"} == update_payload

    del_resp = user_client.delete(f"{user_id}")
    assert del_resp.json()["message"] == "User deleted"

    user_client.get(f"{user_id}", expected_status=HTTPStatus.NOT_FOUND)


@pytest.mark.parametrize("make_payload", ["with_bad_email", "with_bad_url"])
def test_create_user_bad_email_or_url(user_client, user_factory, make_payload):
    bad_payload = getattr(user_factory, make_payload)()
    user_client.post(json=bad_payload, expected_status=HTTPStatus.UNPROCESSABLE_ENTITY)
