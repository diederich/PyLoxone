# PyLoxone Architecture

> Home Assistant custom integration for Loxone Miniserver
>
> For sync lifecycle and registry services, see [SYNC_ENGINE.md](SYNC_ENGINE.md).

## Project Identity

| Key              | Value                                         |
|------------------|-----------------------------------------------|
| Domain           | `loxone`                                      |
| Version          | 0.9.12                                        |
| License          | Apache 2.0                                    |
| HA minimum       | 2025.2.4                                      |
| Installation     | HACS or manual copy of `custom_components/`   |
| IoT class        | `local_push`                                  |
| Runtime deps     | `websockets>=14`, `pycryptodome`, `async-upnp-client` |

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Home Assistant Core                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Event   │  │  Entity  │  │  Device  │  │  Config  │              │
│  │   Bus    │  │ Registry │  │ Registry │  │  Entry   │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │              │              │              │                    │
├───────┼──────────────┼──────────────┼──────────────┼────────────────────┤
│       │     custom_components/loxone/              │                    │
│       │              │              │              │                    │
│  ┌────┴──────────────┴──────────────┴──────────────┴─────────────┐     │
│  │                     __init__.py                                │     │
│  │  - async_setup_entry()     - message_callback()               │     │
│  │  - service handlers        - event routing                    │     │
│  │  - LoxoneEntity base class                                    │     │
│  └───────────────────────────┬───────────────────────────────────┘     │
│                              │                                         │
│  ┌───────────────────────────┴───────────────────────────────────┐     │
│  │                     coordinator.py                             │     │
│  │  LoxoneCoordinator (DataUpdateCoordinator)                    │     │
│  │  - Connection lifecycle, reconnect, structure poll, repairs    │     │
│  │  - MiniServer construction; dispatcher_prefix, monitor_signal   │     │
│  └───────────────────────────┬───────────────────────────────────┘     │
│                              │                                         │
│  ┌───────────────────────────┴───────────────────────────────────┐     │
│  │                     pyloxone_api/                              │     │
│  │  ┌─────────────────┐  ┌──────────────────┐                   │     │
│  │  │  connection.py   │  │  loxone_token.py │                   │     │
│  │  │  (WS + crypto)  │  │  (auth tokens)   │                   │     │
│  │  └────────┬────────┘  └──────────────────┘                   │     │
│  │           │                                                   │     │
│  │  ┌────────┴────────┐  ┌──────────────────┐                   │     │
│  │  │ websocket_      │  │ loxone_http_     │                   │     │
│  │  │ protocol.py     │  │ client.py        │                   │     │
│  │  │ (WS framing)    │  │ (HTTP + Basic)   │                   │     │
│  │  └─────────────────┘  └──────────────────┘                   │     │
│  │  ┌─────────────────┐  ┌──────────────────┐                   │     │
│  │  │  message.py     │  │  discover.py     │                   │     │
│  │  │  (msg parsing)  │  │  (UDP LAN scan)  │                   │     │
│  │  └─────────────────┘  └──────────────────┘                   │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  ┌──────────── Entity Platforms ─────────────────────────────────┐     │
│  │  sensor.py     binary_sensor.py   switch.py    cover.py      │     │
│  │  climate.py    fan.py             alarm_control_panel.py      │     │
│  │  media_player.py  number.py       button.py    scene.py      │     │
│  │  text.py                                                      │     │
│  │                                                               │     │
│  │  lights/                                                      │     │
│  │  ├── colorpickers.py  (RGB, TunableWhite, LumiTech)          │     │
│  │  ├── dimmer.py        (Dimmer, EIBDimmer)                    │     │
│  │  ├── lightcontroller.py (LightControllerV2 moods)            │     │
│  │  └── switch.py        (on/off light subcontrols)             │     │
│  └───────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
PyLoxone/
├── custom_components/
│   └── loxone/
│       ├── __init__.py              # Integration entry point, services, base entity
│       ├── config_flow.py           # Config & options flow (SchemaConfigFlowHandler)
│       ├── coordinator.py           # DataUpdateCoordinator (connection manager)
│       ├── miniserver.py            # MiniServer abstraction over structure file
│       ├── const.py                 # Integration constants
│       ├── helpers.py               # Shared utilities (device registry, mappings)
│       ├── diagnostics.py           # Config entry diagnostics
│       ├── repairs.py               # Fixable repair flows (auth failure)
│       ├── system_health.py         # System health panel
│       ├── services.yaml            # Service definitions
│       ├── manifest.json            # Integration manifest
│       ├── translations/            # UI translations (en, de)
│       │
│       ├── sensor.py                # Analog, digital, meter, text, keep-alive sensors
│       ├── binary_sensor.py         # Digital, presence, smoke binary sensors
│       ├── switch.py                # Switches, timed switches, intercom
│       ├── cover.py                 # Gates, windows, jalousies
│       ├── climate.py               # RoomController(V2), AC control
│       ├── fan.py                   # Ventilation
│       ├── alarm_control_panel.py   # Alarm panel
│       ├── media_player.py          # AudioZoneV2
│       ├── number.py                # Slider controls
│       ├── button.py                # Pushbuttons
│       ├── scene.py                 # LightControllerV2 moods as scenes
│       ├── text.py                  # TextInput (never loaded — see issues)
│       ├── light.py                 # Light platform entry point
│       ├── bridge.py               # Device-level bridge (HA entity <-> Loxone control)
│       ├── bridge_mappers.py       # Type-specific bridge mappers
│       ├── websocket.py            # WebSocket API commands + panel registration
│       │
│       ├── frontend/               # Custom panel (Lit/TypeScript sidebar app)
│       │   ├── src/                # TypeScript source
│       │   │   ├── loxone-panel.ts # Panel entry (tabs: Devices, Areas, Bridges, Monitor, Console, Status)
│       │   │   ├── devices-view.ts # Loxone controls <-> HA entities table
│       │   │   ├── areas-view.ts   # Room-to-area mapping + sync
│       │   │   ├── bridges-view.ts # Bridge CRUD
│       │   │   ├── monitor-view.ts # Live WS message monitor
│       │   │   ├── console-view.ts # Command console (send_command)
│       │   │   ├── status-view.ts  # Connection / Miniserver status
│       │   │   ├── api.ts          # WebSocket/service API helpers
│       │   │   └── types.ts        # TypeScript interfaces
│       │   ├── test/               # Vitest tests
│       │   ├── loxone-panel.js     # Built bundle (served by HA)
│       │   ├── build.mjs           # esbuild build script
│       │   └── package.json
│       │
│       ├── lights/                  # Light entity implementations
│       │   ├── colorpickers.py
│       │   ├── dimmer.py
│       │   ├── lightcontroller.py
│       │   └── switch.py
│       │
│       └── pyloxone_api/            # Low-level API client
│           ├── api.py               # Placeholder (empty)
│           ├── connection.py        # WebSocket lifecycle, crypto, auth (~1420 lines)
│           ├── websocket_protocol.py # WS framing and message reception
│           ├── message.py           # Binary/text message parsing
│           ├── loxone_token.py      # Token storage and lifetime
│           ├── loxone_http_client.py # Async HTTP client (aiohttp + Basic Auth)
│           ├── discover.py          # UDP LAN discovery
│           ├── exceptions.py        # Exception hierarchy
│           ├── helper.py            # HMAC utilities (unused)
│           ├── const.py             # API-level constants
│           └── __main__.py          # Standalone CLI entry point
│
├── .github/workflows/              # CI: hassfest, HACS validation, stale
├── config/configuration.yaml       # Dev HA config
├── scripts/                        # setup, lint helper scripts
├── requirements.txt                # Dev dependencies
├── ruff.toml                       # Linter config
├── hacs.json                       # HACS metadata
└── README.md                       # User-facing documentation
```

## Data Flow

### Connection Setup

See [Connection Lifecycle](#connection-lifecycle) below for full detail. Summary:

```
1. async_setup_entry() creates LoxoneCoordinator
2. api.open() → HTTP bootstrap: API key, structure file, RSA public key
3. MiniServer built from structure file; platforms forwarded → entities created
4. coordinator.async_start_listening() — starts WebSocket as a background task:
   a. AES-256 key exchange + token authentication
   b. CMD_ENABLE_UPDATES → Miniserver sends full state dump then push updates
   c. Keepalive tasks begin (both directions, 30s cycle — see Keepalive Protocol)
5. loxone_{entry_id}_reconnected signal fires → scene generation triggered (with delay)
6. On disconnect → coordinator reconnects with exponential backoff (1s → 300s)
   Entities stay registered; state recovers via next full state dump
```

### Coordinator (`coordinator.py`)

The coordinator is the **connection manager** for one Miniserver. It owns the `LoxoneConnection` (`api`) and `MiniServer` objects, manages the listen and reconnect background tasks, dispatches per-UUID state signals, and fires the `_reconnected` signal after every successful connection. See [HA_INTEGRATION.md](HA_INTEGRATION.md) for the full reconnect flow.

### Runtime event routing (dispatcher, not broadcast)

State updates are not fan-out to every entity. The coordinator dispatches **per-UUID** Home Assistant signals of the form `loxone_{entry_id}_uuid_{uuid}` (prefix from `dispatcher_prefix` + control UUID). Subscribers receive only their UUID’s messages — **O(1)** routing per event, not **O(n)** across all entities. The `entry_id` segment keeps multiple Miniservers isolated.

### Runtime Event Flow

```
Loxone Miniserver
    │
    │  WebSocket (binary/text)
    ▼
LoxoneConnection._do_start_listening()    [pyloxone_api/connection.py]
    │  Parses header + payload via websocket_protocol
    │  On KEEPALIVE header → responds with "keepalive" (required by Miniserver protocol)
    ▼
coordinator._message_callback()           [coordinator.py]
    │  Per-UUID dispatch: async_dispatcher_send(hass, "loxone_{entry_id}_uuid_{uuid}", message)
    ▼
async_dispatcher → "loxone_{entry_id}_uuid_{uuid}"
    │  O(1) routing — only entities subscribed to that UUID wake up
    ▼
LoxoneEntity._dispatch_handler()          [__init__.py — @callback, sync]
    │  Schedules async event_handler via hass.async_create_task
    ▼
LoxoneEntity.event_handler()              [per-entity subclass]
    │  Updates internal state
    ▼
async_schedule_update_ha_state()          [HA core]
```

### Connection Lifecycle

The connection has two sequential phases on every connect (initial and reconnect):

```
Phase 1 — HTTP bootstrap  (api.open())
    ├── GET /jdev/cfg/apiKey          → version, serial, local/remote
    ├── GET /data/LoxAPP3.json        → full structure file (controls, rooms, cats)
    └── GET /jdev/sys/getPublicKey    → RSA public key for key exchange

Phase 2 — WebSocket session  (api.start_listening())
    ├── AES-256 key exchange (RSA-encrypted session key → server)
    ├── HMAC auth (username + password + server salt → token request or authwithtoken)
    ├── CMD_ENABLE_UPDATES → server sends full state dump + begins push updates
    └── Concurrent background tasks (all within the API layer):
          _do_start_listening   — message receive/parse/dispatch loop
          _process_message      — outbound command queue processor
          _keep_alive           — sends "keepalive" every 30s (client-initiated)
          _check_and_refresh_token — proactive token refresh before expiry
          _reconnect_task       — watches for reconnect_event (token errors)
```

After Phase 2 completes, the coordinator fires `loxone_{entry_id}_reconnected` — see below.

### Keepalive Protocol

Both sides independently send keepalives on a 30-second cycle:

| Direction | Trigger | Protocol | Consequence of missing |
|---|---|---|---|
| Server → client | Server timer, every 30s | 8-byte KEEPALIVE header | Server closes connection (code 1000) after ~3s of no response |
| Client → server | `_keep_alive` task, every 30s | `"keepalive"` text command | Server marks connection idle; may close after several missed pings |

**Critical:** when the server sends a KEEPALIVE header, the client *must* immediately respond with a `"keepalive"` text command (`_do_start_listening` handles this). Without the response, the server closes the connection ~3 seconds after its ping — causing a spurious disconnect-reconnect cycle every 30 seconds.

### Task Management Rules

HA's event loop has strict rules about how long-running tasks are created:

| API | Blocks bootstrap? | Tracked for shutdown? | Use for |
|---|---|---|---|
| `hass.async_create_task(coro)` | **Yes** — HA waits for it | Yes | Short-lived tasks (command dispatch, event handlers) |
| `config_entry.async_create_background_task(hass, coro, name)` | **No** | Yes — cancelled on entry unload | Long-running tasks (WebSocket listen loop, reconnect loop) |
| `asyncio.create_task(coro)` | No | No | Internal tasks inside `pyloxone_api` that HA doesn't own |

**The listen and reconnect tasks are `async_create_background_task`** — they run indefinitely and must not block HA startup. Using `hass.async_create_task` for them causes HA's bootstrap to wait forever and reboot after a 5-minute timeout.

### Reconnect & State Recovery

On disconnect, the coordinator's done-callback (`_handle_task_result`) classifies the exception and starts `_async_reconnect` as a background task. Reconnect uses exponential backoff (1s → 300s). After a successful reconnect, the full connection lifecycle runs again.

**What recovers automatically:**

| State | Mechanism |
|---|---|
| Entity states (all UUIDs) | Miniserver sends full state dump after `CMD_ENABLE_UPDATES`. Dispatcher routes to each entity's `event_handler`. |
| Device registry | `miniserver.async_update_device_registry()` called explicitly on reconnect. |
| Structure file | Re-downloaded in `api.open()` on every reconnect. |
| Token | Fresh token requested or existing token re-authenticated. `_check_and_refresh_token` restarts. |
| Bridges (HA ↔ Loxone) | Dispatcher subscriptions remain active; state updates flow through normally. |

**What needs explicit re-triggering (via `_reconnected` signal):**

| State | Why it needs re-triggering |
|---|---|
| LightControllerV2 scenes | `gen_scenes()` queries `entity.effect_list` which is populated by mood events in the state dump. Scenes must be generated *after* moods arrive, not at reconnect time. |

**What is intentionally one-time:**

| State | Reason |
|---|---|
| Group creation | Depends on HA entity IDs, not live Miniserver data. |
| Area/device auto-sync | Run once at initial setup; user can re-run manually via service. |

### The `_reconnected` Dispatcher Signal

Signal name: `loxone_{entry_id}_reconnected`

**Who fires it:** `LoxoneCoordinator` — after both initial `async_start_listening()` (in `__init__.py`) and after every successful reconnect (in `_async_reconnect`).

**Who subscribes:** Platform `async_setup_entry` functions that need to perform one-time-per-session work requiring live Miniserver data. Currently: `scene.py`.

**Contract:**
- The signal fires on the event loop (from a `@callback` context or equivalent).
- At signal time, the connection is established but the state dump may not have arrived yet. Subscribers that depend on state dump data must impose their own delay.
- Subscribers register with `async_dispatcher_connect` and deregister via `config_entry.async_on_unload`.
- `gen_scenes()` uses the entity registry to deduplicate — calling it multiple times is idempotent.

**Pattern for new subscribers:**

```python
# In async_setup_entry:
@callback
def _on_connected() -> None:
    hass.async_create_task(_do_work_after_state_dump())

config_entry.async_on_unload(
    async_dispatcher_connect(hass, f"loxone_{entry_id}_reconnected", _on_connected)
)
```

### Command Flow (User → Miniserver)

```
User action (HA UI / automation / service call)
    │
    ▼
Entity.async_turn_on() / etc.
    │  Fires hass.bus event
    ▼
hass.bus → "loxone_send"
    │
    ▼
loxone_send() listener                 [__init__.py]
    │
    ▼
api.send_websocket_command(uuid, value)
    │  AES-encrypted WebSocket message
    ▼
Loxone Miniserver
```

### Bridge Sync Flow

Device bridges are bidirectional only when the mapper has both an HA → Loxone command path and one or more Loxone state UUIDs to subscribe to. The runtime keeps direction-aware state so feedback loops settle instead of ping-ponging.

```
Loxone app / logic
    │
    ▼
WebSocket state UUID
    │
    ▼
BridgeRuntime._make_lox_listener()
    │  normalize + duplicate/echo checks
    ▼
BridgeMapper.loxone_value_to_ha()
    │  HA service call
    ▼
HA entity state change
    │
    ▼
BridgeRuntime._process_ha_state()
    │  suppress if caused by Loxone, or if it matches last received value
    ▼
api.send_websocket_command()
```

For HA-originated changes the same runtime records the normalized command value, enables echo suppression, and sends the Loxone command. A following Loxone event is suppressed only if it semantically matches that command. Color bridges compare normalized HSV/temp values with tolerances, because Hue/Loxone round-trips can shift color values slightly.

The bridge runtime also clears pending cooldown commands when a Loxone-originated update arrives. This prevents an older HA state from being flushed after the user has already changed the device from the Loxone app.

## Supported Loxone Control Types

| Loxone Control       | HA Platform          | Entity Class                    |
|----------------------|----------------------|---------------------------------|
| InfoOnlyAnalog       | `sensor`             | `LoxoneSensor`                  |
| InfoOnlyDigital      | `sensor`             | `LoxoneSensor`                  |
| Meter                | `sensor`             | `LoxoneMeterSensor`             |
| TextInput            | `sensor` / `text`    | `LoxoneTextSensor` / `LoxoneText` |
| Switch               | `switch`             | `LoxoneSwitch`                  |
| TimedSwitch          | `switch`             | `LoxoneTimedSwitch`             |
| Intercom             | `switch`             | `LoxoneIntercomSubControl`      |
| Pushbutton           | `button`             | `LoxoneButton`                  |
| Jalousie             | `cover`              | `LoxoneJalousie`                |
| Gate                 | `cover`              | `LoxoneGate`                    |
| Window               | `cover`              | `LoxoneWindow`                  |
| LightControllerV2   | `light`              | `LoxoneLightControllerV2`       |
| Dimmer / EIBDimmer   | `light`              | `LoxoneDimmer` / `EIBDimmer`    |
| ColorPickerV2        | `light`              | `RGB/TunableWhite/LumiTech`     |
| IRoomControllerV2    | `climate`            | `LoxoneRoomControllerV2`        |
| IRoomController      | `climate`            | `LoxoneRoomController`          |
| AcControl            | `climate`            | `LoxoneAcControl`               |
| Ventilation          | `fan`                | `LoxoneVentilation`             |
| Alarm                | `alarm_control_panel`| `LoxoneAlarm`                   |
| AudioZoneV2          | `media_player`       | `LoxoneAudioZoneV2`             |
| Slider               | `number`             | `LoxoneNumber`                  |

## Scene platform (`scene.py`)

LightControllerV2 moods are exposed as `LoxoneLightScene` (Home Assistant `Scene` — not a `LoxoneEntity` subclass). Scenes define `device_info` and pass `entry_id` as `miniserver` in `SENDDOMAIN` payloads so commands target the correct config entry on multi-Miniserver setups.

## Authentication & Encryption

The integration uses Loxone's token-based authentication over WebSocket:

1. **Initial handshake** — HTTP fetches the Miniserver's RSA public key
2. **Key exchange** — Client generates a random AES-256 key + IV, RSA-encrypts it, sends over WS
3. **User auth** — HMAC-SHA256 of `username:password` with a server-provided salt
4. **Token request** — Server issues a time-limited token (permission level 2)
5. **Token refresh** — Background task refreshes before expiry
6. **Message encryption** — All subsequent WS commands are AES-256-CBC encrypted

## Configuration

The integration uses HA's config flow (no YAML entity config).

Validates credentials via HTTP before entry creation. Also supports `async_step_reauth` (triggered on auth failure), `async_step_reconfigure` (change connection settings from integration menu), and `async_step_dhcp` (auto-discovery via MAC prefix 504F94).

Key options:

| Option                             | Default | Purpose                                   |
|------------------------------------|---------|-------------------------------------------|
| `host`                             | —       | Miniserver IP/hostname                    |
| `port`                             | 8080    | Miniserver port                           |
| `username`                         | —       | Miniserver credentials                    |
| `password`                         | —       | Miniserver credentials                    |
| `generate_scenes`                  | true    | Create scene entities from moods          |
| `generate_lightcontroller_subcontrols` | false | Create sub-entities for LightControllerV2 |

## Build & Development

- **No Python packaging** — no `setup.py` / `pyproject.toml`; this is a HA custom component
- **Linting** — Ruff (Python 3.13, line length 120)
- **Dev environment** — VS Code devcontainer with Home Assistant core
- **CI** — GitHub Actions: hassfest validation, HACS validation
- **Tests** — `pytest-homeassistant-custom-component` harness in `tests/components/loxone/` with fixtures per platform
