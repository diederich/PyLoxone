# Home Assistant Integration Layer

> Technical deep dive into the HA integration code at `custom_components/loxone/`
>
> For the lights subsystem, see [LIGHTS_SUBSYSTEM.md](LIGHTS_SUBSYSTEM.md).
> For the low-level API client, see [API_LAYER.md](API_LAYER.md).
> For sync lifecycle and registry services, see [SYNC_ENGINE.md](SYNC_ENGINE.md).

## Integration Entry Point (`__init__.py`)

The largest file in the integration layer. Handles:

- Config entry setup/unload/migration
- Service registration (8 services)
- Event bus routing (WS → HA, HA → WS)
- Base entity class (`LoxoneEntity`)
- Legacy discovery and group creation

### Setup Flow

```python
async_setup(hass, config)
    │
    ├── hass.data[DOMAIN] = {}       ← marker only, coordinator stored in runtime_data
    ├── _async_register_services(hass)      ← domain-level services (lazy coordinator lookup)
    │     event_websocket_command
    │     event_secured_websocket_command
    │     sync_areas, sync_device_names, reload
    └── return True

async_setup_entry(hass, config_entry: LoxoneConfigEntry)
    │
    ├── Create LoxoneCoordinator
    ├── coordinator.async_config_entry_first_refresh()
    │     └── api.open() → HTTP setup, structure file
    │
    ├── Build MiniServer from structure file
    ├── config_entry.runtime_data = coordinator    ← typed via LoxoneConfigEntry
    │
    ├── async_forward_entry_setups(LOXONE_PLATFORMS)    ← loads platforms
    ├── async_load_platform() for sensor + binary_sensor ← YAML custom entity escape hatch
    │
    ├── BridgeRuntime.async_setup()   ← restore persisted device bridges
    │
    ├── Register event listeners:
    │     loxone_send → loxone_send()
    │     loxone_send_secured → (secured variant)
    │
    └── api.start_listening(message_callback) → WebSocket
```

### Service Definitions

| Service                           | Type   | Purpose                              |
| --------------------------------- | ------ | ------------------------------------ |
| `event_websocket_command`         | Domain | Send WS command by UUID or entity ID |
| `event_secured_websocket_command` | Domain | Secured WS command with PIN code     |
| `sync_areas`                      | Domain | Sync HA device areas from Loxone rooms (clears entity-level overrides) |
| `sync_device_names`               | Domain | Sync HA device names from structure  |
| `reload`                          | Domain | Reload integration                   |
| `enable_sun_automation`           | Entity | Enable jalousie sun automation       |
| `disable_sun_automation`          | Entity | Disable jalousie sun automation      |
| `quick_shade`                     | Entity | Move jalousie to shade position      |

### Base Entity: `LoxoneEntity`

All platform entities inherit from `LoxoneEntity(Entity)`:

```python
class LoxoneEntity(Entity):
    _attr_should_poll = False       # Event-driven, not polled

    def __init__(self, **kwargs):
        # Extracts: name, type, uuidAction, states, room, cat,
        # details, subControls from config dict
        self.type = kwargs.get("type", "")
        self.uuidAction = kwargs.get("uuidAction", "")
        self.states = kwargs.get("states", {})
        ...

    async def async_added_to_hass(self):
        # Subscribes to ALL loxone_event events
        # Filters by UUID match in event_handler()

    def event_handler(self, event):
        # Override in subclasses
        if self.uuidAction in event.data:
            self._state = event.data[self.uuidAction]
            self.schedule_update_ha_state()
```

**Concern:** Every entity receives every event and filters client-side. With many entities and frequent updates, this is O(entities × events).

## Device Bridge (`bridge.py` + `bridge_mappers.py`)

Maps a single HA entity (e.g. a Hue light, EP One sensor) to a single Loxone control or sub-control. The integration auto-detects the mapping type from the HA entity domain and Loxone control type, handling value conversion, scaling, and echo protection automatically.

### Supported mappings

| HA Domain        | Loxone Type      | Behaviour                                       |
| ---------------- | ---------------- | ----------------------------------------------- |
| `light`          | `ColorPickerV2`  | Brightness + HS color + color temp, bidirectional. Protocol: `hsv(h,s,v)` / `temp(brightness,kelvin)` |
| `light`          | `Dimmer`/`EIBDimmer` | Brightness (0-255 ↔ 0-100) + on/off, bidirectional |
| `light`          | `Switch`         | On/off only, bidirectional                      |
| `switch`         | `Switch`         | On/off, bidirectional                           |
| `binary_sensor`  | `Switch` (VI)    | Expose only (HA state → 0/1)                   |
| `sensor`         | `Slider` (VI)    | Expose only (HA state → float)                 |

### Key concepts

- **DeviceBridge** — persisted in `config_entry.options["bridges"]`, maps an `entity_id` to a Loxone `uuidAction` + control type + state UUIDs. No manual sync_type, direction, or attribute fields — all derived from the entity domain and control type.
- **BridgeMapper** — abstract base class with concrete implementations per Loxone control type (`ColorPickerMapper`, `DimmerMapper`, `SwitchMapper`, etc.). Each mapper implements `ha_state_to_command()` (HA → Loxone) and `loxone_value_to_ha()` (Loxone → HA).
- **BridgeRuntime** — manages bridge lifecycle: activates listeners on HA state changes and Loxone events, applies cooldown (trailing-edge debounce) and echo protection (suppress round-trip loops in bidirectional bridges).
- **Entity suppression** — when a Loxone sub-control is used in a bridge, the integration skips creating the native HA entity for it, preventing duplicates.
- **Options Flow UI** — menu-based: Settings / Device Bridges, with Add Bridge (entity selector + Loxone control picker) / Remove Bridge / Done steps. The control picker shows both top-level controls and LightControllerV2 sub-controls from the structure file.
- **Direction auto-detection** — derived from the Loxone control type and available state UUIDs. Sub-controls with feedback states (e.g. `position` for Dimmer, `color` for ColorPickerV2) are bidirectional; top-level VIs without feedback are expose-only.

## Coordinator (`coordinator.py`)

Wraps `DataUpdateCoordinator` but does **not** use it for polling:

```python
class LoxoneCoordinator(DataUpdateCoordinator):
    def __init__(self, ...):
        super().__init__(hass, _LOGGER, name="LoxoneCoordinator", update_method=None)
        self.api = LoxoneConnection(host, port, user, pass)

    async def _async_update_data(self):
        print("_async_update_data")   # Debug print left in
        return None

    async def async_cleanup(self):
        await self.api.close()
```

The coordinator is really a **connection manager**, not a data coordinator. The `DataUpdateCoordinator` base class is used only for its lifecycle integration with HA, not for its polling capability.

## MiniServer (`miniserver.py`)

Parses `LoxAPP3.json` (the Loxone structure file) into a navigable object:

```python
class MiniServer:
    serial: str
    miniserver_type: int
    name: str
    software_version: str
    miniserver_id: str          # from config entry

    def __init__(self, config: dict, miniserver_id: str):
        cfg = ConfigDataClass(config)
        self.serial = cfg["msInfo"]["serialNr"]
        ...
```

`ConfigDataClass` is a dict-like wrapper that provides attribute-style access.

`get_miniserver_from_hass()` iterates config entries and returns the first available:

```python
def get_miniserver_from_hass(hass):
    for entry in hass.config_entries.async_entries(DOMAIN):
        coordinator = getattr(entry, "runtime_data", None)
        if coordinator is not None and coordinator.miniserver is not None:
            return coordinator.miniserver
    return None
```

This helper still exists for legacy call sites, but **new code should prefer `config_entry.runtime_data`** (the `LoxoneCoordinator` for that entry) so behavior is correct with multiple Miniservers.

## Config Flow (`config_flow.py`)

Uses standard `ConfigFlow` with live connection validation, serial-based `unique_id`, and `async_step_reauth`:

```python
CONFIG_FLOW = {
    "user": SchemaFlowFormStep(DATA_SCHEMA_SETUP, validate_loxone_setup)
}
OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(DATA_SCHEMA_OPTIONS)
}
```

### Validation

Validates credentials via HTTP (`_async_validate_credentials`) and fetches the Miniserver serial (`_async_fetch_serial`) for use as `unique_id`. Supports `async_step_reauth` (re-authenticate on credential failure), `async_step_reconfigure` (change connection settings), and `async_step_dhcp` (DHCP auto-discovery via MAC prefix `504F94`).

User/password must remain Latin-1 encodable where the flow enforces it, and host/port/schema fields are validated as part of setup.

## Platform Analysis

### sensor.py

| Entity Class            | Loxone Type     | HA Device Class | Notes                         |
| ----------------------- | --------------- | --------------- | ----------------------------- |
| `LoxoneSensor`          | InfoOnlyAnalog  | Auto-detected   | Format string → unit mapping  |
| `LoxoneSensor`          | InfoOnlyDigital | —               | 0/1 values                    |
| `LoxoneMeterSensor`     | Meter           | Various         | Creates subsensors per detail |
| `LoxoneTextSensor`      | TextInput       | —               | Bidirectional text            |
| `LoxoneKeepAliveSensor` | —               | TIMESTAMP       | Last WS message time          |
| `LoxoneVersionSensor`   | —               | —               | Miniserver version            |
| `LoxoneCustomSensor`    | —               | —               | YAML-defined (legacy)         |

**Issue:** `SENSOR_TYPES` has duplicate `key="power"` entries for both Watt and Kilowatt.

### binary_sensor.py

| Entity Class          | Loxone Type     | HA Device Class |
| --------------------- | --------------- | --------------- |
| `LoxoneDigitalSensor` | InfoOnlyDigital | Auto-detected   |
| `LoxoneDigitalSensor` | Presence        | PRESENCE        |
| `LoxoneDigitalSensor` | Smoke           | SMOKE           |

**Issues:**

- Docstring says "Support for Fritzbox binary sensors" — copy-paste error
- Dispatcher signal `"binairy_sensors"` is a typo and doesn't match the signal used elsewhere (`"sensors"`)
- Smoke sensor detection order bug: `if self.type == "smoke"` check can be shadowed

### switch.py

| Entity Class               | Loxone Type | Notes                     |
| -------------------------- | ----------- | ------------------------- |
| `LoxoneSwitch`             | Switch      | On/Off                    |
| `LoxoneTimedSwitch`        | TimedSwitch | On with optional duration |
| `LoxoneIntercomSubControl` | Intercom    | SubControls as switches   |

**Issue:** Uses sync `hass.bus.fire()` instead of `hass.bus.async_fire()`.

### cover.py

| Entity Class     | Loxone Type | Features                          |
| ---------------- | ----------- | --------------------------------- |
| `LoxoneGate`     | Gate        | Open, close, stop                 |
| `LoxoneWindow`   | Window      | Open, close, stop                 |
| `LoxoneJalousie` | Jalousie    | Open, close, stop, tilt, sun auto |

**Issues:**

- Dispatcher passes wrong callback argument
- Uses `random.uniform()` for lamella positioning (non-deterministic)
- `is_sun_automation_enabled` returns string instead of `bool | None`
- Typo: `shade_postion_as_text`

### climate.py

| Entity Class             | Loxone Type       | Modes                           |
| ------------------------ | ----------------- | ------------------------------- |
| `LoxoneRoomController`   | IRoomController   | HEAT, COOL, AUTO, OFF           |
| `LoxoneRoomControllerV2` | IRoomControllerV2 | HEAT, COOL, AUTO, OFF           |
| `LoxoneAcControl`        | AcControl         | HEAT, COOL, FAN_ONLY, DRY, AUTO |

**Critical bug in `LoxoneAcControl`:**

```python
async def async_set_temperature(self, **kwargs):
    temperature = kwargs["targetTemperature"]  # Wrong key!
    # HA passes kwargs["temperature"] → KeyError
```

**Security risk in `LoxoneRoomControllerV2`:**

```python
def is_overridden(self):
    override_entries = eval(self.states["overrideEntries"])  # eval() on external data
```

### fan.py

| Entity Class        | Loxone Type | Features            |
| ------------------- | ----------- | ------------------- |
| `LoxoneVentilation` | Ventilation | Speed, preset modes |

- Docstring: "Interfaces with Alarm.com alarm control panels" — copy-paste
- `set_preset_mode()` is empty/not implemented

### alarm_control_panel.py

| Entity Class  | Loxone Type | Modes                      |
| ------------- | ----------- | -------------------------- |
| `LoxoneAlarm` | Alarm       | ARM_HOME, ARM_AWAY, DISARM |

- `code_arm_required` property mutates `self._code` (side effect in property)
- Possible double event subscription

### media_player.py

| Entity Class        | Loxone Type | Features                    |
| ------------------- | ----------- | --------------------------- |
| `LoxoneAudioZoneV2` | AudioZoneV2 | Play, pause, volume, source |

- `play_state_to_media_player_state` has no default return → can return `None`
- `async_media_stop` sends `"pause"` instead of stop

### number.py

| Entity Class   | Loxone Type | Range               |
| -------------- | ----------- | ------------------- |
| `LoxoneNumber` | Slider      | min/max from config |

- Uses sync `schedule_update_ha_state()` instead of async

### button.py

| Entity Class   | Loxone Type | Notes            |
| -------------- | ----------- | ---------------- |
| `LoxoneButton` | Pushbutton  | Stateless, pulse |

- Uses sync `hass.bus.fire()`
- Fragile `cached_property` cache invalidation via `__dict__.pop()`

### scene.py

| Entity Class        | Source            | Notes              |
| ------------------- | ----------------- | ------------------ |
| `LoxoneLightScene`  | LightControllerV2 | Moods as HA scenes |

- Uses `hass.data["light"].get_entity()` — depends on internal HA structure (same pattern as light platform discovery)
- Implements `device_info` linking the scene to the light controller device (and `via_device` to the Miniserver serial when known)
- `async_activate` fires `SENDDOMAIN` with `"miniserver": entry_id` so commands route to the correct integration entry in multi-Miniserver setups
- Does not extend `LoxoneEntity` — scenes only send commands; they do not need WS state subscriptions
- Inconsistent defaults: options default `False`, config flow default `True`

### text.py

| Entity Class | Loxone Type | Notes               |
| ------------ | ----------- | ------------------- |
| `LoxoneText` | TextInput   | Editable text field |

**Critical: This platform is never loaded.** `Platform.TEXT` is missing from `LOXONE_PLATFORMS` in `const.py`. Additionally, `LoxoneTextSensor` in `sensor.py` already handles TextInput, creating potential overlap.

## Cross-Cutting Concerns

### Sync vs Async Inconsistency

Many entities mix sync and async patterns:

| Pattern                      | Locations                      | Should Be                          |
| ---------------------------- | ------------------------------ | ---------------------------------- |
| `hass.bus.fire()`            | switch.py, button.py           | `hass.bus.async_fire()`            |
| `schedule_update_ha_state()` | cover.py, number.py, button.py | `async_schedule_update_ha_state()` |
| `hass.loop.call_later()`     | scene.py                       | `hass.async_create_task()`         |

### `eval()` Usage

`eval()` is used to parse Loxone data strings in multiple places:

| Location                    | Data                               | Risk                 |
| --------------------------- | ---------------------------------- | -------------------- |
| `climate.py`                | `overrideEntries`                  | High — external data |
| `lights/colorpickers.py`    | `temp(50,3000)`, `hsv(180,100,80)` | Medium — structured  |
| `lights/lightcontroller.py` | `activeMoods`, `moodList`          | Medium — lists/dicts |

All should use `ast.literal_eval()` or purpose-built parsers.

### Device Registry

`helpers.py` maintains its own `device_registry` dict (a module-level mutable global):

```python
device_registry = {}

def get_or_create_device(loxone_id, name):
    if loxone_id not in device_registry:
        device_registry[loxone_id] = {"name": name, ...}
    return device_registry[loxone_id]
```

This is separate from HA's actual device registry and can lead to stale entries, memory leaks (never cleaned), and confusion about which registry is authoritative.

### Per-UUID dispatcher routing (inbound state)

WebSocket messages are parsed into a dict keyed by UUID. The coordinator’s `_message_callback` sends **one signal per changed UUID**:

- Signal name: `loxone_{config_entry.entry_id}_uuid_{uuid}`
- Payload: the full message dict (same as before per handler)

`LoxoneEntity.async_added_to_hass` connects `async_dispatcher_connect` for each UUID the entity cares about (`uuidAction` plus values in `states`). The dispatcher callback schedules `event_handler(message)`, so only subscribers for that UUID run.

A separate `monitor_signal` (`loxone_{entry_id}_monitor`) receives the full message for components that need it (e.g. WebSocket event forwarding).

Device triggers still use the HA event bus (`EVENT_LOXONE_STATE_CHANGE`) with a per-UUID lookup into the device registry — that path is separate from entity updates.

### Copy-Paste Docstrings

Module docstrings in `binary_sensor.py`, `fan.py`, and `alarm_control_panel.py` are now Loxone-specific; the old cross-project copy-paste lines are **no longer present** in the codebase.

### Deprecated HA APIs

| Usage                                            | Location      | Replacement                                            |
| ------------------------------------------------ | ------------- | ------------------------------------------------------ |
| `DeviceInfo` from `homeassistant.helpers.entity` | lights/\*.py  | `homeassistant.helpers.device_registry.DeviceInfo`     |
| `async_load_platform()`                          | `__init__.py` | Already using `async_forward_entry_setups` (duplicate) |
| `hass.data["light"].get_entity()`                | `scene.py`    | Entity registry lookup                                 |
