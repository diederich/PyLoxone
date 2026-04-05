"""Component to create an interface to the Loxone Miniserver.

For more details about this component, please refer to the documentation at
https://github.com/JoDehli/pyloxone-api
"""

import asyncio
import logging

import aiohttp

from .const import TIMEOUT
from .exceptions import (
    LoxoneMaxNumOfConnectionsError,
    LoxoneServiceUnAvailableError,
    LoxoneUnauthorisedError,
    LoxoneUnrecognizedCommandError,
)

_LOGGER = logging.getLogger(__name__)


class LoxoneAsyncHttpClient:
    """Represent loxone async http client."""

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        scheme: str = "http",
        session: aiohttp.ClientSession = None,
    ):
        # Validate input parameters
        """Initialize the LoxoneAsyncHttpClient."""
        if not url:
            raise ValueError("URL cannot be empty")
        if not username:
            raise ValueError("Username cannot be empty")
        if not password:
            raise ValueError("Password cannot be empty")
        if scheme not in ("http", "https"):
            raise ValueError(f"Invalid scheme '{scheme}'. Must be 'http' or 'https'")

        if session is None:
            self.session = aiohttp.ClientSession()
            self._own_session = True
        else:
            if session.closed:
                raise ValueError("Provided session is already closed")
            self.session = session
            self._own_session = False

        self.timeout = TIMEOUT
        self.base_url = f"{scheme}://{url}"
        self.username = username
        self.password = password
        self._closed = False

    async def get(self, endpoint):
        """Get."""
        if self._closed:
            raise RuntimeError("HTTP client has been closed")

        if not endpoint:
            raise ValueError("Endpoint cannot be empty")

        if not endpoint.startswith("/"):
            _LOGGER.warning("Endpoint '%s' should start with '/'", endpoint)
            endpoint = f"/{endpoint}"

        url = f"{self.base_url}{endpoint}"
        response = None

        try:
            _LOGGER.debug("Making GET request to: %s", url)
            response = await self.session.get(
                url,
                auth=aiohttp.BasicAuth(self.username, self.password),
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )

            if response.status != 200:
                await self._handle_error(response)

        except aiohttp.ClientConnectionError as err:
            _LOGGER.error("Connection error to %s: %s", url, err)
            raise ConnectionError(f"Failed to connect to Loxone Miniserver at {url}: {err}") from err

        except aiohttp.ClientConnectorError as err:
            _LOGGER.error("Connector error to %s: %s", url, err)
            raise ConnectionError(f"Cannot resolve or connect to {url}: {err}") from err

        except TimeoutError as err:
            _LOGGER.error("Timeout error for %s", url)
            raise TimeoutError(f"Request to {url} timed out after {self.timeout} seconds") from err

        except aiohttp.ClientSSLError as err:
            _LOGGER.error("SSL error for %s: %s", url, err)
            raise ConnectionError(f"SSL/TLS error connecting to {url}: {err}") from err

        except aiohttp.ClientProxyConnectionError as err:
            _LOGGER.error("Proxy connection error for %s: %s", url, err)
            raise ConnectionError(f"Proxy connection error: {err}") from err

        except aiohttp.ServerDisconnectedError as err:
            _LOGGER.error("Server disconnected for %s: %s", url, err)
            raise ConnectionError(f"Server disconnected unexpectedly: {err}") from err

        except aiohttp.ClientPayloadError as err:
            _LOGGER.error("Payload error for %s: %s", url, err)
            raise ValueError(f"Invalid response payload from server: {err}") from err

        except aiohttp.ClientResponseError as err:
            _LOGGER.error("Response error for %s: %s", url, err)
            raise RuntimeError(f"HTTP response error: {err}") from err

        except aiohttp.ClientError as err:
            _LOGGER.error("Client error for %s: %s", url, err)
            raise RuntimeError(f"HTTP client error: {err}") from err

        except (
            LoxoneUnauthorisedError,
            LoxoneUnrecognizedCommandError,
            LoxoneServiceUnAvailableError,
            LoxoneMaxNumOfConnectionsError,
        ):
            # Re-raise Loxone-specific errors without wrapping
            raise

        except Exception as err:
            _LOGGER.exception("Unexpected error during GET request to %s", url)
            raise RuntimeError(f"Unexpected error during HTTP request: {err}") from err
        else:
            return response

    async def close(self):
        """Close."""
        if self._closed:
            _LOGGER.warning("HTTP client is already closed")
            return

        try:
            if self._own_session and not self.session.closed:
                await self.session.close()
            self._closed = True
            _LOGGER.debug("HTTP client closed successfully")
        except OSError as err:
            _LOGGER.error("Error closing HTTP client: %s", err)
            self._closed = True
            raise RuntimeError(f"Failed to close HTTP session: {err}") from err

    @staticmethod
    async def _handle_error(response):
        """Return handle error."""
        content = None

        try:
            # Try to read content with timeout protection
            try:
                content = await asyncio.wait_for(response.content.read(), timeout=5.0)
                content = content.decode("utf-8", errors="replace")
            except TimeoutError:
                _LOGGER.warning("Timeout reading error response content")
                content = "<timeout reading response>"
            except UnicodeDecodeError as err:
                _LOGGER.warning("Failed to decode response content: %s", err)
                content = "<binary content>"
            except Exception as err:  # noqa: BLE001 — chardet/content read may raise anything
                _LOGGER.warning("Error reading response content: %s", err)
                content = f"<error reading content: {err}>"

        except Exception as err:  # noqa: BLE001 — outer guard for _handle_error
            _LOGGER.error("Critical error handling response: %s", err)
            content = "<unavailable>"

        # Handle specific HTTP status codes
        if response.status == 400:
            _LOGGER.error("Bad Request (400): %s", content)
            raise ValueError(f"Bad request to Loxone Miniserver: {content}")

        if response.status == 401:
            _LOGGER.error("Unauthorized (401): %s", content)
            err = LoxoneUnauthorisedError(f"Unauthorized: {content}")
            err.response = response
            raise err

        if response.status == 403:
            _LOGGER.error("Forbidden (403): %s", content)
            raise PermissionError(f"Access forbidden: {content}")

        if response.status == 404:
            _LOGGER.error("Not Found (404): %s", content)
            err = LoxoneUnrecognizedCommandError(f"Unrecognized command: {content}")
            err.response = response
            raise err

        if response.status == 408:
            _LOGGER.error("Request Timeout (408): %s", content)
            raise TimeoutError(f"Request timeout: {content}")

        if response.status == 429:
            _LOGGER.error("Too Many Requests (429): %s", content)
            raise RuntimeError(f"Rate limit exceeded: {content}")

        if response.status == 500:
            _LOGGER.error("Internal Server Error (500): %s", content)
            raise RuntimeError(f"Miniserver internal error: {content}")

        if response.status == 502:
            _LOGGER.error("Bad Gateway (502): %s", content)
            raise ConnectionError(f"Bad gateway: {content}")

        if response.status == 503:
            _LOGGER.error("Service Unavailable (503): %s", content)
            err = LoxoneServiceUnAvailableError(
                f"Service Unavailable; The Miniserver is restarting and not ready for requests: {content}"
            )
            err.response = response
            raise err

        if response.status == 504:
            _LOGGER.error("Gateway Timeout (504): %s", content)
            raise TimeoutError(f"Gateway timeout: {content}")

        if response.status == 901:
            _LOGGER.error("Max Connections (901): %s", content)
            err = LoxoneMaxNumOfConnectionsError(f"Maximum number of allowed concurrent connections reached: {content}")
            err.response = response
            raise err

        # Generic error for any other status code
        _LOGGER.error("HTTP Error %s: %s", response.status, content)
        raise RuntimeError(f"HTTP error {response.status}: {content}")
