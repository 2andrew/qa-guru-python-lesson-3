from http import HTTPStatus

from tests.utils.base_session import BaseSession


class UserGenerator:
    def __init__(self, user_client: BaseSession):
        self.user_client = user_client
        self._created_ids: list[int] = []

    def create(self, payload: dict) -> dict:
        resp = self.user_client.post(json=payload)
        assert resp.status_code == HTTPStatus.CREATED, f"{resp.status_code} {resp.text}"
        user = resp.json()
        self._created_ids.append(user["id"])
        return user

    def delete(self, user_id: int) -> None:
        try:
            self.user_client.delete(f"{user_id}")
        finally:
            if user_id in self._created_ids:
                self._created_ids.remove(user_id)

    def cleanup(self) -> None:
        while self._created_ids:
            uid = self._created_ids.pop()
            try:
                self.user_client.delete(f"{uid}")
            except Exception:
                pass
