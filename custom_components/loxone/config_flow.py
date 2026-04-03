"""Config Flow for PyLoxone.

Supports initial setup with live connection test, reauth on credential
failure, and an options flow for settings + device bridges.
"""

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_CREATE_AREAS,
    CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN,
    CONF_SCENE_GEN,
    CONF_SCENE_GEN_DELAY,
    DEFAULT_DELAY_SCENE,
    DEFAULT_IP,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

_TEST_ENDPOINT = "/jdev/cfg/apiKey"
_SERIAL_ENDPOINT = "/jdev/cfg/mac"

_BRIDGEABLE_TOP_LEVEL = frozenset({"Switch", "Slider", "TextInput"})
_BRIDGEABLE_SUBCTRLS = frozenset({"Dimmer", "EIBDimmer", "Switch", "ColorPickerV2"})


def _setup_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the user/reauth data schema with optional suggested values."""
    d = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_USERNAME, default=d.get(CONF_USERNAME, "")
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Required(
                CONF_PASSWORD, default=d.get(CONF_PASSWORD, "")
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Required(
                CONF_HOST, default=d.get(CONF_HOST, DEFAULT_IP)
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Required(
                CONF_PORT, default=d.get(CONF_PORT, DEFAULT_PORT)
            ): NumberSelector(
                NumberSelectorConfig(mode=NumberSelectorMode.BOX, min=1, max=65535)
            ),
            vol.Required(
                CONF_SCENE_GEN, default=d.get(CONF_SCENE_GEN, True)
            ): BooleanSelector(),
            vol.Optional(
                CONF_SCENE_GEN_DELAY,
                default=d.get(CONF_SCENE_GEN_DELAY, DEFAULT_DELAY_SCENE),
            ): NumberSelector(
                NumberSelectorConfig(mode=NumberSelectorMode.BOX, min=3)
            ),
            vol.Required(
                CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN,
                default=d.get(CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN, False),
            ): BooleanSelector(),
            vol.Required(
                CONF_CREATE_AREAS, default=d.get(CONF_CREATE_AREAS, True)
            ): BooleanSelector(),
        }
    )


async def _async_validate_credentials(
    session: aiohttp.ClientSession,
    host: str,
    port: int,
    username: str,
    password: str,
) -> str | None:
    """Validate credentials against the Miniserver.

    Returns the Miniserver serial on success, None if serial cannot be fetched.
    Raises SchemaFlowError-style strings on failure.
    """
    try:
        username.encode("latin-1")
    except UnicodeEncodeError:
        raise ValueError("username_not_latin1")

    try:
        password.encode("latin-1")
    except UnicodeEncodeError:
        raise ValueError("password_not_latin1")

    url = f"http://{host}:{port}{_TEST_ENDPOINT}"
    try:
        async with asyncio.timeout(10):
            resp = await session.get(
                url, auth=aiohttp.BasicAuth(username, password)
            )
            if resp.status == 401:
                raise ValueError("invalid_auth")
            if resp.status not in (200, 301, 302):
                _LOGGER.warning(
                    "Miniserver returned HTTP %s for %s", resp.status, url
                )
                raise ValueError("cannot_connect")
    except ValueError:
        raise
    except (asyncio.TimeoutError, TimeoutError):
        raise ValueError("cannot_connect")
    except aiohttp.ClientError:
        raise ValueError("cannot_connect")
    except OSError:
        raise ValueError("cannot_connect")

    serial = await _async_fetch_serial(session, host, port, username, password)
    return serial


async def _async_fetch_serial(
    session: aiohttp.ClientSession,
    host: str,
    port: int,
    username: str,
    password: str,
) -> str | None:
    """Fetch the Miniserver serial (MAC) for use as unique_id."""
    url = f"http://{host}:{port}{_SERIAL_ENDPOINT}"
    try:
        async with asyncio.timeout(5):
            resp = await session.get(
                url, auth=aiohttp.BasicAuth(username, password)
            )
            if resp.status == 200:
                data = await resp.json(content_type=None)
                value = data.get("LL", {}).get("value", "")
                if isinstance(value, str) and value:
                    return value.replace(":", "").upper()
    except Exception:
        _LOGGER.debug("Could not fetch Miniserver serial", exc_info=True)
    return None


class LoxoneFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle Loxone config flow."""

    VERSION = 3

    def __init__(self) -> None:
        super().__init__()
        self._reauth_entry: ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        """Handle the initial configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if CONF_PORT in user_input:
                user_input[CONF_PORT] = int(user_input[CONF_PORT])
            if CONF_SCENE_GEN_DELAY in user_input:
                user_input[CONF_SCENE_GEN_DELAY] = int(
                    user_input[CONF_SCENE_GEN_DELAY]
                )

            session = async_get_clientsession(self.hass)
            try:
                serial = await _async_validate_credentials(
                    session,
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
            except ValueError as err:
                errors["base"] = str(err)
            else:
                if serial:
                    await self.async_set_unique_id(serial)
                    self._abort_if_unique_id_configured()

                title = f"PyLoxone ({user_input.get(CONF_HOST, 'Loxone')})"
                return self.async_create_entry(
                    title=title, data={}, options=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_setup_schema(),
            errors=errors,
        )

    # -- Reauth flow -----------------------------------------------------------

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> Any:
        """Handle reauth triggered by the coordinator on auth failure."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        """Show reauth form and validate new credentials."""
        errors: dict[str, str] = {}
        assert self._reauth_entry is not None

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            host = user_input.get(CONF_HOST, self._reauth_entry.options.get(CONF_HOST))
            port = int(
                user_input.get(CONF_PORT, self._reauth_entry.options.get(CONF_PORT))
            )
            try:
                await _async_validate_credentials(
                    session,
                    host,
                    port,
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
            except ValueError as err:
                errors["base"] = str(err)
            else:
                updated_options = {
                    **self._reauth_entry.options,
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                }
                if CONF_HOST in user_input:
                    updated_options[CONF_HOST] = user_input[CONF_HOST]
                if CONF_PORT in user_input:
                    updated_options[CONF_PORT] = int(user_input[CONF_PORT])

                self.hass.config_entries.async_update_entry(
                    self._reauth_entry, options=updated_options
                )
                await self.hass.config_entries.async_reload(
                    self._reauth_entry.entry_id
                )
                return self.async_abort(reason="reauth_successful")

        defaults = {
            CONF_USERNAME: self._reauth_entry.options.get(CONF_USERNAME, ""),
            CONF_PASSWORD: "",
            CONF_HOST: self._reauth_entry.options.get(CONF_HOST, ""),
            CONF_PORT: self._reauth_entry.options.get(CONF_PORT, DEFAULT_PORT),
        }
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_USERNAME, default=defaults[CONF_USERNAME]
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Required(CONF_PASSWORD, default=""): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Required(
                    CONF_HOST, default=defaults[CONF_HOST]
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Required(
                    CONF_PORT, default=defaults[CONF_PORT]
                ): NumberSelector(
                    NumberSelectorConfig(
                        mode=NumberSelectorMode.BOX, min=1, max=65535
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "LoxoneOptionsFlowHandler":
        return LoxoneOptionsFlowHandler(config_entry)


SETTINGS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_HOST): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Required(CONF_PORT): NumberSelector(
            NumberSelectorConfig(mode=NumberSelectorMode.BOX, min=1, max=65535)
        ),
        vol.Required(CONF_SCENE_GEN): BooleanSelector(),
        vol.Optional(CONF_SCENE_GEN_DELAY): NumberSelector(
            NumberSelectorConfig(mode=NumberSelectorMode.BOX, min=3)
        ),
        vol.Required(CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN): BooleanSelector(),
        vol.Required(CONF_CREATE_AREAS): BooleanSelector(),
    }
)


class LoxoneOptionsFlowHandler(OptionsFlow):
    """Options flow with menu: Settings / Device Bridges."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        super().__init__()
        self._options: dict[str, Any] = dict(config_entry.options)

    # -- Menu ----------------------------------------------------------------

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        return self.async_show_menu(
            step_id="init",
            menu_options=["settings", "bridge_menu"],
        )

    # -- Settings (existing connection options) ------------------------------

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            try:
                user_input[CONF_USERNAME].encode("latin-1")
            except UnicodeEncodeError:
                return self.async_show_form(
                    step_id="settings",
                    data_schema=self._settings_schema(),
                    errors={
                        "base": "Username contains characters that are not latin-1 compatible"
                    },
                )
            try:
                user_input[CONF_PASSWORD].encode("latin-1")
            except UnicodeEncodeError:
                return self.async_show_form(
                    step_id="settings",
                    data_schema=self._settings_schema(),
                    errors={
                        "base": "Password contains characters that are not latin-1 compatible"
                    },
                )

            if CONF_PORT in user_input:
                user_input[CONF_PORT] = int(user_input[CONF_PORT])
            if CONF_SCENE_GEN_DELAY in user_input:
                user_input[CONF_SCENE_GEN_DELAY] = int(
                    user_input[CONF_SCENE_GEN_DELAY]
                )

            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        return self.async_show_form(
            step_id="settings",
            data_schema=self._settings_schema(),
        )

    def _settings_schema(self) -> vol.Schema:
        return self.add_suggested_values_to_schema(SETTINGS_SCHEMA, self._options)

    # -- Device Bridges Menu -------------------------------------------------

    async def async_step_bridge_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        bridges = self._options.get("bridges", [])

        if bridges:
            lines = [f"  {self._bridge_label(b)}" for b in bridges]
            bridges_text = "\n".join(lines)
        else:
            bridges_text = "  (none)"

        menu_options = ["bridge_add"]
        if bridges:
            menu_options.append("bridge_remove")
        menu_options.append("bridge_done")

        return self.async_show_menu(
            step_id="bridge_menu",
            menu_options=menu_options,
            description_placeholders={"bridges": bridges_text},
        )

    # -- Add Bridge ----------------------------------------------------------

    async def async_step_bridge_add(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            entity_id = user_input["entity_id"]
            loxone_control = user_input["loxone_control"]

            ctrl_info = self._resolve_control(loxone_control)
            if ctrl_info is None:
                return self.async_show_form(
                    step_id="bridge_add",
                    data_schema=self._bridge_add_schema(),
                    errors={"loxone_control": "Control not found in structure file"},
                )

            bridge_dict: dict[str, Any] = {
                "entity_id": entity_id,
                "loxone_uuid": ctrl_info["uuidAction"],
                "loxone_type": ctrl_info["type"],
                "loxone_states": ctrl_info.get("states", {}),
                "loxone_name": ctrl_info.get("label", ""),
                "cooldown": user_input.get("cooldown", 1.0),
                "details": ctrl_info.get("details", {}),
            }

            bridge_list = list(self._options.get("bridges", []))
            bridge_list.append(bridge_dict)
            self._options["bridges"] = bridge_list

            return await self.async_step_bridge_menu()

        return self.async_show_form(
            step_id="bridge_add",
            data_schema=self._bridge_add_schema(),
        )

    # -- Remove Bridge -------------------------------------------------------

    async def async_step_bridge_remove(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        bridge_list = list(self._options.get("bridges", []))

        if user_input is not None:
            idx = int(user_input["bridge"])
            if 0 <= idx < len(bridge_list):
                bridge_list.pop(idx)
            self._options["bridges"] = bridge_list
            return await self.async_step_bridge_menu()

        options = [
            SelectOptionDict(
                value=str(i),
                label=self._bridge_label(b),
            )
            for i, b in enumerate(bridge_list)
        ]

        schema = vol.Schema(
            {
                vol.Required("bridge"): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="bridge_remove", data_schema=schema)

    # -- Done (save) ---------------------------------------------------------

    async def async_step_bridge_done(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        return self.async_create_entry(title="", data=self._options)

    # -- Helpers -------------------------------------------------------------

    def _get_structure_file(self) -> dict:
        coordinator = getattr(self.config_entry, "runtime_data", None)
        if coordinator and hasattr(coordinator, "api"):
            return coordinator.api.structure_file or {}
        return {}

    def _build_control_options(self) -> list[SelectOptionDict]:
        """Build a flat list of bridgeable controls from the structure file."""
        structure = self._get_structure_file()
        controls = structure.get("controls", {})
        rooms = structure.get("rooms", {})
        options: list[SelectOptionDict] = []

        for uuid, ctrl in controls.items():
            ctrl_type = ctrl.get("type", "")
            room_name = rooms.get(ctrl.get("room", ""), {}).get("name", "")

            if ctrl_type in _BRIDGEABLE_TOP_LEVEL:
                label = ctrl.get("name", uuid)
                if room_name:
                    label = f"{room_name} / {label} ({ctrl_type})"
                else:
                    label = f"{label} ({ctrl_type})"
                options.append(SelectOptionDict(value=uuid, label=label))

            if ctrl_type == "LightControllerV2":
                ctrl_name = ctrl.get("name", uuid)
                for _sc_key, sc in ctrl.get("subControls", {}).items():
                    sc_type = sc.get("type", "")
                    if sc_type not in _BRIDGEABLE_SUBCTRLS:
                        continue
                    if "masterValue" in _sc_key or "masterColor" in _sc_key:
                        continue
                    sc_uuid = sc.get("uuidAction", _sc_key)
                    sc_name = sc.get("name", sc_uuid)
                    if room_name:
                        label = f"{room_name} / {ctrl_name} / {sc_name} ({sc_type})"
                    else:
                        label = f"{ctrl_name} / {sc_name} ({sc_type})"
                    options.append(SelectOptionDict(value=sc_uuid, label=label))

        options.sort(key=lambda o: o["label"])
        return options

    def _resolve_control(self, uuid_action: str) -> dict[str, Any] | None:
        """Look up a control or sub-control by its uuidAction."""
        structure = self._get_structure_file()
        controls = structure.get("controls", {})
        rooms = structure.get("rooms", {})

        for _uuid, ctrl in controls.items():
            room_name = rooms.get(ctrl.get("room", ""), {}).get("name", "")

            if ctrl.get("uuidAction") == uuid_action:
                return {
                    "uuidAction": uuid_action,
                    "type": ctrl.get("type", ""),
                    "states": ctrl.get("states", {}),
                    "details": ctrl.get("details", {}),
                    "label": f"{ctrl.get('name', '')} ({room_name})"
                    if room_name
                    else ctrl.get("name", ""),
                }

            for _sc_key, sc in ctrl.get("subControls", {}).items():
                if sc.get("uuidAction") == uuid_action:
                    ctrl_name = ctrl.get("name", "")
                    sc_name = sc.get("name", "")
                    label = f"{ctrl_name} / {sc_name}"
                    if room_name:
                        label = f"{room_name} / {label}"
                    return {
                        "uuidAction": uuid_action,
                        "type": sc.get("type", ""),
                        "states": sc.get("states", {}),
                        "details": sc.get("details", {}),
                        "label": label,
                    }
        return None

    def _bridge_add_schema(self) -> vol.Schema:
        control_options = self._build_control_options()

        fields: dict[Any, Any] = {
            vol.Required("entity_id"): EntitySelector(EntitySelectorConfig()),
            vol.Required("loxone_control"): SelectSelector(
                SelectSelectorConfig(
                    options=control_options,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional("cooldown", default=1.0): NumberSelector(
                NumberSelectorConfig(
                    min=0,
                    max=60,
                    step=0.1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="s",
                )
            ),
        }
        return vol.Schema(fields)

    @staticmethod
    def _bridge_label(b: dict) -> str:
        entity = b.get("entity_id", "?")
        lox = b.get("loxone_name") or b.get("loxone_uuid", "?")
        lox_type = b.get("loxone_type", "")
        return f"{entity} \u2194 {lox} ({lox_type})"
