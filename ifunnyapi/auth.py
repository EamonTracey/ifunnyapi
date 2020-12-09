from requests.auth import AuthBase


class AuthBearer(AuthBase):
    """Bearer authorization object."""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = "Bearer " + self.token
        return r
