import logging
from http import HTTPStatus
from typing import Any

import curlify
import requests
from requests import Session


class BaseSession(Session):
    def __init__(self, **kwargs):
        super().__init__()
        self.base_url = kwargs.get('base_url', None)

    def request(self, method: str,
                path: str,
                **kwargs: Any
                ):
        resp = super().request(method, path, **kwargs)
        logging.info(curlify.to_curl(resp.request))
        return resp

    def get(self, path="", expected_status=HTTPStatus.OK, **kwargs: Any):
        resp = requests.get(f"{self.base_url}/{path}")
        assert resp.status_code == expected_status
        return resp

    def post(self, path="", expected_status=HTTPStatus.CREATED, **kwargs: Any):
        resp = requests.post(f"{self.base_url}/{path}", json=kwargs["json"])
        assert resp.status_code == expected_status
        return resp

    def put(self, path="", expected_status=HTTPStatus.OK, **kwargs: Any):
        resp = requests.put(f"{self.base_url}/{path}", json=kwargs["json"])
        assert resp.status_code == expected_status
        return resp

    def patch(self, path="", expected_status=HTTPStatus.OK, **kwargs: Any):
        resp = requests.patch(f"{self.base_url}/{path}", json=kwargs["json"])
        assert resp.status_code == expected_status
        return resp

    def delete(self, path="", expected_status=HTTPStatus.OK, **kwargs: Any):
        resp = requests.delete(f"{self.base_url}/{path}")
        assert resp.status_code == expected_status
        return resp
