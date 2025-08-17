from uuid import uuid4
from dataclasses import dataclass

@dataclass
class UserFactory:
    domain: str = "example.com"
    counter: int = 0
    first_name_base: str = "Test"
    last_name_base: str = "User"

    def _next(self) -> int:
        self.counter += 1
        return self.counter

    def user(self, **overrides) -> dict:
        n = self._next()
        base = {
            "email": f"user{n}-{uuid4().hex[:6]}@{self.domain}",
            "first_name": f"{self.first_name_base}{n}",
            "last_name": f"{self.last_name_base}{n}",
            "avatar": f"https://cdn.{self.domain}/avatars/{uuid4().hex[:12]}.png",
        }
        base.update(overrides)
        return base

    def without(self, *fields) -> dict:
        data = self.user()
        for f in fields:
            data.pop(f, None)
        return data

    def with_bad_email(self) -> dict:
        return self.user(email="not-an-email")

    def with_bad_url(self) -> dict:
        return self.user(avatar="htp:/bad_url")
