# PyLoxone Architecture

> Home Assistant custom integration for Loxone Miniserver

## Project Identity

| Key              | Value                                         |
|------------------|-----------------------------------------------|
| Domain           | `loxone`                                      |
| Version          | 0.9.12                                        |
| License          | Apache 2.0                                    |
| HA minimum       | 2025.2.4                                      |
| Installation     | HACS or manual copy of `custom_components/`   |
| IoT class        | `local_push`                                  |
| Runtime deps     | `websockets>=14`, `pycryptodome`, `httpx`     |

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
│  │  - Connection lifecycle                                       │     │
│  │  - MiniServer construction                                    │     │
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

```
1. User adds integration via config flow
2. async_setup_entry() creates LoxoneCoordinator
3. Coordinator calls api.open():
   a. HTTP GET → API key from Miniserver
   b. HTTP GET → LoxAPP3.json (structure file with all controls)
   c. HTTP GET → RSA public key
4. Coordinator builds MiniServer from structure file
5. Platforms forwarded → entities created from structure controls
6. api.start_listening() opens WebSocket:
   a. AES key exchange (RSA-encrypted)
   b. Token-based authentication
   c. Async listen loop begins
```

### Runtime Event Flow

```
Loxone Miniserver
    │
    │  WebSocket (binary/text)
    ▼
LoxoneConnection._listen()
    │  Parses header + payload via websocket_protocol
    ▼
message_callback()                     [__init__.py]
    │  Fires hass.bus event per UUID
    ▼
hass.bus → "loxone_event"
    │  Each entity filters by its UUID
    ▼
LoxoneEntity.event_handler()           [per-entity subclass]
    │  Updates internal state
    ▼
async_schedule_update_ha_state()       [HA core]
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

## Authentication & Encryption

The integration uses Loxone's token-based authentication over WebSocket:

1. **Initial handshake** — HTTP fetches the Miniserver's RSA public key
2. **Key exchange** — Client generates a random AES-256 key + IV, RSA-encrypts it, sends over WS
3. **User auth** — HMAC-SHA256 of `username:password` with a server-provided salt
4. **Token request** — Server issues a time-limited token (permission level 2)
5. **Token refresh** — Background task refreshes before expiry
6. **Message encryption** — All subsequent WS commands are AES-256-CBC encrypted

## Configuration

The integration uses HA's config flow (no YAML entity config). Key options:

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
