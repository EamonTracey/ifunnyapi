class IFAPIException(Exception):
    """Base ifunnyapi exception class."""


class APIError(IFAPIException):
    """Raised when an API request retrieves an error"""

    def __init__(self, status: int, desc: str):
        super(APIError, self).__init__()
        self.status = status
        self.desc = desc

    def __str__(self):
        return f"status {self.status}, {self.desc}"
