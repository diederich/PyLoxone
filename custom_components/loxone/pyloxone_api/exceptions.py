"""Exception hierarchy for pyloxone_api."""


class LoxoneException(Exception):
    """Base class for all Loxone exceptions."""

    response = None


class LoxoneConnectionClosedOk(LoxoneException):
    """WebSocket closed normally."""


class LoxoneConnectionError(LoxoneException):
    """Network connection interrupted."""


class LoxoneOutOfServiceException(LoxoneException):
    """Miniserver is rebooting."""


class LoxoneHTTPStatusError(LoxoneException):
    """Unusual HTTP response from the Miniserver."""


class LoxoneRequestError(LoxoneException):
    """HTTP request error."""


class LoxoneUnauthorisedError(LoxoneRequestError):
    """Incorrect credentials (HTTP 401)."""


class LoxoneTokenError(LoxoneRequestError):
    """Token invalid or expired."""


class LoxoneCommandError(LoxoneException):
    """Command rejected by Miniserver."""

    def __init__(self, code: int, message: str) -> None:
        """Initialize the LoxoneCommandError."""
        self.code = code
        self.message = message

    def __str__(self) -> str:
        """Return str."""
        return f"{self.code}: {self.message}"


class LoxoneTimeOutError(LoxoneException):
    """Request timed out."""


class LoxoneServiceUnAvailableError(LoxoneRequestError):
    """Miniserver is restarting (HTTP 503)."""


class LoxoneMaxNumOfConnectionsError(LoxoneRequestError):
    """Max concurrent connections reached (HTTP 429)."""


class LoxoneUnrecognizedCommandError(LoxoneRequestError):
    """Unrecognized command (HTTP 400)."""


# Legacy aliases — kept for backward compatibility with external consumers.
ConnectionFailure = LoxoneConnectionError
UnauthorizedError = LoxoneUnauthorisedError
ResponseError = LoxoneRequestError
HttpApiError = LoxoneHTTPStatusError
MessageError = LoxoneException
