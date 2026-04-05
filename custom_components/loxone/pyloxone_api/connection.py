"""Loxone Miniserver WebSocket connection.

Orchestrates the connection lifecycle: HTTP setup, WebSocket transport,
key exchange, token auth, keep-alive, and message dispatch.  Crypto
operations are delegated to ``crypto.py``.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import json
import logging
from types import TracebackType
from typing import Any, NoReturn, Self
from urllib.parse import urlparse

from async_upnp_client import aiohttp
import websockets as wslib
import websockets.exceptions

from .const import (
    CMD_AUTH_WITH_TOKEN,
    CMD_ENABLE_UPDATES,
    CMD_GET_API_KEY,
    CMD_GET_KEY,
    CMD_GET_KEY_AND_SALT,
    CMD_GET_PUBLIC_KEY,
    CMD_GET_VISUAL_PASSWD,
    CMD_KEEP_ALIVE,
    CMD_KEY_EXCHANGE,
    CMD_REFRESH_TOKEN,
    CMD_REFRESH_TOKEN_JSON_WEB,
    CMD_REQUEST_TOKEN,
    CMD_REQUEST_TOKEN_JSON_WEB,
    DELAY_CHECK_TOKEN_REFRESH,
    KEEP_ALIVE_PERIOD,
    LOXAPPPATH,
    MAX_REFRESH_DELAY,
    MAX_WEBSOCKET_MESSAGE_SIZE,
    RECONNECT_DELAY,
    RECONNECT_TRIES,
    TIMEOUT,
    TOKEN_PERMISSION,
)
from .crypto import (
    decrypt_command,
    encrypt_command,
    generate_aes_key,
    generate_iv,
    generate_salt,
    hash_credentials,
    hash_secure_command,
    hash_token,
    make_session_key,
    new_salt_needed,
    parse_public_key,
    time_elapsed_in_seconds,
)
from .exceptions import (
    LoxoneConnectionClosedOk,
    LoxoneConnectionError,
    LoxoneException,
    LoxoneOutOfServiceException,
    LoxoneServiceUnAvailableError,
    LoxoneTokenError,
)
from .loxone_http_client import LoxoneAsyncHttpClient
from .loxone_token import LoxoneToken, LxJsonKeySalt
from .message import (
    BaseMessage,
    Keepalive,
    LLResponse,
    MessageType,
    TextMessage,
    check_and_decode_if_needed,
    parse_header,
    parse_message,
)
from .websocket_protocol import LoxoneClientConnection

_LOGGER = logging.getLogger(__name__)


def _require_api_value_dict(value: Any) -> dict[str, Any]:
    """Return require api value dict."""
    if not isinstance(value, dict):
        raise TypeError(f"Expected dict response, got {type(value)}")
    return value


def _require_http_ok(response: Any, *, what: str) -> None:
    """Return require http ok."""
    if response.status != 200:
        raise RuntimeError(f"{what}, status: {response.status}")


def _require_public_key_payload(pk: Any) -> None:
    """Return require public key payload."""
    if not pk:
        raise ValueError("Empty public key received")


def _ensure_connection_open(connection: LoxoneClientConnection) -> None:
    """Return ensure connection open."""
    if not connection or connection.state == connection.state.CLOSED:
        raise LoxoneConnectionError("Connection is closed")


def _raise_out_of_service() -> NoReturn:
    """Return raise out of service."""
    raise LoxoneOutOfServiceException


@dataclass
class MessageForQueue:
    """Represent message for queue."""

    command: str
    flag: bool


class LoxoneConnection:
    """Full Loxone Miniserver connection: HTTP bootstrap + WebSocket lifecycle."""

    _URL_FORMAT = "ws://{url}/ws/rfc6455"
    _SSL_URL_FORMAT = "wss://{url}/ws/rfc6455"

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        *,
        token: dict | None = None,
        port: int = 8080,
        timeout: float | None = None,
    ):
        """Initialize the LoxoneConnection."""
        if not host or not isinstance(host, str):
            raise ValueError("Host must be a non-empty string")
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError(f"Port must be an integer between 1 and 65535, got {port}")
        if timeout is not None and (not isinstance(timeout, (int, float)) or timeout < 0):
            raise ValueError(f"Timeout must be a non-negative number or None, got {timeout}")

        self.host = host
        self.username = username
        self.password = password
        self.token = token
        self.port = port
        self.timeout = None if timeout == 0 else timeout
        self.connection: wslib.ClientConnection | None = None
        self._pending_task: list[asyncio.Task] = []
        self._closed = False
        self._key_update_event: asyncio.Event | None = None
        self._shutdown_event = asyncio.Event()
        self._reconnect_event = asyncio.Event()

        # Parse host to extract scheme
        try:
            parsed = urlparse(host if "://" in host else f"//{host}", scheme="")
        except ValueError as e:
            raise ValueError(f"Invalid host format '{host}': {e}") from e
        self.scheme = parsed.scheme or ("https" if port == 443 else "http")
        netloc = parsed.hostname or parsed.path
        if not netloc:
            raise ValueError(f"Cannot parse hostname from '{host}'")

        default_port = 80 if self.scheme == "http" else 443
        used_port = port if port and port != default_port else None
        self.url = f"{netloc}:{used_port}{parsed.path}" if used_port else f"{netloc}{parsed.path}"

        # Crypto state
        self._iv = generate_iv()
        self._aes_key = generate_aes_key()
        self._public_key: str = ""
        self._session_key: bytes = b""

        # Server metadata
        self.miniserver_version: list[int] = []
        self.miniserver_serial: str = ""
        self.structure_file: dict = {}

        # Token state
        self._init_token(token)
        self._key: str = ""
        self._user_salt: str = ""
        self._hash_alg: str = ""

        # Salt state
        self._salt: str = ""
        self._salt_time_stamp: int = 0
        self._salt_used_count: int = 0

        self._visual_hash: LxJsonKeySalt | None = None
        self._message_queue: asyncio.Queue[MessageForQueue] = asyncio.Queue(maxsize=1000)
        self._secured_queue: asyncio.Queue = asyncio.Queue(maxsize=1)
        self.message_header = None
        self._background_tasks: set[asyncio.Task[Any]] = set()

    def _track_background_task(self, task: asyncio.Task[Any]) -> None:
        """Return track background task."""
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    def _init_token(self, token: dict | None) -> None:
        """Return init token."""
        try:
            if token and token.get("token") and token.get("valid_until") and token.get("hash_alg"):
                t = token
                if t["hash_alg"] in ("SHA1", "SHA256"):
                    self._token = LoxoneToken(
                        token=t["token"],
                        valid_until=t["valid_until"],
                        hash_alg=t["hash_alg"],
                        key="",
                        unsecure_password=t.get("unsecure_password", False),
                    )
                else:
                    _LOGGER.warning("Invalid hash_alg in stored token, resetting")
                    self._token = LoxoneToken()
            else:
                self._token = LoxoneToken()
        except (KeyError, TypeError, ValueError) as e:
            _LOGGER.error("Failed to initialize token: %s", e)
            self._token = LoxoneToken()

    # -- Properties ------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """Return whether is connected."""
        return (
            self.connection is not None
            and hasattr(self.connection, "protocol")
            and self.connection.protocol.state.name == "OPEN"
        )

    def get_token_dict(self) -> dict:
        """Return token dict."""
        try:
            return {
                "token": self._token.token,
                "valid_until": self._token.valid_until,
                "hash_alg": self._token.hash_alg,
                "unsecure_password": self._token.unsecure_password,
            }
        except AttributeError as e:
            _LOGGER.error("Token attributes missing: %s", e)
            return {}

    def reset_token(self) -> None:
        """Reset token."""
        self._token = LoxoneToken()
        _LOGGER.debug("Token reset successfully")

    # -- Crypto helpers (delegate to crypto module) ----------------------------

    def _encrypt_and_send_command(self, command: str) -> str:
        """Encrypt a command, rotating salt if needed."""
        self._salt_used_count += 1
        if new_salt_needed(self._salt_used_count, self._salt_time_stamp):
            old_salt = self._salt
            self._salt = generate_salt()
            self._salt_time_stamp = time_elapsed_in_seconds()
            self._salt_used_count = 0
            return encrypt_command(self._aes_key, self._iv, self._salt, command, old_salt)
        return encrypt_command(self._aes_key, self._iv, self._salt, command)

    def _hash_token(self) -> str | None:
        """Return hash token."""
        if not self._token or not self._token.token or not self._key:
            return None
        return hash_token(self._token.token, self._key, self._hash_alg)

    def _hash_credentials(self) -> str | None:
        """Return hash credentials."""
        return hash_credentials(self.username, self.password, self._user_salt, self._key, self._hash_alg)

    # -- Send commands ---------------------------------------------------------

    async def _send_text_command(self, command: str = "", encrypted: bool = False) -> None:
        """Return send text command."""
        _LOGGER.debug("Send text command: %s", command)
        if encrypted:
            command = self._encrypt_and_send_command(command)
        try:
            if not self.connection or not self.is_connected:
                _LOGGER.warning("Cannot send command — connection is not open")
            await self.connection.send([command])
        except websockets.ConnectionClosedOK:
            raise LoxoneConnectionClosedOk("Connection closed normally while sending command") from None
        except Exception as e:
            _LOGGER.error("Error while sending: %s", e)
            raise

    async def send_websocket_command(self, device_uuid: str, value: str | float) -> None:
        """Send websocket command."""
        if not device_uuid or not isinstance(device_uuid, str):
            raise ValueError("device_uuid must be a non-empty string")
        command = f"jdev/sps/io/{device_uuid}/{value}"
        _LOGGER.debug("Call send_websocket_command: %s", command)
        try:
            self._message_queue.put_nowait(MessageForQueue(command=command, flag=True))
        except asyncio.QueueFull:
            _LOGGER.error(
                "Message queue full (size: %d), dropping command for %s",
                self._message_queue.maxsize,
                device_uuid,
            )
            raise RuntimeError("Message queue is full, cannot send command") from None

    async def send_secured__websocket_command(self, device_uuid: str, value: str | float, code: str) -> None:
        """Send secured websocket command."""
        if not device_uuid or not isinstance(device_uuid, str):
            raise ValueError("device_uuid must be a non-empty string")
        if value is None or not isinstance(value, (str, int, float)):
            raise ValueError("value must be a string, int, or float")
        if not code or not isinstance(code, str):
            raise ValueError("code must be a non-empty string")

        command = f"{CMD_GET_VISUAL_PASSWD}{self.username}"
        _LOGGER.debug("Call send_secured__websocket_command: %s", command)
        try:
            self._secured_queue.put_nowait(self._send_secure(device_uuid, value, code))
            self._message_queue.put_nowait(MessageForQueue(command=command, flag=True))
        except asyncio.QueueFull:
            _LOGGER.error("Queue is full, dropping secured command")
            raise RuntimeError("Queue is full, cannot send secured command") from None

    async def _send_secure(self, device_uuid: str, value: Any, code: str) -> None:
        """Return send secure."""
        if self._visual_hash is None:
            _LOGGER.error("No visual hash available for secure command")
            return
        cmd = hash_secure_command(
            code,
            self._visual_hash.key,
            self._visual_hash.salt,
            self._visual_hash.hash_alg,
            device_uuid,
            str(value),
        )
        if cmd:
            await self._message_queue.put(MessageForQueue(cmd, True))

    # -- Context manager -------------------------------------------------------

    async def __aenter__(self) -> Self:
        """Return aenter."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Return aexit."""
        await self.close()

    # -- open() — HTTP bootstrap -----------------------------------------------

    async def open(self, session: aiohttp.ClientSession | None = None) -> LoxoneClientConnection:
        """Open."""
        if self._closed:
            raise RuntimeError("Cannot open a closed connection")

        connector = None
        try:
            connector = LoxoneAsyncHttpClient(
                url=self.url,
                username=self.username,
                password=self.password,
                scheme=self.scheme,
                session=session,
            )

            # Fetch API key with retries
            api_resp = None
            for attempt in range(RECONNECT_TRIES):
                try:
                    api_resp = await connector.get(CMD_GET_API_KEY)
                    break
                except (LoxoneServiceUnAvailableError, ConnectionError, OSError, TimeoutError) as e:
                    if attempt < RECONNECT_TRIES - 1:
                        _LOGGER.debug(
                            "Connection error (attempt %d/%d), retrying in %ds: %s",
                            attempt + 1,
                            RECONNECT_TRIES,
                            RECONNECT_DELAY,
                            e,
                        )
                        await asyncio.sleep(RECONNECT_DELAY)
                    else:
                        _LOGGER.exception("Max connection tries exceeded. Stopping.")
                        raise

            data = await asyncio.wait_for(api_resp.content.read(), timeout=self.timeout or TIMEOUT)
            _value = LLResponse(data).value
            value = _require_api_value_dict(json.loads(_value.replace("'", '"')))

            version_str = value.get("version")
            if version_str:
                try:
                    self.miniserver_version = [int(x) for x in version_str.split(".")]
                except (ValueError, AttributeError) as e:
                    _LOGGER.warning("Invalid version format '%s': %s", version_str, e)
                    self.miniserver_version = []

            self.miniserver_serial = value.get("snr", "")
            local = value.get("local", True)

            if not local:
                try:
                    connector.base_url = str(api_resp.url).replace(CMD_GET_API_KEY, "")
                    self.url = connector.base_url.replace("https://", "").replace("http://", "")
                except (TypeError, ValueError, AttributeError) as e:
                    _LOGGER.warning("Failed to update URL for remote access: %s", e)

            # Fetch structure file
            lox_app_data = await connector.get(LOXAPPPATH)
            _require_http_ok(lox_app_data, what="Failed to get structure file")

            data = await asyncio.wait_for(lox_app_data.content.read(), timeout=self.timeout or TIMEOUT)
            self.structure_file = json.loads(data)
            self.structure_file["softwareVersion"] = self.miniserver_version

            # Fetch public key
            pk_data = await connector.get(CMD_GET_PUBLIC_KEY)
            pk_data_text = await asyncio.wait_for(pk_data.content.read(), timeout=self.timeout or TIMEOUT)
            pk = LLResponse(pk_data_text).value
            _require_public_key_payload(pk)
            self._public_key = parse_public_key(pk)

        except LoxoneServiceUnAvailableError:
            raise
        except Exception:
            _LOGGER.exception("Failed to initialize connection")
            raise
        finally:
            if session is None and connector:
                try:
                    await connector.session.close()
                except OSError as e:
                    _LOGGER.warning("Error closing HTTP session: %s", e)

        # Build session key
        try:
            self._session_key = make_session_key(self._public_key, self._aes_key, self._iv)
        except (TypeError, ValueError) as exc:
            raise LoxoneException(f"Session key generation failed: {exc}") from exc

        # Generate first salt
        self._salt = generate_salt()
        self._salt_time_stamp = time_elapsed_in_seconds()
        self._salt_used_count = 0

        # Establish WebSocket
        params = {"url": self.url}
        if self.scheme == "https":
            base_url = self._SSL_URL_FORMAT.format(**params)
        else:
            base_url = self._URL_FORMAT.format(**params)

        try:
            connection = await asyncio.wait_for(
                wslib.connect(
                    base_url,
                    open_timeout=self.timeout or TIMEOUT,
                    create_connection=LoxoneClientConnection,
                    compression=None,
                    max_size=MAX_WEBSOCKET_MESSAGE_SIZE,
                ),
                timeout=(self.timeout or TIMEOUT) * 2,
            )
        except TimeoutError:
            raise TimeoutError(f"Timeout connecting to websocket at {base_url}") from None
        except websockets.exceptions.WebSocketException as e:
            raise LoxoneConnectionError(f"Websocket connection failed: {e}") from e
        except OSError as e:
            raise ConnectionError(f"Network error connecting to {base_url}: {e}") from e

        _LOGGER.debug("Websocket connection established to %s", base_url)
        return connection

    # -- start_listening() — WebSocket lifecycle --------------------------------

    async def start_listening(
        self,
        callback: Callable[[Any], Awaitable[None] | None] | None = None,
    ) -> None:
        """Start listening."""
        if not self.connection:
            raise RuntimeError("No existing connection — call open(session) before start_listening()")
        _LOGGER.debug("Using existing connection.")

        self._shutdown_event.clear()

        # Send key exchange
        if not self._session_key:
            raise RuntimeError("Session key not initialized")
        await self.connection.send(f"{CMD_KEY_EXCHANGE}{self._session_key.decode()}")

        # Launch concurrent tasks
        self._pending_task = [
            asyncio.create_task(self._do_start_listening(callback, self.connection)),
            asyncio.create_task(self._process_message()),
            asyncio.create_task(self._keep_alive()),
            asyncio.create_task(self._check_and_refresh_token()),
            asyncio.create_task(self._reconnect_task()),
        ]

        try:
            done, _pending = await asyncio.wait(self._pending_task, return_when=asyncio.FIRST_EXCEPTION)
            for task in done:
                try:
                    await task
                except websockets.exceptions.ConnectionClosedOK:
                    raise LoxoneConnectionClosedOk from None
                except LoxoneTokenError:
                    raise
                except LoxoneOutOfServiceException:
                    raise
                except websockets.exceptions.ConnectionClosed:
                    raise LoxoneConnectionError("Connection closed") from None
                except asyncio.CancelledError:
                    pass
                except Exception:
                    raise
        except asyncio.CancelledError:
            _LOGGER.debug("Listening task cancelled")
            raise
        except (LoxoneConnectionError, LoxoneTokenError, LoxoneConnectionClosedOk):
            raise
        finally:
            for task in self._pending_task:
                if task and not task.done():
                    task.cancel()
            if self._pending_task:
                await asyncio.gather(*self._pending_task, return_exceptions=True)

    async def _keep_alive(self) -> NoReturn:
        """Return keep alive."""
        try:
            while True:
                await asyncio.sleep(KEEP_ALIVE_PERIOD)
                await self._send_text_command(CMD_KEEP_ALIVE, encrypted=False)
        except (LoxoneConnectionClosedOk, asyncio.CancelledError):
            raise
        except Exception as exc:
            _LOGGER.error("Keep-alive failed: %s", exc)
            raise

    async def _check_and_refresh_token(self) -> NoReturn:
        """Return check and refresh token."""
        _LOGGER.debug("Start check refresh token task...")
        await asyncio.sleep(DELAY_CHECK_TOKEN_REFRESH)
        while not self._shutdown_event.is_set():
            try:
                candidate = int(self._token.seconds_to_expire() * 0.5)
                seconds_to_refresh = max(1, min(candidate, MAX_REFRESH_DELAY))
                _LOGGER.debug("Token refresh in %ds", seconds_to_refresh)

                await asyncio.sleep(seconds_to_refresh)
                if self._shutdown_event.is_set():
                    break

                old_key = self._key
                key_updated_event = asyncio.Event()
                self._key_update_event = key_updated_event

                try:
                    self._track_background_task(
                        asyncio.create_task(self._send_text_command(CMD_GET_KEY, encrypted=False))
                    )
                    await asyncio.sleep(0)
                except (RuntimeError, OSError, ValueError) as exc:
                    _LOGGER.error("Error requesting new key: %s", exc)
                    self._key_update_event = None
                    await asyncio.sleep(1)
                    continue

                try:
                    await asyncio.wait_for(key_updated_event.wait(), timeout=15.0)
                    if self._key != old_key:
                        _LOGGER.debug("Key changed successfully.")
                        self._track_background_task(asyncio.create_task(self._refresh_token()))
                    else:
                        _LOGGER.warning("Key was not updated despite event being set")
                except TimeoutError:
                    _LOGGER.warning("Timed out waiting for new key (15s)")
                finally:
                    self._key_update_event = None

            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001 — continue token refresh loop after any failure
                _LOGGER.error("Error in token refresh cycle: %s", e)
                await asyncio.sleep(1)

    async def _refresh_token(self) -> None:
        """Return refresh token."""
        token_hash = self._hash_token()
        if token_hash is None:
            _LOGGER.error("Failed to hash token for refresh")
            return
        if self.miniserver_version < [10, 2]:
            command = f"{CMD_REFRESH_TOKEN}{token_hash}/{self.username}"
        else:
            command = f"{CMD_REFRESH_TOKEN_JSON_WEB}{token_hash}/{self.username}"
        await self._message_queue.put(MessageForQueue(command, True))

    async def _reconnect_task(self) -> None:
        """Return reconnect task."""
        while True:
            t_shutdown = asyncio.create_task(self._shutdown_event.wait())
            t_reconnect = asyncio.create_task(self._reconnect_event.wait())
            try:
                await asyncio.wait({t_shutdown, t_reconnect}, return_when=asyncio.FIRST_COMPLETED)
            finally:
                for t in (t_shutdown, t_reconnect):
                    if not t.done():
                        t.cancel()

            if self._shutdown_event.is_set():
                return
            if self._reconnect_event.is_set():
                self._reconnect_event.clear()
                raise LoxoneTokenError

    # -- Message processing ----------------------------------------------------

    async def _process_message(self) -> NoReturn:
        """Return process message."""
        _LOGGER.debug("Message processing task started")
        try:
            while not self._shutdown_event.is_set():
                try:
                    msg = await self._message_queue.get()
                    await asyncio.sleep(0)
                    try:
                        self._track_background_task(
                            asyncio.create_task(self._send_text_command(msg.command, encrypted=msg.flag))
                        )
                        await asyncio.sleep(0)
                    except (OSError, RuntimeError, ValueError) as e:
                        _LOGGER.error("Error sending message: %s", e)
                    finally:
                        self._message_queue.task_done()
                except asyncio.CancelledError:
                    raise
                except Exception as e:  # noqa: BLE001 — keep processor alive; log and backoff
                    _LOGGER.error("Error in message processing loop: %s", e)
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            while not self._message_queue.empty():
                try:
                    msg = self._message_queue.get_nowait()
                    try:
                        await self._send_text_command(msg.command, encrypted=msg.flag)
                    except Exception:  # noqa: BLE001 — best-effort drain on shutdown
                        pass
                    finally:
                        self._message_queue.task_done()
                except asyncio.QueueEmpty:
                    break
            raise

    # -- Listening loop --------------------------------------------------------

    async def _do_start_listening(
        self,
        callback: Callable[[Any], Awaitable[None] | None] | None,
        connection: LoxoneClientConnection,
    ) -> None:
        """Return do start listening."""
        callback_types = {
            MessageType.VALUE_STATES,
            MessageType.TEXT_STATES,
            MessageType.TEXT,
            MessageType.KEEPALIVE,
        }

        last_header = None

        async def _run_callback(msg: BaseMessage) -> None:
            try:
                await callback(msg.as_dict())
            except Exception:
                _LOGGER.exception("Callback error")

        try:
            async for message in connection:
                _ensure_connection_open(connection)

                message_length = len(message)

                if message_length == 8:
                    last_header = parse_header(message)
                    if last_header.message_type == MessageType.OUT_OF_SERVICE:
                        _raise_out_of_service()
                    if last_header.message_type == MessageType.KEEPALIVE:
                        self._track_background_task(asyncio.create_task(_run_callback(Keepalive(""))))

                elif last_header and last_header.payload_length == message_length:
                    msg_type = last_header.message_type

                    if msg_type == MessageType.TEXT:
                        message = check_and_decode_if_needed(message)

                    parsed_message = parse_message(message, msg_type)
                    self._track_background_task(asyncio.create_task(self._websocket_event(parsed_message)))

                    if callback and msg_type in callback_types:
                        self._track_background_task(asyncio.create_task(_run_callback(parsed_message)))
                else:
                    _LOGGER.error("Message not handled: %s", message)
        except asyncio.CancelledError:
            raise
        except (LoxoneTokenError, LoxoneOutOfServiceException, LoxoneConnectionError):
            raise
        except Exception:
            _LOGGER.exception("Unexpected error in listening loop")
            raise

    # -- Internal event dispatch -----------------------------------------------

    async def _websocket_event(self, message: dict[str, Any] | BaseMessage) -> None:
        """Return websocket event."""
        if message is None:
            return

        mess_obj: BaseMessage | None = None
        try:
            if isinstance(message, (str, bytes)):
                mess_obj = parse_message(
                    message,
                    self.message_header.message_type if self.message_header else None,
                )
            elif isinstance(message, BaseMessage):
                mess_obj = message
            else:
                return

            if mess_obj is None:
                return

            # Decrypt if needed
            if hasattr(mess_obj, "control") and mess_obj.control and "/enc/" in mess_obj.control:
                mess_obj.control = decrypt_command(self._aes_key, self._iv, mess_obj.control)

            if isinstance(mess_obj, TextMessage):
                await self._handle_text_event(mess_obj)

        except LoxoneTokenError:
            raise
        except Exception:
            _LOGGER.exception("Error in websocket event handler")

    async def _drain_secured_queue(self) -> None:
        """Run pending secured commands after visual hash / salt is ready."""
        while not self._secured_queue.empty():
            try:
                awaitable = self._secured_queue.get_nowait()
                if awaitable:
                    await awaitable
                self._secured_queue.task_done()
            except asyncio.QueueEmpty:
                break
            except (OSError, RuntimeError, ValueError) as e:
                _LOGGER.error("Error processing secured queue item: %s", e)

    async def _handle_text_event(self, msg: TextMessage) -> None:
        """Route a text protocol message to the appropriate handler."""
        m = msg.message

        if "keyexchange" in m:
            _LOGGER.debug("Key exchange with miniserver...")
            command = f"{CMD_GET_KEY_AND_SALT}/{self.username}"
            await self._message_queue.put(MessageForQueue(command, True))

        elif "getkey2" in m:
            _LOGGER.debug("Got getkey2")
            vd = msg.value_as_dict
            if not isinstance(vd, dict):
                return

            self._key = vd.get("key", "")
            self._user_salt = vd.get("salt", "")
            self._hash_alg = vd.get("hashAlg", "")

            if not self._key or not self._user_salt:
                _LOGGER.error("Missing key or salt in getkey2 response")
                return

            if self._token.seconds_to_expire() > 100:
                _LOGGER.debug("Using existing token...")
                token_hash = self._hash_token()
                if token_hash is None:
                    _LOGGER.error("Failed to hash existing token")
                    return
                command = f"{CMD_AUTH_WITH_TOKEN}{token_hash}/{self.username}"
                await self._message_queue.put(MessageForQueue(command, True))
            else:
                _LOGGER.debug("Acquiring new token...")
                new_hash = self._hash_credentials()
                if new_hash is None:
                    _LOGGER.error("Failed to hash credentials")
                    return
                if self.miniserver_version < [10, 2]:
                    command = f"{CMD_REQUEST_TOKEN}/{new_hash}/{self.username}/{TOKEN_PERMISSION}/edfc5f9a-df3f-4cad-9dddcdc42c732b82/pyloxone_api"
                else:
                    command = f"{CMD_REQUEST_TOKEN_JSON_WEB}/{new_hash}/{self.username}/{TOKEN_PERMISSION}/edfc5f9a-df3f-4cad-9dddcdc42c732b82/pyloxone_api"
                await self._message_queue.put(MessageForQueue(command, True))

        elif "getkey" in m:
            _LOGGER.debug("Got getkey")
            vd = msg.value_as_dict
            if isinstance(vd, dict):
                self._key = vd.get("value", "")
                if self._key_update_event is not None:
                    self._key_update_event.set()

        elif "getvisusalt" in m:
            vd = msg.value_as_dict
            if isinstance(vd, dict):
                self._key = vd.get("value", "")
            key_and_salt = LxJsonKeySalt()
            key_and_salt.read_user_salt_response(msg.message)
            key_and_salt.time_elapsed_in_seconds = time_elapsed_in_seconds()
            self._visual_hash = key_and_salt

            await self._drain_secured_queue()

        elif "gettoken" in m or "getjwt" in m:
            vd = msg.value_as_dict
            if not isinstance(vd, dict):
                return
            self._token.token = vd.get("token")
            self._token.valid_until = vd.get("validUntil", 0)
            self._token.key = vd.get("key", "")
            self._token.hash_alg = self._hash_alg
            if "unsecurePass" in vd:
                self._token.unsecure_password = vd.get("unsecurePass", False)
            if not self._token.token:
                _LOGGER.error("Received empty token")
                return
            await self._message_queue.put(MessageForQueue(CMD_ENABLE_UPDATES, True))

        elif "authwithtoken" in m:
            if msg.code == 401:
                _LOGGER.error("Token authentication failed (401)")
                self.reset_token()
                self._reconnect_event.set()
            else:
                _LOGGER.debug("Got message authwithtoken")
                await self._message_queue.put(MessageForQueue(CMD_ENABLE_UPDATES, True))

        elif "refreshjwt" in m or "refresh" in m:
            _LOGGER.debug("Got token refresh response")
            vd = msg.value_as_dict
            if not isinstance(vd, dict):
                return
            token = vd.get("token")
            valid_until = vd.get("validUntil")
            if not token or valid_until is None:
                _LOGGER.error("Invalid refresh response: %s", vd)
                return
            self._token.token = token
            self._token.valid_until = valid_until
            if "unsecurePass" in vd:
                self._token.unsecure_password = vd.get("unsecurePass", False)
            _LOGGER.debug("Token refreshed, valid until: %s", valid_until)

    # -- close() ---------------------------------------------------------------

    async def close(self) -> None:
        """Close."""
        if self._closed:
            return

        _LOGGER.debug("Closing connection...")
        self._closed = True
        self._shutdown_event.set()

        if self._message_queue and self._message_queue.qsize() > 0:
            try:
                await asyncio.wait_for(self._message_queue.join(), timeout=5.0)
            except TimeoutError:
                _LOGGER.warning("Timeout waiting for message queue to drain")

        if self._pending_task:
            for task in self._pending_task:
                if task and not task.done():
                    task.cancel()
            await asyncio.gather(*self._pending_task, return_exceptions=True)
            self._pending_task = []

        if self._background_tasks:
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks.clear()

        if self.connection:
            try:
                if self.connection.state != self.connection.state.CLOSED:
                    await asyncio.wait_for(self.connection.close(), timeout=5.0)
            except (TimeoutError, OSError, wslib.exceptions.WebSocketException) as e:
                _LOGGER.warning("Error closing websocket: %s", e)
            finally:
                self.connection = None

        _LOGGER.debug("Connection closed successfully.")
