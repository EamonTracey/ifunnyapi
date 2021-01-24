"""Representations of iFunny auth tokens using requests.auth.AuthBase"""

from requests.auth import AuthBase


class AuthBasic(AuthBase):
    """Bearer authorization object."""

    def __init__(self, token):
        self.token = token

    def __call__(self, req):
        req.headers["Authorization"] = "Basic " + self.token
        return req


class AuthBearer(AuthBase):
    """Bearer authorization object."""

    def __init__(self, token):
        self.token = token

    def __call__(self, req):
        req.headers["Authorization"] = "Bearer " + self.token
        return req
