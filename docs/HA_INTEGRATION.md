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
    ├── hass.data[DOMAIN] = {}              ← marker only; coordinator stored in runtime_data
    ├── _async_register_services(hass)      ← domain-level services (lazy coordinator lookup)
    │     event_websocket_command
    │     event_secured_websocket_command
    │     sync_areas, sync_device_names, reload
    └── return True

async_setup_entry(hass, config_entry: LoxoneConfigEntry)
    │
    ├── Create LoxoneCoordinator
    ├── coordinator.async_config_entry_first_refresh()
    │     └── api.open() → HTTP bootstrap (API key, structure file, RSA public key)
    │
    ├── Build MiniServer from structure file
    ├── config_entry.runtime_data = coordinator    ← typed via LoxoneConfigEntry
    │
    ├── async_forward_entry_setups(LOXONE_PLATFORMS)    ← loads all platforms (entities created here)
    ├── async_load_platform() for sensor + binary_sensor ← YAML custom entity escape hatch
    │
    ├── BridgeRuntime.async_setup()   ← restore persisted device bridges
    │
    ├── Register event listeners:
    │     loxone_send → loxone_send()
    │     loxone_send_secured → (secured variant)
    │
    ├── await coordinator.async_start_listening()
    │     └── Starts WebSocket session as background task (does not block bootstrap)
    │
    └── async_dispatcher_send("loxone_{entry_id}_reconnected")
          └── Triggers one-time-per-session work (scene generation etc.)
              See "The _reconnected signal" in ARCHITECTURE.md
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
    _attr_should_poll = False       # Push-driven via dispatcher, not polled

    def __init__(self, **kwargs):
        # Extracts: name, type, uuidAction, states, room, cat,
        # details, subControls from config dict
        self.type = kwargs.get("type", "")
        self.uuidAction = kwargs.get("uuidAction", "")
        self.states = kwargs.get("states", {})
        ...

    async def async_added_to_hass(self):
        # Subscribes to per-UUID dispatcher signals for uuidAction and each value in states{}
        # Deregisters on config_entry.async_on_unload
        for uuid in {self.uuidAction, *self.states.values()}:
            self.async_on_remove(
                async_dispatcher_connect(hass, f"loxone_{entry_id}_uuid_{uuid}", self._handle)
            )

    @callback
    def _handle(self, message: dict) -> None:
        hass.async_create_task(self.event_handler(message))

    async def event_handler(self, message: dict) -> None:
        # Override in subclasses — receives the full parsed message dict for the entity's UUID
        ...
```

**Routing is O(1) per event.** Each incoming UUID fires a single dispatcher signal; only the one entity (or few entities) subscribed to that UUID wakes up. See [ARCHITECTURE.md — Runtime Event Flow](ARCHITECTURE.md) for the full dispatch chain.

## Device Bridge (`bridge.py` + `bridge_mappers.py`)

Maps a single HA entity (e.g. a Hue light, EP One sensor) to a single Loxone control or sub-control. The integration auto-detects the mapping type from the HA entity domain and Loxone control type, handling value conversion, scaling, and echo protection automatically.

### Supported mappings

| HA Domain        | Loxone Type          | Behaviour                                       |
| ---------------- | -------------------- | ----------------------------------------------- |
| `light`          | `ColorPickerV2`      | Brightness + HS color + color temp, bidirectional. Protocol: `hsv(h,s,v)` / `temp(brightness,kelvin)` |
| `light`          | `Dimmer`/`EIBDimmer` | Brightness (0-255 ↔ 0-100) + on/off, bidirectional |
| `light`          | `Switch`             | On/off only, bidirectional                      |
| `switch`         | `Switch`             | On/off, bidirectional                           |
| `binary_sensor`  | `Switch` (VI)        | Expose only (HA state → 0/1)                   |
| `sensor`         | `Slider` (VI)        | Expose only (HA state → float)                 |
| `number` / `input_number` | `Slider` (VI) | Bidirectional float value, no scaling          |
| `input_boolean`  | `Switch` (VI)        | On/off, bidirectional                           |
| `cover`          | compound VI + VOs    | Bidirectional position bridge — see below       |

#### Cover bridge (`CoverMapper`)

A cover bridge is **compound**: one entry maps to multiple Loxone controls. All VO fields are optional.

| Field in `DeviceBridge.details` | Loxone block | Role |
| ------------------------------- | ------------ | ---- |
| `loxone_uuid` (primary)         | Slider VI    | Position feedback — PyLoxone writes actual position (0–100) here so Loxone always knows where the shade is |
| `details["uuid_up_vo"]`         | Switch VO    | Drives high when moving up → `cover.open_cover` |
| `details["uuid_down_vo"]`       | Switch VO    | Drives high when moving down → `cover.close_cover` |
| `details["uuid_target_vo"]`     | Slider VO    | Target position (0–100) → `cover.set_cover_position` (or open/close at 100/0) |

The bridge panel shows a **Setup Guide** (collapsible) with recommended block names and wiring instructions, and a **Scan Loxone** button that searches the structure file for controls matching a naming convention derived from the entity ID and pre-fills the UUID fields.

Typical Loxone wiring for Velux: a Jalousie block with its up/down/manualPosition outputs connected to VOs, and the Slider VI fed back as the position input. The Jalousie block gives the Loxone app a proper shade tile with up/down/stop UI.

Rain sensors (`binary_sensor.*_rain`) are bridged separately using the existing `BinarySensorExposeMapper` → Switch VI.

### Key concepts

- **DeviceBridge** — persisted in `config_entry.options["bridges"]`, maps an `entity_id` to a Loxone `uuidAction` + control type + state UUIDs. The `details` dict carries extra configuration (e.g. VO UUIDs for cover bridges). All fields derived at bridge creation time from the HA domain and Loxone structure.
- **BridgeMapper** — abstract base class with concrete implementations per HA domain/Loxone type (`ColorPickerMapper`, `DimmerMapper`, `SwitchMapper`, `CoverMapper`, etc.). Each mapper implements `ha_state_to_command()` (HA → Loxone) and `loxone_value_to_ha()` (Loxone → HA).
- **BridgeRuntime** — manages bridge lifecycle: activates listeners on HA state changes and Loxone events, applies cooldown (trailing-edge debounce) and echo protection (suppress round-trip loops in bidirectional bridges).
- **Entity suppression** — when a Loxone control is used in a bridge, the integration disables the native HA entity for it, preventing duplicates. All UUIDs (including cover VO UUIDs) are tracked in `bridged_uuids` for this purpose.
- **Options Flow UI** — menu-based: Settings / Device Bridges, with Add Bridge (entity selector + Loxone control picker) / Remove Bridge / Done steps. Cover bridges show additional VO pickers, a setup guide, and a Scan button.
- **Direction auto-detection** — derived from the Loxone control type and available state UUIDs. Sub-controls with feedback states are bidirectional; top-level VIs without feedback are expose-only. Cover bridges derive directionality from which VO fields are populated.

### Bridge sync contract

Bidirectional bridges treat HA state changes and Loxone WebSocket values as two independent event streams. `BridgeRuntime` keeps per-bridge runtime state for the last HA → Loxone command, the last Loxone → HA value, pending cooldown commands, echo suppression, and a short HA feedback suppression window.

Loop prevention has three layers:

| Layer | Direction | Purpose |
| --- | --- | --- |
| Echo match | HA → Loxone → Loxone event | Suppresses a Loxone value only when it semantically matches the command PyLoxone just sent. Non-identical Loxone app changes are still processed. |
| HA feedback window | Loxone → HA → HA state event | Suppresses immediate HA state changes caused by the HA service call that applied a Loxone-originated update. |
| Last-value convergence | both | Ignores HA states that already match the last Loxone value, and duplicate Loxone values that already match the last received value. |

Mappers provide semantic normalization for comparisons. For example, `ColorPickerMapper` still sends Loxone's wire protocol (`hsv(...)`, `temp(...)`, `On`, `Off`), but equality is checked using normalized color values with tolerances for Hue/Hue Bridge round-trip drift. This avoids infinite RGB/HSV correction loops when HA and Loxone normalize colors slightly differently.

When a genuine Loxone event arrives, any pending HA → Loxone cooldown command is cancelled. Loxone has taken ownership of the current interaction, so stale HA commands must not flush later and overwrite the user's Loxone app action.

`loxone/get_bridges` exposes runtime diagnostics for each active bridge: persisted `loxone_states`, active `subscribe_uuids`, last sent/received values, pending command, echo flag, HA suppression remaining, and the last suppression reason. Use this alongside `loxone/subscribe_events` when debugging sync.

## Coordinator (`coordinator.py`)

`LoxoneCoordinator` wraps `DataUpdateCoordinator` but does **not** use it for polling. The base class is used only for its lifecycle integration with HA (config entry, first-refresh pattern).

The coordinator is the **connection manager** for one Miniserver. Its responsibilities:

- Owns one `LoxoneConnection` (`self.api`) and one `MiniServer` (`self.miniserver`)
- Starts and monitors the WebSocket listen task
- On disconnect: classifies the failure, starts reconnect with exponential backoff
- On reconnect: rebuilds `MiniServer`, fires `_reconnected` signal
- Cleans up `miniserver.listeners` before replacing the `MiniServer` object (prevents listener leaks)

### Task lifecycle

Both the listen task and the reconnect task are `config_entry.async_create_background_task`:

```python
# listen task — runs indefinitely; replaced after each reconnect
self._listening_task = config_entry.async_create_background_task(
    hass, coordinator.async_start_listening(), "loxone-listen"
)

# reconnect task — started when _handle_task_result detects a disconnect
self._reconnect_task = config_entry.async_create_background_task(
    hass, self._async_reconnect(), "loxone-reconnect"
)
```

**Why `async_create_background_task` and not `hass.async_create_task`?**
`hass.async_create_task` is tracked by the HA bootstrap watchdog — if the task is still running when HA checks progress, it triggers a restart. Long-running tasks must use `async_create_background_task`, which signals to HA "this task runs in the background and should not block startup."

### Reconnect flow

```
_handle_task_result(task)          ← done-callback registered on listen task
    │
    ├── Classify exception:
    │     LoxoneAuthError          → raise RepairIssue (no reconnect)
    │     ConnectionRefused        → exponential backoff, reconnect
    │     asyncio.CancelledError   → entry is unloading, stop
    │     other                    → exponential backoff, reconnect
    │
    └── config_entry.async_create_background_task(_async_reconnect())

_async_reconnect()
    ├── Cleanup: call all unsub callables in miniserver.listeners
    ├── api.close()
    ├── Backoff sleep (1s → 300s)
    ├── api.open()                 ← re-downloads structure file
    ├── self.miniserver = MiniServer(...)
    ├── miniserver.async_update_device_registry()
    ├── config_entry.async_create_background_task(_do_start_listening())
    └── async_dispatcher_send("loxone_{entry_id}_reconnected")
```

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

Sensor classification flows through `match_sensor_description(unit, name, category)`: unambiguous units (°C, kWh, ppm, …) match by unit alone; ambiguous units (%) require a keyword hit in the Loxone name or category to pick `humidity` vs `battery`. One description per concept — no per-variant duplication. See `README.md` → *Sensor Device Class Detection* for the user-facing table and override pattern.

**Meter discovery walks subControls.** `Meter` controls are surfaced as their own device with up to four subsensors (`Actual`, `Total`, `Total Returned`, `Level`). Discovery uses `helpers.get_all_including_subcontrols("Meter")` so meters nested inside a parent control — most commonly the per-circuit meters of a `PowerUnit` (Loxone Energy Flow Monitor) — are exposed alongside top-level meters. Subcontrol meters inherit `room` and `cat` from their parent when not set on the subcontrol itself.

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

**Scene generation is event-driven, not startup-once.**

Scenes are created dynamically by `gen_scenes()`, which is called each time `loxone_{entry_id}_reconnected` fires (initial connect + every reconnect). This keeps scenes valid even after a Miniserver disconnect.

**Why delayed generation?**

`gen_scenes()` reads `entity.effect_list`, which is populated by mood events in the Miniserver's state dump. The state dump arrives *after* the connection is established. A short `asyncio.sleep` delay (1 second, inside `run_delayed_scene_gen`) ensures moods are populated before scene entities are built.

**Deduplication:**

Before adding a scene, `gen_scenes()` checks the entity registry (`ent_reg.async_get_entity_id`). Scenes that already exist are skipped. This makes the function safe to call on every reconnect without producing "ID already exists" warnings.

**Other notes:**

- Does not extend `LoxoneEntity` — scenes only send commands and do not need WS state subscriptions
- `async_activate` fires `SENDDOMAIN` with `"miniserver": entry_id` so commands route to the correct config entry in multi-Miniserver setups
- Implements `device_info` linking each scene to its LightControllerV2 device (and `via_device` to the Miniserver serial when known)
- Uses `hass.data["light"].get_entity()` to look up the LightControllerV2 entity — this is a fragile internal HA API and should eventually be replaced with an entity registry lookup

### text.py

| Entity Class | Loxone Type | Notes               |
| ------------ | ----------- | ------------------- |
| `LoxoneText` | TextInput   | Editable text field |

**Critical: This platform is never loaded.** `Platform.TEXT` is missing from `LOXONE_PLATFORMS` in `const.py`. Additionally, `LoxoneTextSensor` in `sensor.py` already handles TextInput, creating potential overlap.

## Cross-Cutting Concerns

### Async Rules for this Codebase

Follow these rules when writing any code in `custom_components/loxone/`:

| Rule | Correct | Wrong |
|---|---|---|
| Fire HA bus events from async context | `hass.bus.async_fire()` | `hass.bus.fire()` |
| Schedule a state push | `async_schedule_update_ha_state()` | `schedule_update_ha_state()` |
| Short-lived tasks (commands, events) | `hass.async_create_task(coro)` | `asyncio.create_task(coro)` |
| Long-running tasks (listen, reconnect) | `config_entry.async_create_background_task(hass, coro, name)` | `hass.async_create_task(coro)` |
| Blocking I/O from async context | `await hass.async_add_executor_job(fn, *args)` | `fn(*args)` directly |
| Sync callback registered with dispatcher | `@callback` decorator | bare `async def` |
| Subscribe → auto-deregister on unload | `config_entry.async_on_unload(async_dispatcher_connect(...))` | bare `async_dispatcher_connect(...)` |

**Rationale for the `async_create_background_task` rule:** `hass.async_create_task` tasks are watched by HA's bootstrap supervisor. A never-ending task registered this way will eventually trigger a reboot (HA waits for all registered tasks to complete before finalising startup). The listen loop and reconnect loop are indefinite — they must not block startup.

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
