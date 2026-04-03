# Issues, TODOs, and Improvements

> Consolidated findings from the full codebase review.
> Cross-references: [ARCHITECTURE.md](ARCHITECTURE.md) · [API_LAYER.md](API_LAYER.md) · [HA_INTEGRATION.md](HA_INTEGRATION.md) · [LIGHTS_SUBSYSTEM.md](LIGHTS_SUBSYSTEM.md)

---

## Critical Bugs

These will cause crashes or incorrect behavior for users.

### BUG-013: Ventilation sub-entities collide on unique_id with the fan entity

**File:** `fan.py` (lines 68-136)
**Impact:** When a Ventilation control has sub-entities (presence, humidity, air quality, temperature), all of them get their `uuidAction` overwritten to the parent fan's UUID via `parent_id`. Since `LoxoneEntity.unique_id` returns `self.uuidAction`, every sub-entity shares the same unique_id as the main fan entity. HA's entity registry rejects duplicates, so the **main fan entity is silently dropped** — only the sub-entities survive.

The root cause is twofold:
1. `LoxoneDigitalSensor.__init__` and `LoxoneSensor.__init__` both do `if self._parent_id: self.uuidAction = self._parent_id`, overwriting the originally distinct UUID
2. All entities (fan + sub-entities) are added through the fan platform's `async_add_entities` in a single list, so they share the same unique_id namespace

**Fix:** Sub-entities should use a composite unique_id (e.g. `f"{parent_uuid}_{suffix}"`) or keep their original `uuidAction` as the unique_id and store `parent_id` separately for device grouping only.

---

## High-Priority Improvements

### IMP-007: Fix sync/async inconsistencies

`hass.bus.fire()` is used throughout entity service methods (turn_on, turn_off, etc.) which may run in threads. Switching to `async_fire()` requires careful per-method analysis — sync methods must use thread-safe versions. `hass.loop.call_later()` in scene.py should be `async_call_later()`.

| Current (sync)               | Replace with (async)                          | Files                          |
| ---------------------------- | --------------------------------------------- | ------------------------------ |
| `hass.loop.call_later()`     | `async_call_later()` or `async_create_task()` | scene.py                       |

---

## Medium-Priority Issues

### MED-000: Text platform never loaded (dead code)

**File:** `const.py`, `text.py`

`Platform.TEXT` is missing from `LOXONE_PLATFORMS`. The `text.py` platform file exists but is never loaded. `LoxoneTextSensor` in `sensor.py` already handles TextInput, so this is dead code with a working alternative. Decide whether to wire up `text.py` (and remove the sensor overlap) or delete it.

### MED-002: Standalone `ColorPickerV2` never discovered

**File:** `light.py`

Only ColorPickerV2 subcontrols of LightControllerV2 are created. A standalone ColorPickerV2 control (not inside a LightControllerV2) will be silently ignored.

### MED-006: `LoxoneAlarm.code_arm_required` — Side effect in property

**File:** `alarm_control_panel.py`

The property getter mutates `self._code`. Properties should be side-effect-free.

### MED-010: `LoxoneAudioZoneV2` — `async_media_stop` sends pause

**File:** `media_player.py`

`async_media_stop()` sends `"pause"` instead of an actual stop command. If Loxone has a distinct stop command, it should be used.

### MED-013: `send_websocket_command` has no connection state check

**File:** `pyloxone_api/connection.py` (`send_websocket_command`, line ~1099)
**Impact:** Commands queue silently during disconnects; may flood Miniserver on reconnect

`send_websocket_command` validates the UUID parameter but does not check whether the WebSocket is connected before calling `_message_queue.put_nowait()`. During a disconnect, commands accumulate in the queue. When `_send_text_command` processes them, it logs a warning and attempts `self.connection.send()` anyway, which raises on a closed connection. The exception is caught, but the stale command is lost.

**Fix:** Check `is_connected` before enqueueing. Either raise immediately (caller can decide what to do) or log and discard. For the expose feature specifically, this matters because rapid state changes during a disconnect shouldn't flood the queue — only the latest value matters.

---

## Low-Priority / Cosmetic

| #       | Issue                                                        | File                                             |
| ------- | ------------------------------------------------------------ | ------------------------------------------------ |
| LOW-009 | Deprecated `DeviceInfo` import path                          | lights/dimmer.py, lights/lightcontroller.py      |
| LOW-010 | Inconsistent command casing `"on"`/`"off"` vs `"On"`/`"Off"` | lights/switch.py vs lights/dimmer.py             |

---

## Testing Strategy

### Current State

Test harness is in place using `pytest-homeassistant-custom-component==0.13.314` (HA 2026.2.1, Python >=3.13).

| File (tests)                      | What's covered                                                                                                                                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_helpers.py`                 | `map_range`, brightness conversions, color temp, `get_all`, `get_miniserver_type`, room/cat lookup, `get_or_create_device` cache behavior — all parametrized with edge cases |
| `test_config_flow.py`             | User step, entry title, port coercion, latin-1 validation (username + password), options flow                                                                       |
| `test_switch.py`                  | Entity creation, attributes, event→state (on/off), command dispatch (On/Off), no-op when already on, TimedSwitch delay attributes                                   |
| `test_cover.py`                   | Device class mapping (blind/curtain/garage/window), position inversion, tilt, opening/closing state, gate direction, commands (FullUp/FullDown/stop/manualPosition) |
| `test_climate.py`                 | AC entity creation, attributes, set temperature command, current/target temp events, HVAC mode mapping (off/heat/cool); IRoomControllerV2 creation, `is_overridden` JSON parsing |
| `test_init.py`                    | Setup, unload, services registered in `async_setup` (survive unload, raise when no coordinator), `sync_device_names` service (update/skip/ignore non-Loxone)         |
| `test_sensor.py`                  | InfoOnlyAnalog (creation, unit/format parsing, device_class matching, event updates), TextInput state, Meter subsensors (actual/total/totalReturned), energy dashboard attrs (device_class/state_class on totals + actual), fallback classification from details.type, version + keep-alive sensors |
| `test_binary_sensor.py`           | InfoOnlyDigital, PresenceDetector, SmokeAlarm entity creation; event state updates; correct `_state_uuid` selection per type                                         |
| `test_alarm_control_panel.py`     | Entity creation, alarm_state branching (disarmed/armed_away/armed_home/arming/triggered), priority logic, arm/disarm command dispatch, extra state attributes        |
| `test_fan.py`                     | Ventilation entity creation, supported features, preset modes, speed/mode events, set_percentage command                                                             |
| `test_number.py`                  | Slider entity creation, min/max/step properties, event state updates, set_native_value command                                                                       |
| `test_button.py`                  | Pushbutton entity creation, extra attributes, press sends pulse, event updates state, ignores unrelated events                                                       |
| `test_light.py`                   | LightControllerV2 creation, mood list JSON parsing (BUG-008 regression), effect commands; RGBColorPicker subcontrol creation, hsv/temp event parsing, None-guard turn_on (BUG-009) |
| `test_media_player.py`            | AudioZoneV2 entity creation, device class, supported features, playState events (playing/paused/idle), play/pause/next/prev/volume commands                          |
| `test_bridge.py`                  | DeviceBridge serialization, `_values_equal` helper, `get_mapper` factory, all BridgeMapper implementations (Dimmer, ColorPicker, LightSwitch, Switch, BinarySensor, Analog), BridgeRuntime lifecycle, entity suppression |
| `test_sync_areas.py`             | Device-level area assignment, entity override cleanup, create_areas flag, re-sync after area deletion, wrong-area device move, idempotency (BUG-015/BUG-016 regression) |
| `test_repairs.py`                | Token error triggers reconnect, auth failure creates repair + reauth, successful reconnect clears repair issues (namespaced by entry_id)                                |
| `test_structure_poll.py`         | Structure change detection, no-change noop, HTTP error resilience, skip-when-disconnected                                                                                |

Infrastructure:

| File                        | Purpose                                                                                                                                                          |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `conftest.py` (component)   | `mock_config_entry`, `mock_loxone_connection`, `init_integration` fixtures; `structure_fixture_name` override                                                    |
| `fixtures/structure_*.json` | `structure_minimal.json`, `structure_switches.json`, `structure_covers.json`, `structure_climate.json`, `structure_sensors.json`, `structure_binary_sensors.json`, `structure_alarm.json`, `structure_fan.json`, `structure_numbers.json`, `structure_buttons.json`, `structure_lights.json`, `structure_media_player.json` |
| `conftest.py` (root)        | Minimal root conftest (kept empty; `auto_enable_custom_integrations` lives in the component conftest)                                                            |
| `pyproject.toml`            | pytest config (`asyncio_mode = auto`)                                                                                                                            |
| `requirements_test.txt`     | Test dependencies                                                                                                                                                |

Additional test tracks:

| File / Directory                        | Purpose                                                                                                                                         |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_structure_dumps.py`               | Parametrized unit tests over real Miniserver structure dumps in `fixtures/dumps/`. Golden-file expectations ensure backwards compatibility.      |
| `known_types.py`                        | Shared mapping of Loxone control/subcontrol types to HA platforms, used by both dump tests and e2e tests.                                       |
| `fixtures/dumps/*.json`                 | Real `LoxAPP3.json` snapshots captured with `scripts/dump_miniserver`. Each has a companion `_expected.json` with entity counts.                |
| `tests_e2e_miniserver/test_miniserver.py` | E2E tests against a real Miniserver (no HA needed): connection, structure, WebSocket, command round-trip, snapshot.                            |
| `tests_e2e_miniserver/test_discover.py` | UDP broadcast discovery test (requires live Miniserver on LAN). Moved from legacy `pyloxone_api/tests/`.                                        |
| `tests_e2e_miniserver/conftest.py`      | Session-scoped fixtures for live Miniserver connection (credentials from env vars or `.env`).                                                    |
| `scripts/dump_miniserver`               | Script to fetch `LoxAPP3.json` from a real Miniserver and save it as a dump fixture with auto-generated expectations.                           |

No CI test jobs yet.

### How HA Integrations Do Testing

The Home Assistant ecosystem has a well-established testing pattern. Reference integrations to study:

- **WLED** — platinum quality, tests for every platform, snapshot testing, JSON fixtures
- **Hue** — complex multi-device, versioned API (v1/v2), extensive mocking
- **deCONZ** — WebSocket + REST, good model for event-driven integrations like PyLoxone

#### Core Infrastructure

| Component                                                                                                        | Purpose                                                                                                                                                            |
| ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`pytest-homeassistant-custom-component`](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) | Extracts HA's test fixtures for custom component use. Provides `hass` instance, `MockConfigEntry`, `async_fire_time_changed`, `load_json_object_fixture`, and more |
| `conftest.py` (root)                                                                                             | Enables custom integrations, provides component-specific fixtures                                                                                                  |
| `conftest.py` (per-component)                                                                                    | Mocked clients, config entries, `init_integration` fixture                                                                                                         |
| JSON fixture files                                                                                               | Recorded API responses stored as `.json` files in `tests/fixtures/`                                                                                                |
| Snapshot testing (`syrupy`)                                                                                      | Assert entity states against stored snapshots                                                                                                                      |

#### Standard Test File Structure (what HA core expects)

```
tests/
├── __init__.py
├── conftest.py                  # Root: auto_enable_custom_integrations
├── components/
│   └── loxone/
│       ├── __init__.py
│       ├── conftest.py          # Mock API client, config entry, init fixture
│       ├── fixtures/            # JSON fixtures (LoxAPP3.json snippets, WS messages)
│       │   ├── structure_minimal.json
│       │   ├── structure_lights.json
│       │   └── ws_value_states.bin
│       ├── test_init.py         # Setup, unload, migration, services
│       ├── test_config_flow.py  # Config + options flow
│       ├── test_sensor.py       # Sensor entity tests
│       ├── test_binary_sensor.py
│       ├── test_switch.py
│       ├── test_cover.py
│       ├── test_climate.py
│       ├── test_light.py
│       ├── test_fan.py
│       ├── test_alarm_control_panel.py
│       ├── test_media_player.py
│       ├── test_number.py
│       ├── test_button.py
│       ├── test_scene.py
│       └── test_diagnostics.py
```

**For `pyloxone_api` (pure Python, no HA dependency):**

Future unit tests for the API layer would live in `tests/pyloxone_api/` (outside `custom_components/`). The legacy `custom_components/loxone/pyloxone_api/tests/` directory has been removed. Potential test files:

```
tests/pyloxone_api/
├── __init__.py
├── conftest.py              # Shared fixtures for API tests
├── test_message.py          # Message parsing (all types)
├── test_token.py            # Token expiry, salt
├── test_http_client.py      # HTTP error mapping, auth
├── test_connection.py       # Key exchange, auth flow (mocked WS)
└── fixtures/                # Binary WS messages, HTTP responses
```

#### Key Pattern: The `conftest.py` Stack

**Root `tests/conftest.py`** — enables custom integrations:

```python
import pytest

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all tests."""
    yield
```

**Component `tests/components/loxone/conftest.py`** — mocks the API layer:

```python
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from homeassistant.core import HomeAssistant
from tests.common import MockConfigEntry, load_json_object_fixture

MOCK_CONFIG = {
    "host": "192.168.1.100",
    "port": 8080,
    "username": "admin",
    "password": "password",
}

@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain="loxone",
        data=MOCK_CONFIG,
        unique_id="504f94a0fea2",
        version=3,
    )

@pytest.fixture
def structure_fixture() -> str:
    return "structure_minimal"

@pytest.fixture
def mock_loxone_api(structure_fixture):
    """Mock the LoxoneConnection."""
    with patch(
        "custom_components.loxone.coordinator.LoxoneConnection",
        autospec=True,
    ) as mock_cls:
        api = mock_cls.return_value
        api.open = AsyncMock()
        api.close = AsyncMock()
        api.start_listening = AsyncMock()
        api.send_websocket_command = AsyncMock()
        api.structure_file = load_json_object_fixture(
            f"{structure_fixture}.json", "loxone"
        )
        yield api

@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_api: MagicMock,
) -> MockConfigEntry:
    """Set up the Loxone integration for testing."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
```

#### Key Pattern: JSON Fixture Files

Instead of hardcoding Loxone structure data in tests, store trimmed versions of `LoxAPP3.json` as fixtures:

```json
// tests/components/loxone/fixtures/structure_minimal.json
{
  "msInfo": {
    "serialNr": "504F94A0FEA2",
    "msName": "Test Miniserver",
    "projectName": "Test",
    "swVersion": "14.5.12.7",
    "localUrl": "192.168.1.100",
    "tempUnit": 0
  },
  "rooms": {
    "0f1e2d3c-0000-0000-0000000000000000": {
      "name": "Living Room",
      "uuid": "0f1e2d3c-0000-0000-0000000000000000"
    }
  },
  "cats": {},
  "controls": {
    "1a2b3c4d-0000-0000-0000000000000000": {
      "name": "Test Switch",
      "type": "Switch",
      "uuidAction": "1a2b3c4d-0000-0000-0000000000000000",
      "room": "0f1e2d3c-0000-0000-0000000000000000",
      "cat": "",
      "states": { "active": "1a2b3c4d-0000-0000-0000000000000001" }
    }
  }
}
```

Create targeted fixture files per scenario: `structure_lights.json`, `structure_climate.json`, etc.

#### Key Pattern: Testing Entity State Updates

```python
# Example: test_switch.py
import pytest
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant

pytestmark = pytest.mark.usefixtures("init_integration")

async def test_switch_turn_on(hass: HomeAssistant, mock_loxone_api):
    """Test turning on a switch sends the correct WS command."""
    await hass.services.async_call(
        "switch", "turn_on",
        {"entity_id": "switch.test_switch"},
        blocking=True,
    )
    mock_loxone_api.send_websocket_command.assert_called_with(
        "1a2b3c4d-0000-0000-0000000000000000", "on"
    )

async def test_switch_state_update(hass: HomeAssistant):
    """Test switch state updates from WS event."""
    hass.bus.async_fire("loxone_event", {
        "1a2b3c4d-0000-0000-0000000000000001": 1.0,  # states.active UUID
    })
    await hass.async_block_till_done()

    state = hass.states.get("switch.test_switch")
    assert state.state == STATE_ON
```

### Required Dependencies

Add to `requirements.txt` (or a separate `requirements_test.txt`):

```
pytest
pytest-asyncio
pytest-homeassistant-custom-component
pytest-cov
syrupy
aioresponses
freezegun
```

### Required Configuration

**`pytest.ini`** (or `[tool.pytest.ini_options]` in `pyproject.toml`):

```ini
[pytest]
testpaths = tests
asyncio_mode = auto
markers =
    online: marks tests that require network access (deselect with '-m "not online"')
```

### CI Workflow

Add `.github/workflows/tests.yaml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements_test.txt
      - name: Run tests
        run: pytest --cov=custom_components/loxone -m "not online" -v
      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

### Test Plan (Priority Order)

#### Tier 1 — `pyloxone_api` Unit Tests (pure Python, no HA)

These test the API client in isolation. No HA fixtures needed — just plain pytest.

| Module                     | What to Test                                                                             | Approach                                        |
| -------------------------- | ---------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `message.py`               | Parse all 8 message types, malformed headers, encoding edge cases                        | Construct binary payloads, assert parsed fields |
| `loxone_token.py`          | Token expiry calculation, `valid_until=0`, negative values, `LxJsonKeySalt` parsing      | Direct instantiation, `freezegun` for time      |
| `loxone_http_client.py`    | Error code mapping (401→Unauthorized, 503→Unavailable, etc.), timeout, Basic Auth header | `aioresponses` to mock HTTP                     |
| `websocket_protocol.py`    | `recv_message()` header+payload combos, `_last_header=None` guard                        | Mock `ClientConnection`                         |
| `helpers.py` (integration) | `map_range`, `lox_to_hass`, `hass_to_lox`, `to_hass_color_temp`, `to_loxone_color_temp`  | Pure function tests, boundary values            |
| `discover.py`              | UDP broadcast/response parsing, timeout handling                                         | Mock `asyncio.DatagramTransport`                |

**Estimated effort:** 2–3 days. **Value:** High — these are the foundations everything else builds on, and they're fast to run.

#### Tier 2 — Config Flow & Init Tests (needs HA fixtures)

| Component               | What to Test                                                         | Approach                                |
| ----------------------- | -------------------------------------------------------------------- | --------------------------------------- |
| `config_flow.py`        | User step with valid/invalid input, Latin-1 validation, options flow | `hass.config_entries.flow.async_init()` |
| `__init__.py` setup     | `async_setup_entry` with mocked API, platform forwarding             | `init_integration` fixture              |
| `__init__.py` unload    | `async_unload_entry` cleanup                                         | Verify listeners removed                |
| `__init__.py` migration | v1→v2→v3 config migration paths                                      | `MockConfigEntry` with old versions     |
| `__init__.py` services  | `event_websocket_command`, `sync_areas`, `reload`                    | Service call assertions                 |

**Estimated effort:** 2–3 days. **Value:** High — config flow is the first user touchpoint.

#### Tier 3 — Platform Entity Tests (needs HA fixtures + structure fixtures)

| Platform              | Key Scenarios                                                                    |
| --------------------- | -------------------------------------------------------------------------------- |
| `sensor`              | InfoOnlyAnalog state updates, format string → unit mapping, Meter subsensors     |
| `binary_sensor`       | InfoOnlyDigital, Presence, Smoke — state changes, device class                   |
| `switch`              | Turn on/off → correct WS command, TimedSwitch duration, Intercom                 |
| `cover`               | Gate/Window/Jalousie — position, tilt, sun automation service calls              |
| `light`               | Dimmer brightness mapping, ColorPicker HSV/temp parsing, LightControllerV2 moods |
| `climate`             | RoomControllerV2 modes, AcControl temperature (verifies BUG-001 fix)             |
| `fan`                 | Ventilation speed, subsensor creation                                            |
| `alarm_control_panel` | Arm/disarm, code handling                                                        |
| `media_player`        | AudioZoneV2 play state mapping, volume, source                                   |
| `number`              | Slider min/max/step, value mapping                                               |
| `button`              | Pushbutton press → WS command                                                    |
| `diagnostics`         | Returns structure file data                                                      |

**Estimated effort:** 1 week. **Value:** Medium-high — catches regressions in entity behavior.

#### Tier 4 — Connection Integration Tests (mocked WS)

| Scenario       | What to Test                                                      |
| -------------- | ----------------------------------------------------------------- |
| Happy path     | `open()` → HTTP setup → WS connect → key exchange → auth → listen |
| Auth failure   | Wrong credentials → `LoxoneUnauthorisedError`                     |
| Reconnect      | WS disconnect → automatic reconnect with backoff                  |
| Token refresh  | Token approaching expiry → refresh request                        |
| Out of service | `MessageType.OUT_OF_SERVICE` → graceful handling                  |
| Keep-alive     | Periodic keepalive sent, timeout detection                        |

**Estimated effort:** 3–5 days. **Value:** Medium — complex to set up but critical for reliability.

### Quick Start: First Test to Write

The lowest-friction starting point is `helpers.py` — pure functions with no dependencies:

```python
# tests/components/loxone/test_helpers.py
from custom_components.loxone.helpers import (
    lox_to_hass, hass_to_lox, map_range,
    to_hass_color_temp, to_loxone_color_temp,
)

def test_lox_to_hass_zero():
    assert lox_to_hass(0) == 0

def test_lox_to_hass_hundred():
    assert lox_to_hass(100) == 255

def test_hass_to_lox_roundtrip():
    for lox_val in range(0, 101):
        assert hass_to_lox(lox_to_hass(lox_val)) == pytest.approx(lox_val, abs=1)

def test_map_range():
    assert map_range(50, 0, 100, 0, 255) == 127.5

def test_color_temp_roundtrip():
    for kelvin in [2000, 3000, 4000, 5000, 6500]:
        result = to_hass_color_temp(to_loxone_color_temp(kelvin))
        assert result == pytest.approx(kelvin, abs=10)
```

Then progress to `message.py` parsing, then config flow, then entity platforms.

---

## Architectural Improvements (Long-term)

### ARCH-001: Separate `pyloxone_api` into its own package

The API client is already quasi-independent. Making it a proper Python package with `pyproject.toml` would:

- Enable independent versioning and releases
- Allow other projects to use the Loxone API without HA
- Enable proper CI/CD with its own test suite
- Clean up the nested directory structure

### ARCH-002: Use `DataUpdateCoordinator` properly or replace

The coordinator currently only manages the connection — `_async_update_data` is a no-op. Either:

- Use it for periodic polling of health/status
- Replace with a simple connection manager class
- Use HA's `async_setup_entry` lifecycle directly

### ARCH-004: Use entity descriptions

Modern HA integrations use `EntityDescription` dataclasses for entity metadata. Most platforms here define attributes inline in `__init__`. Migrating to `SensorEntityDescription`, `BinarySensorEntityDescription`, etc. would:

- Reduce boilerplate
- Make entity configuration declarative
- Align with HA best practices

### ARCH-006: Add config entry migration tests

`async_migrate_entry` handles v1→v2→v3 migrations but there are no tests for these migration paths.

### ARCH-008: Firmware update entity (`UpdateEntity`)

Surface the Miniserver firmware version as an HA `UpdateEntity` (Settings > Updates). `installed_version` is already available from the API key response. The blocker is `latest_version` — Loxone has no stable public API for checking available firmware. Options: scrape the changelog page (brittle), poll `update.loxone.com` (undocumented), or wait for Loxone to expose an API. Revisit when a reliable source for latest firmware version becomes available.

---

## Quick Wins

Tasks that can be done in under 30 minutes each:

| #   | Task                                                                                         | Impact                                           |
| --- | -------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| 1   | Fix `kwargs["targetTemperature"]` → `kwargs[ATTR_TEMPERATURE]` in climate.py                 | Fixes AC temperature control                     |
| 2   | Add `Platform.TEXT` to `LOXONE_PLATFORMS`                                                    | Enables text platform                            |
| 7   | Add `None` guard for `_last_header` in websocket_protocol.py                                 | Prevent crash                                    |
| 9   | Replace `eval()` with `ast.literal_eval()` where possible                                    | Security hardening                               |
| 10  | Fix copy-paste docstrings                                                                    | Code hygiene                                     |
| 11  | Remove unused imports (`cast`, `ToggleEntity`)                                               | Code hygiene                                     |
| 12  | Remove dead files (`helper.py`, `api.py`)                                                    | Reduce confusion                                 |
| 14  | Add missing `name`/`description` to all services in `services.yaml`                          | Proper service metadata for HA action validation |
