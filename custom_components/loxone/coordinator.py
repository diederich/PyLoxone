import asyncio
import enum
import logging

import websockets
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (CONF_HOST, CONF_PASSWORD, CONF_PORT,
                                 CONF_USERNAME)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.dispatcher import async_dispatcher_send
import homeassistant.helpers.issue_registry as ir

from .miniserver import MiniServer
from .pyloxone_api.connection import LoxoneConnection, LoxoneException
from .pyloxone_api.exceptions import (LoxoneConnectionClosedOk,
                                      LoxoneConnectionError,
                                      LoxoneOutOfServiceException,
                                      LoxoneTokenError)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_RECONNECT_MIN_DELAY = 1.0
_RECONNECT_MAX_DELAY = 300.0


class ConnectionState(enum.Enum):
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISCONNECTED = "disconnected"


class LoxoneCoordinator(DataUpdateCoordinator):
    """Manages the Loxone Miniserver connection lifecycle.

    On disconnect, reconnects in-process with exponential backoff instead of
    tearing down and reloading the entire integration.  Entities survive the
    reconnect and toggle ``available`` via ``last_update_success``.
    """

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="PyLoxone Coordinator",
            update_method=None,
        )
        self.config_entry = config_entry
        self._username = config_entry.options[CONF_USERNAME]
        self._password = config_entry.options[CONF_PASSWORD]
        self._host = config_entry.options[CONF_HOST]
        self._port = config_entry.options[CONF_PORT]

        self.api: LoxoneConnection | None = None
        self.miniserver: MiniServer | None = None
        self.listeners = []
        self._listening_task: asyncio.Task | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._shutting_down = False
        self.connection_state = ConnectionState.DISCONNECTED

    # -- Bootstrap / first connect ---------------------------------------------

    def _create_api(self) -> LoxoneConnection:
        """Create a fresh LoxoneConnection from the current config entry."""
        kwargs: dict = dict(
            host=self._host,
            port=self._port,
            username=self._username,
            password=self._password,
        )
        if "token" in self.config_entry.data:
            kwargs["token"] = self.config_entry.data
        self.api = LoxoneConnection(**kwargs)
        return self.api

    async def async_config_entry_first_refresh(self) -> None:
        _LOGGER.debug("async_config_entry_first_refresh")
        if self.api and self.api.connection:
            await self.api.close()
            self.api.connection = None

        self._create_api()
        try:
            session = async_get_clientsession(self.hass)
            self.api.connection = await self.api.open(session)
        except LoxoneException as e:
            _LOGGER.error("Could not connect to Loxone Miniserver")
            raise e
        except Exception as e:
            _LOGGER.error("Could not connect to Loxone Miniserver")
            raise e

        self.miniserver = MiniServer(
            self.hass, self.api.structure_file, self.config_entry
        )
        await self.miniserver.async_update_device_registry()
        self.connection_state = ConnectionState.CONNECTED
        self.last_update_success = True

    async def _async_update_data(self) -> None:
        _LOGGER.debug("_async_update_data")
        return None

    # -- Connection lifecycle --------------------------------------------------

    async def _message_callback(self, message):
        """Dispatch state updates per-UUID for O(1) entity routing."""
        _LOGGER.debug(f"{message}")
        for uuid in message:
            async_dispatcher_send(
                self.hass, f"loxone_uuid_{uuid}", message
            )

    def _handle_task_result(self, task: asyncio.Task) -> None:
        """Done-callback for the listening task — triggers reconnect on error."""
        if self._shutting_down:
            if not task.cancelled():
                task.exception()
            return

        clear_token = False
        try:
            task.result()
            return
        except LoxoneTokenError:
            _LOGGER.warning(
                "Token is no longer valid. Will re-authenticate on reconnect."
            )
            clear_token = True
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "token_expired",
                is_fixable=False,
                is_persistent=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="token_expired",
            )
        except LoxoneOutOfServiceException:
            _LOGGER.warning("Miniserver reports out of service. Will reconnect.")
        except LoxoneConnectionError:
            _LOGGER.warning("Connection error. Will reconnect.")
        except (
            LoxoneConnectionClosedOk,
            websockets.exceptions.ConnectionClosedOK,
        ):
            _LOGGER.warning("WebSocket connection closed. Will reconnect.")
        except asyncio.CancelledError:
            _LOGGER.debug("Listening task cancelled — not reconnecting")
            return
        except Exception:
            _LOGGER.exception("Unexpected error in listening task")

        self.connection_state = ConnectionState.DISCONNECTED
        self.async_set_update_error(
            LoxoneConnectionError("Disconnected from Miniserver")
        )

        if self._reconnect_task and not self._reconnect_task.done():
            _LOGGER.debug("Reconnect already in progress, skipping")
            return

        self._reconnect_task = self.hass.async_create_task(
            self._async_reconnect(clear_token=clear_token)
        )

    async def _async_reconnect(self, clear_token: bool = False) -> None:
        """Reconnect to the Miniserver with exponential backoff."""
        self.connection_state = ConnectionState.RECONNECTING
        _attempts = 0

        if clear_token:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={
                    **self.config_entry.data,
                    "token": "", "hash_alg": "", "valid_until": "",
                },
            )

        if self.api:
            try:
                await self.api.close()
            except Exception:
                _LOGGER.debug("Error closing old connection", exc_info=True)

        delay = _RECONNECT_MIN_DELAY
        while not self._shutting_down:
            _LOGGER.info(
                "Reconnecting to Miniserver at %s in %.0fs...",
                self._host, delay,
            )
            await asyncio.sleep(delay)

            if self._shutting_down:
                break

            try:
                self._create_api()
                session = async_get_clientsession(self.hass)
                self.api.connection = await self.api.open(session)

                self.miniserver = MiniServer(
                    self.hass, self.api.structure_file, self.config_entry
                )
                await self.miniserver.async_update_device_registry()

                await self.async_start_listening()

                self.connection_state = ConnectionState.CONNECTED
                self.async_set_updated_data({"connected": True})
                ir.async_delete_issue(self.hass, DOMAIN, "token_expired")
                ir.async_delete_issue(self.hass, DOMAIN, "persistent_disconnect")
                _LOGGER.info("Reconnected to Miniserver at %s", self._host)
                return
            except asyncio.CancelledError:
                raise
            except Exception as err:
                _attempts += 1
                delay = min(delay * 2, _RECONNECT_MAX_DELAY)
                _LOGGER.warning(
                    "Reconnect to %s failed (%d): %s. Next attempt in %.0fs",
                    self._host, _attempts, err, delay,
                )
                if _attempts == 3:
                    ir.async_create_issue(
                        self.hass,
                        DOMAIN,
                        "persistent_disconnect",
                        is_fixable=False,
                        is_persistent=False,
                        severity=ir.IssueSeverity.ERROR,
                        translation_key="persistent_disconnect",
                        translation_placeholders={"host": self._host},
                    )
                if self.api:
                    try:
                        await self.api.close()
                    except Exception:
                        pass

    async def async_send_command(self, uuid: str, value) -> None:
        """Send a command, dropping silently if not connected."""
        if self.connection_state != ConnectionState.CONNECTED:
            _LOGGER.warning(
                "Dropping command for %s — Miniserver is %s",
                uuid, self.connection_state.value,
            )
            return
        await self.api.send_websocket_command(uuid, value)

    async def async_send_secured_command(
        self, uuid: str, value, code
    ) -> None:
        """Send a secured command, dropping silently if not connected."""
        if self.connection_state != ConnectionState.CONNECTED:
            _LOGGER.warning(
                "Dropping secured command for %s — Miniserver is %s",
                uuid, self.connection_state.value,
            )
            return
        await self.api.send_secured__websocket_command(uuid, value, code)

    async def async_start_listening(self) -> None:
        """Start the WebSocket listening task."""
        self._listening_task = asyncio.create_task(
            self.api.start_listening(callback=self._message_callback)
        )
        self._listening_task.add_done_callback(self._handle_task_result)

    async def async_save_token(self) -> None:
        """Persist the current token to the config entry."""
        token = self.api.get_token_dict()
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data={
                **self.config_entry.data,
                "token": token["token"],
                "hash_alg": token["hash_alg"],
                "valid_until": token["valid_until"],
            },
        )

    async def async_cleanup(self):
        """Cancel listening/reconnect tasks, remove listeners, close connection."""
        self._shutting_down = True

        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            except Exception:
                _LOGGER.debug("Error awaiting reconnect task during cleanup",
                              exc_info=True)
        self._reconnect_task = None

        if self._listening_task and not self._listening_task.done():
            self._listening_task.cancel()
            try:
                await self._listening_task
            except asyncio.CancelledError:
                pass
            except Exception:
                _LOGGER.debug("Error awaiting listening task during cleanup",
                              exc_info=True)
        self._listening_task = None

        for listener in self.listeners:
            if listener is not None:
                listener()
        self.listeners = []

        if self.api:
            try:
                await self.async_save_token()
            except Exception:
                _LOGGER.debug("Could not save token during cleanup",
                              exc_info=True)
            await self.api.close()
