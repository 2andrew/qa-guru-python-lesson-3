from http import HTTPStatus
import requests

class UserGenerator:
    def __init__(self, app_url: str):
        self.app_url = app_url
        self._created_ids: list[int] = []

    def create(self, payload: dict) -> dict:
        resp = requests.post(f"{self.app_url}/api/users/", json=payload)
        assert resp.status_code == HTTPStatus.CREATED
        user = resp.json()
        self._created_ids.append(user["id"])
        return user

    def delete(self, user_id: int) -> None:
        try:
            requests.delete(f"{self.app_url}/api/users/{user_id}")
        finally:
            if user_id in self._created_ids:
                self._created_ids.remove(user_id)

    def cleanup(self) -> None:
        while self._created_ids:
            uid = self._created_ids.pop()
            try:
                requests.delete(f"{self.app_url}/api/users/{uid}")
            except Exception:
                pass
