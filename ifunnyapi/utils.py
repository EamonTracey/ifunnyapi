from functools import wraps
from .exceptions import APIError


def api_request(func):
    """iFunny API request function decorator."""

    @wraps(func)
    def decorated(*args, **kwargs):
        retv = func(*args, **kwargs)
        if "error" in retv:
            raise APIError(retv["status"], retv["error_description"])
        return retv
    return decorated
