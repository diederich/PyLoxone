# Worklog

Session-by-session record of work done on PyLoxone. Newest first.

---

## 2026-03-30 — Architectural hardening (post-reconnect)

### Decisions

- Commands sent while the Miniserver is disconnected were silently dropped or caused unhandled exceptions. Added guarded `async_send_command` / `async_send_secured_command` methods to the coordinator — entity event bus sends log a warning, service calls raise `HomeAssistantError` with the connection state.
- On a large Miniserver, every coordinator update triggered `async_write_ha_state()` on every entity, even when availability didn't change. Added a `_prev_available` guard so state is only written when the flag actually flips.
- `stop_event` (on `EVENT_HOMEASSISTANT_STOP`) raced with `async_cleanup` (on entry unload) — both called `api.close()`, and token save could fail if the connection was already closed. Moved token save into `async_cleanup` and removed the redundant `stop_event` closure entirely.

### Changes

- **`coordinator.py`:** Added `async_send_command()`, `async_send_secured_command()` with connection state guard. Added `async_save_token()` call in `async_cleanup()` before `api.close()`.
- **`__init__.py`:** Updated `loxone_send` to use guarded coordinator methods. Added `ConnectionState` check to service handlers. Added `_prev_available` to `LoxoneEntity._handle_coordinator_update`. Removed `stop_event`, `EVENT_HOMEASSISTANT_STOP` listener/import.

### Test results

- 293 tests pass (no new tests needed — behaviour change is internal).

---

## 2026-03-30 — In-process reconnect and connectivity sensor

### Decisions

- Replaced the "reload entire integration on disconnect" architecture with in-process reconnect using exponential backoff (1s to 300s). Entities now survive disconnects and toggle `available` via the coordinator's `last_update_success`.
- Moved all connection lifecycle management (`message_callback`, `handle_task_result`, `start_event`, `stop_event`) from `async_setup_entry` closures into `LoxoneCoordinator` methods. This fixes the longstanding bug where `async_unload_entry` tried to cancel `coordinator._listening_task` that was never set.
- On disconnect, a new `LoxoneConnection` is created per reconnect attempt (avoids the `_closed = True` problem in `close()`). Structure file is re-fetched each time for consistency after Miniserver restarts.
- Added a gold-standard `BinarySensorDeviceClass.CONNECTIVITY` entity ("Connection") on the Miniserver device. It extends `CoordinatorEntity` and always reports `available=True` so users can see the disconnected state.
- All `LoxoneEntity` subclasses now register as coordinator listeners and report `available=False` when the Miniserver is disconnected.
- Closes ARCH-003 (entity availability).

### Changes

- **`coordinator.py`:** Complete rewrite. Added `ConnectionState` enum, `_create_api()`, `_handle_task_result()`, `_async_reconnect()` with backoff, `_message_callback()`, `async_start_listening()`, `async_save_token()`. `async_cleanup()` now cancels both `_listening_task` and `_reconnect_task`.
- **`__init__.py`:** Removed `websockets` import, `LoxoneConnection` import, and several exception imports no longer needed. Removed `_reload_after_delay`, `handle_task_result`, `message_callback`, `start_event` closures. Simplified `stop_event` to delegate to `coordinator.async_save_token()`. Simplified `async_unload_entry`. Added `available` property, `_register_coordinator_listener()`, and `_handle_coordinator_update()` to `LoxoneEntity`.
- **`binary_sensor.py`:** Added `LoxoneConnectivitySensor(CoordinatorEntity, BinarySensorEntity)` with `CONNECTIVITY` device class, `DIAGNOSTIC` category. Registered in `async_setup_entry`.
- **`sensor.py`:** Updated `LoxoneMiniserverInfoSensor.async_added_to_hass` to register coordinator listener for availability tracking.
- **`test_coordinator.py`:** New test file with 16 tests covering connectivity sensor creation/device link/availability, connection state tracking, reconnect logic (token error, cancel, shutdown guard), entity availability toggling, and cleanup during reconnect.

### Test results

- 293 tests pass (277 existing + 16 new coordinator/connectivity tests).

---

## 2026-03-30 — Tier 2: Miniserver diagnostic info sensors

### Decisions

- Added three new diagnostic sensors to the miniserver device: **Project name**, **Location** (with lat/lon/alt attributes), and **Connected user** (with is_admin attribute).
- Used a description-based pattern (`MiniserverSensorDescription` dataclass + `LoxoneMiniserverInfoSensor` class) for clean declarative sensor definitions — easy to extend with future miniserver sensors.
- Static sensors override `async_added_to_hass` to skip the event bus subscription (no runtime state changes).
- Sensors are only created when the corresponding `msInfo` field is present (graceful degradation).
- Disabled the software version sensor by default (`entity_registry_enabled_default = False`) since it duplicates `sw_version` on the device itself. Still available for users who want automations.

### Changes

- **`miniserver.py`:** Added properties: `project_name`, `location`, `latitude`, `longitude`, `altitude`, `current_user`.
- **`sensor.py`:** Added `MiniserverSensorDescription`, `MINISERVER_SENSOR_DESCRIPTIONS` (3 entries), `LoxoneMiniserverInfoSensor`. Added `_attr_entity_registry_enabled_default = False` to `LoxoneVersionSensor`. Updated `async_setup_entry` to iterate descriptions.
- **`structure_sensors.json`:** Added `location`, `latitude`, `longitude`, `altitude`, `currentUser` to `msInfo`.
- **`test_sensor.py`:** Added `test_project_name_sensor`, `test_location_sensor`, `test_connected_user_sensor`, `test_miniserver_sensors_missing_data`. Updated version sensor test to verify disabled-by-default behavior.

### Test results

- All 277 tests pass (20 sensor tests including 4 new).

---

## 2026-03-30 — Tier 1: Attach diagnostic sensors to miniserver device

### Decisions

- `LoxoneKeepAliveSensor` and `LoxoneVersionSensor` were orphaned entities (no `device_info`) because they lacked a `uuidAction`. They clearly belong to the miniserver device.
- Adopted gold-standard HA patterns: `has_entity_name = True` (entity name is a suffix to the device name), `entity_category = DIAGNOSTIC` (these are system-level info, not user-facing controls).
- Scoped `unique_id` to the miniserver serial (`{serial}_keep_alive`, `{serial}_software_version`) for multi-miniserver readiness.
- Updated icons: `mdi:heart-pulse` for keep-alive (heartbeat metaphor), `mdi:package-up` for software version (firmware).
- Entity names shortened from "Loxone Last Keep Alive Message" / "Loxone Software Version" to "Keep alive" / "Software version" — with `has_entity_name = True`, HA prepends the device name automatically.

### Changes

- **`sensor.py`:** Both classes now accept a `serial` parameter, set `_attr_has_entity_name = True`, `_attr_entity_category = EntityCategory.DIAGNOSTIC`, and override `device_info` to return `DeviceInfo(identifiers={(DOMAIN, serial)})`. `async_setup_entry` passes `miniserver.serial` to both constructors.
- **`test_sensor.py`:** Updated entity IDs to match new `has_entity_name` convention. Added `test_version_sensor_on_miniserver_device` and `test_keep_alive_sensor_on_miniserver_device` verifying device linkage, unique_id format, and entity_category.

### Test results

- All 273 tests pass (16 sensor tests including 2 new, plus full suite).

---

## 2026-03-30 — MED-012: Register services in async_setup

### Decisions

- Moved all domain-level services (`event_websocket_command`, `event_secured_websocket_command`, `sync_areas`, `sync_device_names`, `reload`) from `async_setup_entry` to `async_setup` so they exist regardless of whether the config entry has loaded.
- Service handlers now look up the coordinator lazily via `_get_coordinator(hass)` instead of closing over it at registration time. If no coordinator is available (Miniserver not connected), they raise `HomeAssistantError` with a clear message.
- Extracted `sync_areas_with_loxone` and `sync_device_names_from_structure` from nested closures to module-level functions (`_async_sync_areas`, `_async_sync_device_names`) since they only need `hass`.
- Removed service teardown from `async_unload_entry` — services now outlive individual config entries.

### Changes

- **`__init__.py`:** Added `_get_coordinator()`, `_async_sync_areas()`, `_async_sync_device_names()`, `_async_register_services()` as module-level functions. `async_setup` now calls `_async_register_services()` and initializes `hass.data[DOMAIN]`. Removed handler definitions and `hass.services.async_register` calls from `async_setup_entry`. Removed `hass.services.async_remove` calls from `async_unload_entry`.
- **`test_init.py`:** Added `test_services_registered_before_entry_setup`, `test_services_survive_entry_unload`, and `test_websocket_command_raises_when_no_coordinator`.
- **`ISSUES_AND_TODOS.md`:** Removed MED-012.

---

## 2026-03-29 — Sync Engine: auto-sync, config flow area option, connection validation

### Decisions

- Auto-sync (`sync_device_names` + `sync_areas`) runs automatically at the end of `async_setup_entry` so fresh installs get a fully organized device tree without manual service calls.
- Area creation (`create_areas`) is only honoured on the very first setup. A new config flow checkbox "Create HA areas from Loxone rooms" (default: true) controls this. After the first sync, an `initial_sync_done` flag is persisted in `config_entry.data`; subsequent restarts always use `create_areas=False` to avoid re-creating areas the user intentionally deleted.
- Connection validation added to config flow: a live HTTP test against `/jdev/cfg/apiKey` catches bad credentials or unreachable Miniservers before the entry is saved.
- Created `docs/SYNC_ENGINE.md` as the single source of truth for sync lifecycle documentation.

### Changes

- **`const.py`:** Added `CONF_CREATE_AREAS = "create_areas_on_setup"`.
- **`config_flow.py`:** Added `CONF_CREATE_AREAS` checkbox to `DATA_SCHEMA_SETUP` and `SETTINGS_SCHEMA`. Added live connection test in `validate_loxone_setup` using `aiohttp.BasicAuth` against the Miniserver.
- **`__init__.py`:** Auto-sync block at end of `async_setup_entry` checks `initial_sync_done` flag — first run uses user's `create_areas` preference, restarts use `False`. Persists `initial_sync_done` in entry data after first sync.
- **`translations/en.json`, `translations/de.json`:** Added labels for `create_areas_on_setup` and error messages (`cannot_connect`, `invalid_auth`, `unknown`).
- **`docs/SYNC_ENGINE.md`:** New doc covering sync lifecycle, auto-sync behavior, and first-run vs restart semantics.
- **`docs/ARCHITECTURE.md`, `docs/HA_INTEGRATION.md`, `AGENTS.md`:** Updated doc tables to include SYNC_ENGINE.md.
- **`docs/ISSUES_AND_TODOS.md`:** Removed IMP-003.
- **`tests/components/loxone/test_init.py`:** Added tests for auto-sync first-run area creation, `initial_sync_done` flag, opt-out behavior, and no-recreate-on-restart.
- **`tests/components/loxone/test_config_flow.py`:** Added tests for connection validation (invalid credentials, unreachable host, timeout). Updated `VALID_USER_INPUT` with new field.
- **`tests/components/loxone/conftest.py`:** Added `CONF_CREATE_AREAS` to `MOCK_OPTIONS`.

### Investigations

- HA's `suggested_area` in `DeviceInfo` auto-creates areas during platform setup, independent of our `sync_areas`. Tests for opt-out behavior must account for this by mocking `_async_sync_areas` and asserting call args rather than checking area registry state.

---

## 2026-03-29 — ARCH-005 / MED-011: Migrate to proper DeviceInfo

### Decisions

- Used `device_info` property on `LoxoneEntity` instead of per-entity `_attr_device_info` assignment, following modern HA pattern.
- `get_miniserver_from_hass(self.hass).serial` provides the `via_device` reference — no extra plumbing needed since `self.hass` is set before HA reads `device_info`.
- `_attr_device_info` override still honored (checked first in the property) for special cases like `LoxoneMeterSensor`.
- Light subcontrols override `device_info` to group under their parent `LightControllerV2` UUID.
- `device_info` kwarg key is skipped in `LoxoneEntity.__init__`'s generic setattr loop (it collides with the new property).

### Changes

- **`__init__.py`:** Added `device_info` property to `LoxoneEntity` returning `DeviceInfo` with `via_device` pointing to the Miniserver. Removed `helpers_device_registry` import and `.clear()` call from `async_unload_entry`. Added `DeviceInfo` import. Added `_SKIP_KWARGS` set.
- **`helpers.py`:** Removed `device_registry` dict, `get_or_create_device` function, and `DOMAIN` import.
- **14 platform files:** Removed all `get_or_create_device` imports and `_attr_device_info` assignments from `alarm_control_panel.py`, `binary_sensor.py`, `climate.py`, `cover.py`, `fan.py`, `media_player.py`, `number.py`, `sensor.py`, `switch.py`, `text.py`.
- **`button.py`:** Removed redundant custom `device_info` property (now inherited from base). Removed unused `DeviceInfo` import.
- **`lights/`:** Removed `get_or_create_device` from `lightcontroller.py`, `dimmer.py`, `switch.py`, `colorpickers.py`. Added `device_info` property overrides in subcontrol classes to group under parent light controller UUID.
- **`coordinator.py`:** Added `await self.miniserver.async_update_device_registry()` after `MiniServer` construction — this method existed but was never called, so the Miniserver device was never registered in HA.
- **`miniserver.py`:** Fixed `CONNECTION_NETWORK_MAC` to use `format_mac(self.serial)` instead of the IP address. Loxone serials are MAC addresses, so this lets HA auto-merge the Miniserver device with devices from other integrations (e.g. UniFi) that share the same MAC. Removed dead `CONNECTION_NETWORK_MAC` constant and commented-out code.
- **Tests:** Removed `TestGetOrCreateDevice` from `test_helpers.py`. Removed `test_unload_clears_helpers_device_registry` from `test_init.py`. Fixed `test_auto_sync_assigns_devices_to_areas_on_setup` to skip the Miniserver device (it has no room). Removed stale imports.
- **Docs:** Removed ARCH-005 and MED-011 from `ISSUES_AND_TODOS.md`.

---

## 2026-03-29 (fix 8) — Replace random tilt jitter with deterministic cycle

### Changes

- **MED-008:** `LoxoneJalousie` used `random.uniform()` to add a tiny offset to `manualLamelle` commands — a cache-busting trick so the Miniserver doesn't ignore repeated same-value commands. Replaced with `itertools.cycle([0.001, 0.002, 0.003, 0.004])` for deterministic, reproducible behavior. Added a comment explaining *why* the jitter exists. Also fixed `open_cover_tilt` docstring (said "Close" instead of "Open"). Removed `import random`.

---

## 2026-03-29 (fix 7) — Remove unused httpx dependency

### Changes

- **MED-007:** Removed `httpx` from `manifest.json` requirements — the codebase uses `aiohttp`, not `httpx`. Also removed the stale `warnings.filterwarnings` for `httpx._config` and a misleading comment in `connection.py`. Removed unused `import warnings`.

---

## 2026-03-29 (fix 6) — Fix __main__.py docstring argument order

### Changes

- **BUG-010:** Docstring said `username password host port` but code reads `host port username password`. The code order is correct (connection info first, credentials second) — fixed the docstring to match.

---

## 2026-03-29 — Fix sync_areas to operate at device level (other session)

### Changes

- **BUG-016:** `sync_areas` was assigning areas to individual entities, but HA entities inherit area from their parent device. Rewrote to group by device, assign via device registry, and clear stale entity-level overrides. (`9be41b0`)
- **BUG-015:** Also fixed the earlier issue where `sync_areas` never updated entities already assigned to an area (the `entry.area_id is None` guard was too strict). Subsumed into the device-level rewrite.
- Fixed deploy script to default to `--restart` since code changes require a full HA Core restart.

---

## 2026-03-29 — Clean up ISSUES_AND_TODOS convention

### Decisions

- Changed convention: completed items are now **removed** from ISSUES_AND_TODOS.md entirely (the worklog is the record of what was done). Previously they were kept struck-through, which added clutter.
- Updated AGENTS.md to reflect the new convention.

### Changes

- Removed all struck-through completed items from every section (Critical Bugs, High-Priority, Medium-Priority, Low-Priority, Architectural, Quick Wins).
- Removed "Completed" subsections and "Completed Quick Wins" table.
- Updated AGENTS.md ISSUES_AND_TODOS section with new rules.

---

## 2026-03-29 (fix 5) — Narrow bare except in message.py

### Changes

- **MED-003:** `clean_up_control()` used bare `except:` which catches `SystemExit`, `KeyboardInterrupt`, etc. Narrowed to `(TypeError, re.error)` — the only exceptions `re.sub` can raise on bad input — and added `_LOGGER.debug()`.

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
- BUG-007 (cover dispatcher `async_add_covers` unused): reclassified as not a bug — dead code, no change needed
- Identified entity duplication issue (controls registered via both `async_load_platform` loop and `async_setup_platform` stubs)
- Mapped complete light entity hierarchy: `LightControllerV2` → sub-controls (Switch, Dimmer, EIBDimmer, ColorPickerV2 with Rgb/LumiTech/TunableWhite picker types)
- Analyzed connection.py god object (1420 lines) and proposed decomposition
- Reviewed event bus broadcast pattern — O(entities × events) scaling issue documented
