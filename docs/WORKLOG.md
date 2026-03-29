# Worklog

Session-by-session record of work done on PyLoxone. Newest first.

---

## 2026-03-29 (fix 4) — Fix logger format strings in colorpickers

### Changes

- **MED-009 / Quick Win #5:** Two `_LOGGER.error("Not handled command ->", _color)` calls passed `_color` as a positional arg instead of using `%s` formatting — the value was silently dropped. Fixed both occurrences.

---

## 2026-03-29 (fix 3) — Fix masterColor filter in light subcontrol discovery

### Changes

- **MED-001 / Quick Win #6:** `sub_control_uuid.find("masterColor") > 1` only matched if "masterColor" appeared at string index 2+. Changed to `"masterColor" in sub_control_uuid`. Also simplified the adjacent `masterValue` check to use `in` for consistency.

---

## 2026-03-29 (fix 2) — Remove sys.exit(-1) from LoxoneEntity

### Changes

- **MED-004 / Quick Win #8:** Removed `sys.exit(-1)` from `LoxoneEntity.__init__` — an unhandled `setattr` exception would kill the entire HA process. Replaced with `_LOGGER.exception()`.
- Also fixed `_LOGGER.error` missing "not" ("Could set" → "Could not set") and switched to `%s` formatting.
- Removed now-unused `import sys` and `import traceback`.

---

## 2026-03-29 — Small fixes: fan feature flags, coordinator print, docstring

### Changes

- **BUG-014:** Added `FanEntityFeature.TURN_ON | TURN_OFF` to `LoxoneVentilation.supported_features` — without these flags, `fan.turn_on` / `fan.turn_off` services raise `ServiceNotSupported` in HA 2024.8+.
- **MED-005 / Quick Win #4:** Replaced `print("_async_update_data")` with `_LOGGER.debug(...)` in `coordinator.py`.
- **LOW-001 (partial):** Fixed copy-paste docstring in `fan.py` — was "Interfaces with Alarm.com alarm control panels", now describes Loxone Ventilation.
- Updated `test_fan.py` to assert `TURN_ON` and `TURN_OFF` feature flags.
- Marked BUG-014, MED-005, and Quick Win #4 as completed in ISSUES_AND_TODOS.md.

---

## 2026-03-16 (session 2) — Device Bridge: redesign sync → bridge

### Decisions

- The v1 "sync bindings" approach (VI/VO name-based, manual type selection, separate expose/subscribe directions) was too complex for users and would change entirely in v2 — scrapped before shipping.
- Adopted a device-level "bridge" model inspired by 1Home Loxone Server: one HA entity maps to one Loxone sub-control (e.g. a Hue light → a ColorPickerV2 RGB circuit inside a LightControllerV2).
- Loxone-side setup: create RGB/Dimmer/Switch circuits in LightControllerV2 in Loxone Config. The bridge auto-detects mapping type from the HA entity domain + Loxone control type.
- UI-first: no service API, all management via options flow menu.
- Entity suppression: when a Loxone sub-control is bridged, skip creating its native HA entity to avoid duplicates.
- RGBW/RGB/XY support: HA always derives `hs_color` for any color mode, so the mapper uses that instead of checking for specific modes.

### Changes

- **New:** `bridge.py` — `DeviceBridge` dataclass, `BridgeMapper` ABC, `BridgeRuntime` (lifecycle, cooldown, echo protection)
- **New:** `bridge_mappers.py` — `ColorPickerMapper`, `DimmerMapper`, `LightSwitchMapper`, `SwitchMapper`, `BinarySensorExposeMapper`, `AnalogExposeMapper`, `get_mapper` factory
- **Deleted:** `sync.py`, `test_sync.py`
- **Modified:** `__init__.py` — replaced `LoxoneSync` with `BridgeRuntime`
- **Modified:** `config_flow.py` — replaced sync menu/steps with bridge menu/steps, auto-detect control type from structure file
- **Modified:** `light.py`, `switch.py` — entity suppression for bridged sub-controls
- **Modified:** `services.yaml` — removed `sync`/`unsync` service definitions
- **Modified:** translations (`en.json`, `de.json`) — "Sync Bindings" → "Device Bridges"
- **New:** `test_bridge.py` — 50 tests covering mappers, runtime, suppression
- **Modified:** `test_config_flow.py` — replaced sync tests with bridge tests
- **Docs:** updated `ARCHITECTURE.md`, `HA_INTEGRATION.md`, `ISSUES_AND_TODOS.md`

### Investigations

- Studied how 1Home Loxone Server maps external devices to Loxone
- Explored LightControllerV2 sub-control types (RGB/Dimmer/Switch circuits) as bridge targets — virtual circuits can be created in Loxone Config
- Confirmed `jdev/sps/io/{uuid}/{value}` works for any control (visualized or not) for expose direction
- Confirmed subscribe direction works via WebSocket event table for sub-controls with state UUIDs
- Explored Loxone Config template generator for EP One sensors — deferred as follow-up
- Verified HA provides `hs_color` as a derived attribute for all color modes (RGBW, RGB, XY, RGBWW), so a single code path handles them all

---

## 2026-03-16 (session 1) — Sync feature (v1), bug fixes, discovery

### Decisions

- Built sync feature as HA → Loxone expose + Loxone → HA subscribe using VIs/VOs
- Added name-based resolution (`vi_name` + optional `room`) alongside direct UUID
- Designed bidirectional options flow UI with separate input/output dropdowns
- Added unicast discovery support using `.deploy.env` for directed Miniserver detection

### Changes

- `fb45387` — `sync.py` with `loxone.sync`/`loxone.unsync` services, cooldown, echo protection
- `f759945` — Options flow UI for sync bindings (add/remove/done menu)
- `1553be3` — Fix BUG-011: phantom service removals in `async_unload_entry`
- `363eb1a` — Directed (unicast) discovery with e2e tests
- `2ae37c3` — Fix BUG-005: narrow `async_load_platform` to sensor/binary_sensor only
- `d656252` — Clean up legacy `pyloxone_api/tests/`, fix discover socket conflict

### Investigations

- Studied KNX, MQTT, ZHA expose patterns for prior art
- Explored whether VIs need visualization to appear in the structure file (yes for subscribe/list, no for commands)
- Tested VI/VO state synchronization over WebSocket

---

## 2026-03-15 — Initial audit, docs, test harness, bug fixes

### Decisions

- Wrote full project documentation from scratch (architecture, API layer, HA integration, lights subsystem, issues/todos)
- Established test infrastructure using `pytest-homeassistant-custom-component`
- Adopted fixture-per-platform pattern with trimmed `LoxAPP3.json` snippets
- Created deploy script for remote HA machine with restart and reload modes
- Prioritized critical bugs for immediate fixes

### Changes

- `d866b0a` — Initial docs (`ARCHITECTURE.md`, `API_LAYER.md`, `HA_INTEGRATION.md`, `LIGHTS_SUBSYSTEM.md`, `ISSUES_AND_TODOS.md`)
- `c032d20` — Deploy script (`scripts/deploy`) with rsync + HA restart/reload
- `472e39a` — Fix manifest `iot_class` → `local_push`, add `services.yaml` metadata
- `4dec185` — Drop redundant "loxone" prefix from device names
- `8d5cebe` — Test harness: conftest, helpers, config flow, switch, cover tests
- `374f889` — Fix BUG-001: AC `set_temperature` KeyError
- `c97ee72` — `sync_device_names` service, fix cache staleness on reload
- `aafe62f` — Sensor, binary sensor, alarm tests; fix BUG-012 (`_state_uuid` selection)
- `d65621c` — Fan, number, button, media player tests
- `3ec4609` — Structure dump tests and e2e Miniserver tests
- `eb169fa` — Fix BUG-003: guard `None` `_last_header` in websocket protocol
- `07eea3f` — Fix BUG-006: correct binary sensor `NEW_SENSOR` typo
- `529ba8b` — Fix BUG-008: replace `eval()` with safe parsers
- `4d97811` — Fix BUG-009: guard `None` brightness/hs_color in `RGBColorPicker`
- `05910f7` — Light and climate tests covering BUG-008/009 fixes

### Investigations

- Full codebase audit: catalogued 15 bugs, 8 high-priority improvements, 12 medium-priority issues, 14 quick wins
- Identified entity duplication issue (controls registered via both `async_load_platform` loop and `async_setup_platform` stubs)
- Mapped complete light entity hierarchy: `LightControllerV2` → sub-controls (Switch, Dimmer, EIBDimmer, ColorPickerV2 with Rgb/LumiTech/TunableWhite picker types)
- Analyzed connection.py god object (1420 lines) and proposed decomposition
- Reviewed event bus broadcast pattern — O(entities × events) scaling issue documented
