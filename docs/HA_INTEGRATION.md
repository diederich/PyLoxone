# Home Assistant Integration Layer

> Technical deep dive into the HA integration code at `custom_components/loxone/`
>
> For the lights subsystem, see [LIGHTS_SUBSYSTEM.md](LIGHTS_SUBSYSTEM.md).
> For the low-level API client, see [API_LAYER.md](API_LAYER.md).

## Integration Entry Point (`__init__.py`)

The largest file in the integration layer. Handles:

- Config entry setup/unload/migration
- Service registration (8 services)
- Event bus routing (WS → HA, HA → WS)
- Base entity class (`LoxoneEntity`)
- Legacy discovery and group creation

### Setup Flow

```python
async_setup_entry(hass, config_entry)
    │
    ├── Create LoxoneCoordinator
    ├── coordinator.async_config_entry_first_refresh()
    │     └── api.open() → HTTP setup, structure file
    │
    ├── Build MiniServer from structure file
    ├── Store coordinator in hass.data[DOMAIN][entry_id]
    │
    ├── async_forward_entry_setups(LOXONE_PLATFORMS)    ← loads platforms
    ├── async_load_platform() for sensor + binary_sensor ← YAML custom entity escape hatch
    │
    ├── Register services:
    │     event_websocket_command
    │     event_secured_websocket_command
    │     sync_areas
    │     sync_device_names
    │     sync / unsync            ← new: expose HA state to Loxone VIs
    │     reload
    │
    ├── LoxoneSync.async_setup()   ← restore persisted sync bindings
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
| `sync_areas`                      | Domain | Sync HA areas from Loxone rooms      |
| `sync_device_names`               | Domain | Sync HA device names from structure  |
| `sync`                            | Domain | Bind HA entity state to Loxone VI    |
| `unsync`                          | Domain | Remove a sync binding                |
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

## Sync Module (`sync.py`)

Binds HA entities to Loxone controls in one or both directions:

- **Expose (HA → Loxone):** Listens for HA `state_changed` events and pushes converted values to a Loxone Virtual Input via `jdev/sps/io/{uuid}/{value}`.
- **Subscribe (Loxone → HA):** Listens for Loxone event-table updates on a Virtual Output UUID and updates the bound HA entity via domain-appropriate service calls (`input_boolean`, `input_number`, `input_text`) or `async_set` fallback.

Each binding can set either direction, or both for bidirectional sync.

### Key concepts

- **SyncBinding** — persisted in `config_entry.options["sync"]`, maps an `entity_id` to Loxone controls with type (binary/analog/text), optional attribute, and cooldown. Fields: `vi_name`/`vi_uuid` (expose), `vo_name`/`vo_uuid` (subscribe) — at least one direction required.
- **Name resolution** — `vi_name` resolved to UUID from the structure file; optional `room` qualifier for disambiguation
- **Echo/loop protection** — three layers: skip_unchanged (tracks `last_sent_value`), analog epsilon (0.01), trailing-edge cooldown debounce (default 1s)
- **Services** — `loxone.sync` to add bindings, `loxone.unsync` to remove them; managed by `LoxoneSync` class instantiated in `async_setup_entry`
- **Options Flow UI** — menu-based options flow in `config_flow.py` with Add / Remove / Done steps; separate Loxone Input and Output control dropdowns populated from the structure file
- **Update listener** — `config_entry.add_update_listener` triggers `async_options_updated()` when options change via the UI, re-initializing bindings; internal changes via services use `_self_update` flag to avoid double-init
- **Persistence** — bindings survive restarts via `config_entry.options`; on setup, current state is pushed immediately

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

**Issue:** `get_miniserver_from_hass()` assumes at least one entry exists:

```python
def get_miniserver_from_hass(hass):
    for k, v in hass.data[DOMAIN].items():
        return v.miniserver    # Returns first one found
```

## Config Flow (`config_flow.py`)

Uses `SchemaConfigFlowHandler` — a declarative approach:

```python
CONFIG_FLOW = {
    "user": SchemaFlowFormStep(DATA_SCHEMA_SETUP, validate_loxone_setup)
}
OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(DATA_SCHEMA_OPTIONS)
}
```

### Validation

Only validates:

- Username/password are Latin-1 encodable (Loxone requirement)
- Port is castable to int

**Does not** test actual connectivity during setup. A user can configure invalid credentials and only discover the error at runtime.

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

| Entity Class       | Source            | Notes              |
| ------------------ | ----------------- | ------------------ |
| `Loxonelightscene` | LightControllerV2 | Moods as HA scenes |

- Uses `hass.data["light"].get_entity()` — depends on internal HA structure
- Does not extend `LoxoneEntity` — no event subscription
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

### Event Bus Broadcast

Every `loxone_event` is broadcast to all entities. Each entity checks if its UUID is in the event data:

```python
# In every entity's event_handler:
if self.uuidAction in event.data:
    ...
for uuid in self.states:
    if self.states[uuid] in event.data:
        ...
```

With 100+ entities and frequent state updates, this means thousands of unnecessary dict lookups per update cycle. A dispatch-by-UUID approach (e.g., `async_dispatcher_send` per UUID) would be far more efficient.

### Copy-Paste Docstrings

Several files have docstrings from other projects:

- `binary_sensor.py`: "Support for Fritzbox binary sensors"
- `fan.py`: "Interfaces with Alarm.com alarm control panels"
- `alarm_control_panel.py`: "Interfaces with Alarm.com alarm control panels"

### Deprecated HA APIs

| Usage                                            | Location      | Replacement                                            |
| ------------------------------------------------ | ------------- | ------------------------------------------------------ |
| `DeviceInfo` from `homeassistant.helpers.entity` | lights/\*.py  | `homeassistant.helpers.device_registry.DeviceInfo`     |
| `async_load_platform()`                          | `__init__.py` | Already using `async_forward_entry_setups` (duplicate) |
| `hass.data["light"].get_entity()`                | `scene.py`    | Entity registry lookup                                 |
