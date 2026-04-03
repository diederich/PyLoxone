import asyncio
import enum
import logging
from datetime import timedelta

import aiohttp
import websockets
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (CONF_HOST, CONF_PASSWORD, CONF_PORT,
                                 CONF_USERNAME)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.dispatcher import async_dispatcher_send
import homeassistant.helpers.issue_registry as ir

from .miniserver import MiniServer
from .pyloxone_api.connection import LoxoneConnection, LoxoneException
from .pyloxone_api.exceptions import (LoxoneConnectionClosedOk,
                                      LoxoneConnectionError,
                                      LoxoneOutOfServiceException,
                                      LoxoneTokenError,
                                      LoxoneUnauthorisedError)

from .const import CONF_STRUCTURE_POLL_INTERVAL, DEFAULT_STRUCTURE_POLL_INTERVAL, DOMAIN

STRUCTURE_DIFF_KEY = f"{DOMAIN}_structure_diff"

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
        self._structure_poll_unsub: CALLBACK_TYPE | None = None
        self._structure_last_modified: str | None = None
        self._shutting_down = False
        self.connection_state = ConnectionState.DISCONNECTED
        self.reconnect_count: int = 0

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
        self._structure_last_modified = self.api.structure_file.get(
            "lastModified"
        )
        self._snapshot_controls()
        self.connection_state = ConnectionState.CONNECTED
        self.last_update_success = True

    async def _async_update_data(self) -> None:
        _LOGGER.debug("_async_update_data")
        return None

    # -- Connection lifecycle --------------------------------------------------

    @property
    def dispatcher_prefix(self) -> str:
        """Signal prefix for this entry's UUID dispatches."""
        return f"loxone_{self.config_entry.entry_id}_uuid_"

    @property
    def monitor_signal(self) -> str:
        """Signal for the live monitor subscription."""
        return f"loxone_{self.config_entry.entry_id}_monitor"

    async def _message_callback(self, message):
        """Dispatch state updates per-UUID for O(1) entity routing."""
        _LOGGER.debug(f"{message}")
        prefix = self.dispatcher_prefix
        for uuid in message:
            async_dispatcher_send(self.hass, f"{prefix}{uuid}", message)
        async_dispatcher_send(self.hass, self.monitor_signal, message)

        self._fire_device_trigger_events(message)

    def _fire_device_trigger_events(self, message: dict) -> None:
        """Fire HA bus events for device triggers.

        Maps each UUID in the message to its device_id so device triggers
        can match.  The UUID-to-device_id mapping is built lazily.
        """
        from .device_trigger import EVENT_LOXONE_STATE_CHANGE
        from homeassistant.helpers import device_registry as dr

        dr_registry = dr.async_get(self.hass)
        for uuid in message:
            device = dr_registry.async_get_device(identifiers={(DOMAIN, uuid)})
            if device is None:
                continue
            self.hass.bus.async_fire(
                EVENT_LOXONE_STATE_CHANGE,
                {
                    "device_id": device.id,
                    "uuid": uuid,
                    "values": {
                        k: v for k, v in message.items() if k == uuid
                    },
                },
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
                self.reconnect_count += 1
                self.async_set_updated_data({"connected": True})
                _eid = self.config_entry.entry_id
                ir.async_delete_issue(self.hass, DOMAIN, f"token_expired_{_eid}")
                ir.async_delete_issue(self.hass, DOMAIN, f"persistent_disconnect_{_eid}")
                _LOGGER.info("Reconnected to Miniserver at %s", self._host)
                return
            except asyncio.CancelledError:
                raise
            except LoxoneUnauthorisedError:
                _LOGGER.error(
                    "Authentication failed — credentials may have changed"
                )
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    f"token_expired_{self.config_entry.entry_id}",
                    is_fixable=True,
                    is_persistent=True,
                    severity=ir.IssueSeverity.ERROR,
                    translation_key="token_expired",
                )
                self.config_entry.async_start_reauth(self.hass)
                return
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
                        f"persistent_disconnect_{self.config_entry.entry_id}",
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
        """Start the WebSocket listening task and structure poll."""
        self._listening_task = asyncio.create_task(
            self.api.start_listening(callback=self._message_callback)
        )
        self._listening_task.add_done_callback(self._handle_task_result)
        self._start_structure_poll()

    def _start_structure_poll(self) -> None:
        """Start periodic structure file change detection."""
        if self._structure_poll_unsub is not None:
            return
        interval = self.config_entry.options.get(
            CONF_STRUCTURE_POLL_INTERVAL, DEFAULT_STRUCTURE_POLL_INTERVAL
        )
        if interval <= 0:
            _LOGGER.debug("Structure polling disabled (interval=%s)", interval)
            return
        self._structure_poll_unsub = async_track_time_interval(
            self.hass,
            self._async_poll_structure,
            timedelta(seconds=interval),
        )

    async def _async_poll_structure(self, _now=None) -> None:
        """Called periodically to check for structure changes."""
        if self._shutting_down or self.connection_state != ConnectionState.CONNECTED:
            return
        try:
            await self._check_structure_change()
        except Exception:
            _LOGGER.debug("Structure poll failed", exc_info=True)

    async def _check_structure_change(self) -> None:
        """Query LoxAPPversion3 (lightweight) and reload if lastModified changed."""
        session = async_get_clientsession(self.hass)
        url = f"http://{self._host}:{self._port}/jdev/sps/LoxAPPversion3"
        try:
            async with asyncio.timeout(10):
                resp = await session.get(
                    url,
                    auth=aiohttp.BasicAuth(self._username, self._password),
                )
                if resp.status != 200:
                    _LOGGER.debug("Structure poll got HTTP %s", resp.status)
                    return
                data = await resp.json(content_type=None)
        except Exception as err:
            _LOGGER.debug("Structure poll fetch failed: %s", err)
            return

        # Response: {"LL": {"control": "...", "value": "<lastModified>", "code": "200"}}
        new_modified = None
        ll = data.get("LL") if isinstance(data, dict) else None
        if isinstance(ll, dict):
            new_modified = ll.get("value")
        if not new_modified:
            new_modified = data.get("lastModified")
        if (
            new_modified
            and self._structure_last_modified
            and new_modified != self._structure_last_modified
        ):
            _LOGGER.info(
                "Miniserver structure changed (%s → %s), reloading integration",
                self._structure_last_modified,
                new_modified,
            )
            self._compute_structure_diff()
            self._structure_last_modified = new_modified
            await self.hass.config_entries.async_reload(
                self.config_entry.entry_id
            )

    def _snapshot_controls(self) -> None:
        """Store a baseline of current controls for future diff comparisons."""
        structure = self.api.structure_file or {}
        controls = structure.get("controls", {})
        rooms = structure.get("rooms", {})

        summary = {}
        for uuid, ctrl in controls.items():
            room_uuid = ctrl.get("room", "")
            room_name = rooms.get(room_uuid, {}).get("name", "") if room_uuid else ""
            summary[uuid] = {
                "name": ctrl.get("name", ""),
                "type": ctrl.get("type", ""),
                "room": room_name,
            }

        diffs = self.hass.data.setdefault(STRUCTURE_DIFF_KEY, {})
        existing = diffs.get(self.config_entry.entry_id)
        if existing is None:
            diffs[self.config_entry.entry_id] = {
                "timestamp": None,
                "new_controls": summary,
                "added": {},
                "removed": {},
                "changed": {},
            }
        else:
            existing["new_controls"] = summary

    def _compute_structure_diff(self) -> None:
        """Snapshot current controls and compute diff against previous snapshot.

        Stores the result in ``hass.data[STRUCTURE_DIFF_KEY][entry_id]`` so it
        survives the config entry reload (which creates a new coordinator).
        """
        from homeassistant.util import dt as dt_util

        if self.api is None:
            return

        old_structure = self.api.structure_file or {}
        old_controls = old_structure.get("controls", {})
        old_rooms = old_structure.get("rooms", {})

        old_summary = {}
        for uuid, ctrl in old_controls.items():
            room_uuid = ctrl.get("room", "")
            room_name = old_rooms.get(room_uuid, {}).get("name", "") if room_uuid else ""
            old_summary[uuid] = {
                "name": ctrl.get("name", ""),
                "type": ctrl.get("type", ""),
                "room": room_name,
            }

        prev_diffs = self.hass.data.setdefault(STRUCTURE_DIFF_KEY, {})
        prev = prev_diffs.get(self.config_entry.entry_id)
        prev_summary = prev.get("new_controls", {}) if prev else {}

        if prev_summary:
            added = {k: old_summary[k] for k in old_summary if k not in prev_summary}
            removed = {k: prev_summary[k] for k in prev_summary if k not in old_summary}
            changed = {}
            for k in old_summary:
                if k in prev_summary and old_summary[k] != prev_summary[k]:
                    changed[k] = {"old": prev_summary[k], "new": old_summary[k]}
        else:
            added = {}
            removed = {}
            changed = {}

        prev_diffs[self.config_entry.entry_id] = {
            "timestamp": dt_util.utcnow().isoformat(),
            "new_controls": old_summary,
            "added": added,
            "removed": removed,
            "changed": changed,
        }

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
        """Cancel listening/reconnect/poll tasks, remove listeners, close connection."""
        self._shutting_down = True

        if self._structure_poll_unsub is not None:
            self._structure_poll_unsub()
            self._structure_poll_unsub = None

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
