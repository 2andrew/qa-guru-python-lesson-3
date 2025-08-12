from http import HTTPStatus
from math import ceil

import pytest
import requests

from models.User import User


@pytest.fixture
def users(app_url):
    response = requests.get(f"{app_url}/api/users/")
    assert response.status_code == HTTPStatus.OK
    return response.json()


def test_users(app_url):
    response = requests.get(f"{app_url}/api/users/")
    assert response.status_code == HTTPStatus.OK

    _users = response.json()["items"]
    for user in _users:
        User.model_validate(user)


def test_users_no_duplicates(users):
    users_ids = [user["id"] for user in users["items"]]
    assert len(users_ids) == len(set(users_ids))


@pytest.mark.parametrize("user_id", [1, 6, 12])
def test_user(app_url, user_id):
    response = requests.get(f"{app_url}/api/users/{user_id}")
    assert response.status_code == HTTPStatus.OK

    user = response.json()
    User.model_validate(user)


@pytest.mark.parametrize("user_id", [13])
def test_user_nonexistent_values(app_url, user_id):
    response = requests.get(f"{app_url}/api/users/{user_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize("user_id", [-1, 0, "fafaf"])
def test_user_invalid_values(app_url, user_id):
    response = requests.get(f"{app_url}/api/users/{user_id}")
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


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
