# Worklog

Session-by-session record of work done on PyLoxone. Newest first.

---

## 2026-06-07 — Battery meter labels: Discharge / Charge instead of Total / Total Returned

Real-world bug uncovered by Stephan: his BYD HVB battery's `sensor.battery_total` and `sensor.battery_total_returned` had been wired to the wrong sources in the Home Assistant Energy Dashboard, leading to ~89% "Untracked Consumption". Root cause: Loxone's `total` / `totalNeg` semantic *flips* between meter types, and our meter sub-sensor mapping was meter-type-blind.

### Background

For a normal energy meter (consumer / bidirectional grid):

- `total` = imported (Bezug aus dem Netz)
- `totalNeg` = exported (Einspeisung)
- "Total" / "Total Returned" labels read naturally for an English user.

For a storage meter (`details.type == "storage"`, e.g. BYD HVB):

- `actual` is signed power: `+W = discharge`, `-W = charge` (matches HA / power-flow-card-plus convention).
- `total` accumulates **discharge** (Loxone variable `Mrd`).
- `totalNeg` accumulates **charge** (Loxone variable `Mrc`).
- `storage` is the battery state-of-charge in %.

An English reader looking at `sensor.battery_total_returned` parses "returned" as "given back to home" and wires it as `stat_energy_from` in the Energy Dashboard. That is the exact opposite of what `totalNeg` is for a battery (charge, energy going INTO the battery). The result is a fully reversed battery storage row in the dashboard, leading to nonsense energy balances.

Live evidence from Stephan's system at the time of investigation:

```
sensor.battery_total           = 13.41 kWh   (Mrd / discharge)
sensor.battery_total_returned  = 20.73 kWh   (Mrc / charge)
sensor.battery_actual          =  0.007 kW   (positive: ~7 W standby discharge at 99.3% SoC)
sensor.battery_level           = 99.3 %      (device_class was empty!)
```

`Mrc > Mrd` is consistent with round-trip losses (more energy goes in than comes out over time), confirming the empirical interpretation.

### Decisions

- **Meter-type-aware sub-sensor layout.** Replace the single hard-coded tuple list in `async_setup_entry` with a small `_meter_state_layout(meter_type)` helper that returns `(_METER_LAYOUT_DEFAULT or _METER_LAYOUT_STORAGE)`. Only storage diverges today; future meter types (`water` / `gas` rename, custom Loxone meter variants, ...) can land as additional branches without touching the call site.
- **Storage labels: "Discharge energy" / "Charge energy" / "Battery level".** Picked over "Energy out / Energy in" because the discharge/charge terminology matches the rest of the HA battery ecosystem (Tesla, Sonnen, BYD HVB native integration). "Battery level" matches what HA Lovelace badges already say for the BATTERY device class.
- **`actual` stays "Actual".** Loxone's sign convention (positive = discharge) already matches HA's common convention for battery power sensors. Power-flow cards just work; the Energy Dashboard doesn't use `actual` directly (only the total / totalNeg counters). No label problem; rename would just be cosmetic. Decision and rationale walked through in-thread before implementation.
- **Add `"storage"` to `_METER_CLASSIFICATION` and `_METER_EXPECTED_CLASSES`.** Bonus side-effect: `sensor.battery_level` finally gets `device_class=battery` even when its Loxone-side name isn't one of the `battery / batt / akku` keywords used by `match_sensor_description`. The fallback classification also makes the format/type mismatch repair issue cover storage meters from now on.
- **One-shot Repair issue for legacy installs, fresh installs see nothing.** Asked the user explicitly between `warn_only_legacy`, `warn_always`, `fixable_rename`. `fixable_rename` is dangerous (auto-renaming entity IDs breaks user automations / Lovelace cards / template sensors silently). `warn_always` would spam fresh installs unnecessarily. `warn_only_legacy` triggers only when we can prove via the entity registry that the user installed before the relabel (entity for `state.total` UUID exists with `_total` slug, ditto for `totalNeg` with `_total_returned`). One issue per meter, dismissable, deduplicated by meter UUID across restarts.
- **Don't auto-rename entity IDs.** HA freezes the entity_id slug at first registration. Changing `translation_key` only updates the friendly name. Entity IDs stay (e.g. `sensor.battery_total` remains, now reading "BYD HVB Discharge energy"). This preserves long-term statistics history (recorder keys by unique_id, which is UUID-based here) and doesn't break any existing automation / Lovelace card / template sensor referencing the old entity_id. The Repair issue tells the user the IDs themselves are unchanged.
- **Single commit for clean upstream PR.** Upstream `JoDehli/PyLoxone` uses `_attr_name = "Total Neg"` (no translation keys); the equivalent upstream patch is a smaller cherry-pick of the layout helper + classification + repair issue with English labels inlined. Doing a separate upstream PR after this lands and we've verified on the live system.

### Changes

- `custom_components/loxone/sensor.py`:
  - new `_METER_LAYOUT_DEFAULT` and `_METER_LAYOUT_STORAGE` constants;
  - new `_meter_state_layout(meter_type)` returning the per-type sub-sensor table;
  - meter loop in `async_setup_entry` switched to `_meter_state_layout(meter_type)`;
  - new `"storage"` entry in `_METER_CLASSIFICATION` (POWER/W, ENERGY/kWh × 2, BATTERY/%);
  - `_METER_EXPECTED_CLASSES["storage"] = {POWER, ENERGY, BATTERY}` so the unit-mismatch repair check applies to storage too;
  - new `_LEGACY_STORAGE_TOTAL_SUFFIXES` + `_maybe_create_storage_legacy_repair(hass, meter=...)` helper;
  - meter loop invokes the helper once per storage meter, before sub-sensors are constructed;
  - import of `entity_registry as er` added.
- `custom_components/loxone/translations/en.json` + `de.json`:
  - new entity-name keys `meter_storage_discharge`, `meter_storage_charge`, `meter_storage_level`;
  - new issue key `meter_storage_legacy_labels` with full description spelling out the entity-IDs-and-mapping advice.
- `custom_components/loxone/icons.json`: new entries for the three storage sub-sensor keys (`mdi:battery-arrow-up-outline`, `mdi:battery-arrow-down-outline`, `mdi:battery`).
- `tests/components/loxone/fixtures/structure_meter_storage.json` (new): single BYD-HVB-shaped storage meter with `details.type="storage"` and the four states (`actual`/`total`/`totalNeg`/`storage`) wired to plausible format strings.
- `tests/components/loxone/test_meter_storage.py` (new, 10 tests):
  - `TestMeterStateLayout` (3 pure-unit tests) — storage layout uses the new translation keys, energy layout unchanged, unknown type falls back to default.
  - 7 integration tests: storage sub-sensors registered with correct translation_keys; discharge/charge sub-sensors carry ENERGY + TOTAL_INCREASING + kWh; storage sub-sensor carries BATTERY + MEASUREMENT + %; `actual` stays POWER + W; no repair issue on fresh install; repair issue created with correct placeholders when legacy `..._total` / `..._total_returned` entities pre-exist in the registry.
- `docs/HA_INTEGRATION.md`: new paragraph in the `sensor.py` section describing `_meter_state_layout`, the storage-classification entry, and the legacy-install Repair flow.
- `docs/WORKLOG.md`: this entry.

### Testplan

- `python -m pytest tests/ -q --tb=short` -> 517 passed in ~55s (was 507 -> +10).
- `python -m ruff check custom_components/loxone tests/components/loxone` -> All checks passed.
- Live: deploy via `scripts/deploy`, verify on the live HA via `/api/states` and the Repairs panel:
  - `sensor.battery_total` keeps its entity_id, friendly name now "BYD HVB Discharge energy", unit still `kWh`, `device_class=energy`, `state_class=total_increasing` (statistics history intact).
  - `sensor.battery_total_returned` symmetric -> "BYD HVB Charge energy".
  - `sensor.battery_level` now reports `device_class=battery`, unit `%`.
  - One Repair issue `meter_storage_legacy_labels_<bydhvb_uuid>` shows up in Settings -> System -> Repairs with the actual entity IDs in the description.

---

## 2026-06-04 — Group PowerUnit sub-meters via `via_device` and expose PowerUnit headline states

After [the 2026-05-26 fix](#2026-05-26--discover-meter-subcontrols-of-powerunit-energy-flow-monitor) made the 8 sub-meters of `Power Supply & Backup` discoverable in HA, the user pointed out that they showed up as 8 independent meter devices instead of being visually grouped under the parent PowerUnit. The `PowerUnit`'s own states (`outputPower`, `batteryStateOfCharge`, `supplyTimeRemaining`, `fuse`, `CP1..CP7`, `deviceInfo`) were also still unused. This session does the "premium Loxone/HA" treatment of the whole block.

### Decisions

- **`via_device` over single-device collapse.** Two options for grouping: (a) each sub-meter stays its own device but is linked to the `PowerUnit` via HA's `via_device` (the device entry the integration creates for the PowerUnit itself), or (b) all sub-meter sensors collapse onto one giant device card. (a) wins because HA's nested device hierarchy is the canonical pattern (e.g. Shelly Pro 3EM phase devices, Sonnen battery sub-modules) and keeps each sub-meter's existing 2–3 sensor card clean. The user explicitly chose this, and on reflection the alternative would have meant ~24 sensors on a single device, which is unreadable.
- **Headline sensors vs everything-equally.** The pushback in-thread: surface `outputPower`, `batteryStateOfCharge`, `supplyTimeRemaining` as enabled headline sensors; `deviceInfo` as DIAGNOSTIC + disabled-by-default (text dump, debug only); `fuse` as DIAGNOSTIC + enabled (a blown main fuse is actionable); `CP1..CP7` as DIAGNOSTIC + disabled-by-default (cryptic per-circuit labels with no Loxone-side names — exposing them on by default would be noise for the 95% of users who never care). Users who *do* care can enable them per-need.
- **Inverted `problem` semantics for fuse + CP\*.** Loxone reports `1=OK / 0=tripped` for protection states. We map this to `BinarySensorDeviceClass.PROBLEM` with `on_when=0.0` so the entity is *on* when there's a problem — matching the HA convention and letting users plug straight into alerts.
- **`DURATION` + seconds for `supplyTimeRemaining`.** Loxone reports raw seconds; HA's `SensorDeviceClass.DURATION` auto-formats to a human-readable string (`1:23:45`) in the UI, so no need to convert to minutes/hours on our side.
- **Pre-register the PowerUnit parent device before adding entities.** Critical bug found via the via_device test: HA's device registry silently drops `via_device` if the parent device isn't yet in the registry at entity-registration time. Fix: at the top of `sensor.async_setup_entry`, walk all `PowerUnit` controls and call `dr.async_get_or_create(**create_power_unit_device_info(power_unit))` before iterating meters. The PowerUnit sensor entities later attach to the same device entry via shared identifiers.
- **Single shared `create_power_unit_device_info(power_unit)` helper.** Both `sensor.py` and `binary_sensor.py` need to register child entities on the same parent device. Sharing the constructor (rather than duplicating the `DeviceInfo` literal) guarantees identical identifiers / name / model and means changes to the parent device representation happen in one place.
- **`get_all_including_subcontrols(..., with_parent=True)` over a side-channel.** To know whether a discovered meter is a subcontrol (and of what), the helper now optionally returns `(control, parent_or_None)` tuples. Default behaviour is unchanged (flat `list[dict]`) so existing callers stay on the simple signature. Alternative considered: annotate the subcontrol dict with a hidden key like `_parent_uuid` via `setdefault` — rejected as it pollutes the structure dict in a way the rest of the integration can't see.
- **`PowerUnit` mapped to `sensor` in `KNOWN_CONTROL_TYPES`, even though it also uses `binary_sensor`.** The known-types sync test's `test_platform_mapping_correct` only requires the declared platform to be *among* the platforms that use the type; using `sensor` matches one of two and the binary_sensor coverage is implicit.
- **EFM (`Energieflussmonitor`) aggregates left for a follow-up** — out of scope for this PR. The new docs and `ISSUES_AND_TODOS.md` MED-003 entry note that an EFM device should likely also be linked to the parent PowerUnit via `via_device` when one is present; design that with the EFM headline sensors in a separate change.

### Changes

#### Helper

- `custom_components/loxone/helpers.py` — `get_all_including_subcontrols(..., with_parent: bool = False)` now returns `list[tuple[control, parent_or_None]]` when `with_parent=True`; default behaviour unchanged.

#### Sensor platform

- `custom_components/loxone/sensor.py` —
  - new `PowerUnitSensorDescription` dataclass and `POWER_UNIT_SENSOR_DESCRIPTIONS` (4 entries: `outputPower`, `batteryStateOfCharge`, `supplyTimeRemaining`, `deviceInfo`);
  - new `create_power_unit_device_info(power_unit)` shared with binary_sensor;
  - new `LoxonePowerUnitSensor` entity (subscribes per-UUID, reports native value, attaches to PowerUnit device via `_attr_device_info`);
  - `async_setup_entry` pre-registers each PowerUnit device via `dr.async_get_or_create` before discovering meters, then iterates `get_all(loxconfig, "PowerUnit")` to add headline sensors;
  - `LoxoneMeterSensor.create_device_info_from_sensor(sensor, parent=None)` adds `via_device=(DOMAIN, parent["uuidAction"])` when a parent is provided;
  - meter loop switched to `get_all_including_subcontrols(..., with_parent=True)` and passes parent through;
  - imports: `UnitOfTime`, `device_registry as dr`.

#### Binary sensor platform

- `custom_components/loxone/binary_sensor.py` —
  - imports `create_power_unit_device_info` from `sensor`;
  - new `PowerUnitBinarySensorDescription` dataclass with `state_key` + `on_when` (=0.0 by default) for inverted PROBLEM semantics;
  - new `POWER_UNIT_BINARY_DESCRIPTIONS` (`fuse` enabled DIAGNOSTIC, `CP1..CP7` DIAGNOSTIC + disabled-by-default);
  - new `LoxonePowerUnitBinarySensor` (per-UUID subscribe, sets `_attr_is_on = value == on_when`);
  - `async_setup_entry` adds entities for each matching PowerUnit state.

#### Translations

- `custom_components/loxone/translations/en.json` + `de.json` — new entity name keys: `powerunit_output_power`, `powerunit_battery_soc`, `powerunit_supply_time_remaining`, `powerunit_device_info`, and (under `binary_sensor`) `powerunit_fuse` + `powerunit_cp1..7`.

#### Tests + fixtures

- `tests/components/loxone/fixtures/structure_sensors.json` — extended the `PowerUnit` "Power Supply & Backup" with the full state map (`batteryStateOfCharge`, `supplyTimeRemaining`, `deviceInfo`, `fuse`, `CP1..CP7`) so the new tests have realistic UUIDs to fire events at.
- `tests/components/loxone/test_helpers.py` — 2 new tests: `test_with_parent_returns_tuples` and `test_with_parent_false_unchanged` (backwards-compat).
- `tests/components/loxone/test_sensor.py` — new `test_submeter_linked_to_powerunit_via_device`, `test_top_level_meter_has_no_via_device`, and 5 new tests covering each `LoxonePowerUnitSensor` (output power / battery SoC / time remaining / deviceInfo diagnostic+disabled / shared parent device).
- `tests/components/loxone/test_powerunit_binary_sensor.py` — new test module (uses `structure_sensors.json`): 5 tests covering fuse creation+enabled, CP1..CP7 created but disabled-by-default, inverted PROBLEM semantics for fuse (`1`→off, `0`→on), CP1 event update via force-enable helper, and shared parent device.
- `tests/components/loxone/known_types.py` — `PowerUnit` added under `KNOWN_CONTROL_TYPES` (mapped to `sensor`; `test_platform_mapping_correct` is satisfied because the declared platform need only be one of the platforms that uses the type).

#### Docs

- `docs/ARCHITECTURE.md` — added `PowerUnit` row to the supported-control-types table.
- `docs/HA_INTEGRATION.md` — `sensor.py` and `binary_sensor.py` entity tables updated; new sub-sections describing the `via_device` link, the pre-registration trick, and tables of which PowerUnit states map to which entities + their default-enabled flags.
- `docs/ISSUES_AND_TODOS.md` — MED-003 description tightened to reflect what's now done (per-meter discovery + PowerUnit-grouping) vs what remains (EFM aggregates).
- `docs/WORKLOG.md` — this entry.

### Investigation notes

- Live diagnostics dump from the user's Miniserver showed two distinct UUID-prefix clusters in the 12 active meter devices: 8 meters under one `PowerUnit` (`2063c3dc-0101-9e60-…` parent, `2063c460-01ce..032a-…` children + one "Power Supply & Backup" meter that shares the parent's name, with `details.type = "unidirectional"`) and 4 top-level `Meter`s (BYD HVB battery, Grid bidirectional, PV, Wattpilot). The 4 top-level meters intentionally remain at the top of the device hierarchy with no `via_device` link.
- The PowerUnit's full state map from the live structure file: `outputPower`, `CP1..CP7`, `fuse`, `batteryStateOfCharge`, `deviceInfo`, `supplyTimeRemaining`. There is no `details` block on the PowerUnit itself, so units are hardcoded per the Loxone Backup module convention (`outputPower=W`, `batteryStateOfCharge=%`, `supplyTimeRemaining=seconds`). Hardcoding is acceptable here because Loxone doesn't expose format strings for these states; if a future Loxone firmware changes the unit conventions we'll revisit.
- The teardown error `"Unable to remove unknown job listener … loxone_discovered"` observed in some test runs is unrelated to this change — it's a pre-existing pytest teardown noise from the `EVENT_COMPONENT_LOADED` listener in `__init__.py`. Tests still pass and the test harness doesn't surface it as a failure.

### Testplan

- `python -m pytest tests/ -q --tb=short` → 507 passed in ~53s (was 493 → +14: 2 helper, 7 sensor, 5 PowerUnit binary sensor).
- `python -m ruff check custom_components/loxone tests/components/loxone` → All checks passed.
- Manual: deployed via `scripts/deploy`; need to verify on the live Miniserver that (a) the 8 `Meter` sub-devices of `Power Supply & Backup` now show "via_device" linking to the PowerUnit in the HA device page, (b) the PowerUnit device itself shows `Output power`, `Battery state of charge`, `Time remaining on battery`, and `Fuse` (with deviceInfo + CP1..CP7 hidden under "+1 disabled entities" until enabled).

---

## 2026-05-26 — Discover Meter subControls of PowerUnit (Energy Flow Monitor)

User reported their Loxone Energy Flow Monitor view in Loxone Config (`Energieflussmonitor`) lists 8 meters but only 1 of them — the standalone `Fronius Energy Flow` — shows up in HA. Diagnostics dump confirmed the 7 missing meters are `subControls` of a `PowerUnit` block (`Power Supply & Backup`), and that `sensor.py` only iterates top-level `Meter` controls via `get_all(loxconfig, "Meter")`.

### Decisions

- **Walk subControls in Meter discovery, not just top-level controls.** Loxone exposes per-circuit meters of an Energy Flow Monitor as `Meter` subControls inside a `PowerUnit` block. The integration must surface these or the user's grid/consumer/producer breakdown is invisible in HA. Same model that `LightControllerV2` already uses for its sub-controls; we just hadn't applied it to meters.
- **Each subcontrol meter gets its own device, not a child of the parent.** `LoxoneMeterSensor.create_device_info_from_sensor()` already keys by `uuidAction`, which is unique per (sub)control. Treating each meter as its own device keeps the existing user-facing model (one device per meter, with Actual / Total / Total Returned / Level subsensors) and avoids special-casing PowerUnit handling. The `PowerUnit` block itself stays unhandled for now — it has no clean HA representation and would only contribute extra entities for `outputPower`, fuse state, battery SoC, etc.
- **New helper `get_all_including_subcontrols`, not a refactor of `get_all`.** Most callers (lights, switches, climate, …) deliberately operate on top-level controls only — silently expanding `get_all` to descend into subControls would surface things like `Switch` subcontrols of `LightControllerV2` as duplicate entities. Adding a parallel helper keeps the existing semantics intact and makes the recursive variant opt-in.
- **SubControls inherit `room` and `cat` from their parent.** Loxone subcontrols typically omit these because they belong to the parent control's room/category. The helper fills them in only via `setdefault` so an explicitly-set room on the subcontrol still wins.
- **Update `KNOWN_SUBCONTROL_TYPES` and the `get_all` AST scanner.** `Meter` is now a recognised subcontrol type for the dump-coverage tests; `_extract_get_all_types` in `test_known_types_sync.py` recognises `get_all_including_subcontrols` so the new call doesn't make `Meter` look stale in `KNOWN_CONTROL_TYPES`.

### Changes

- `custom_components/loxone/helpers.py` — new `get_all_including_subcontrols(json_data, name)` that walks both top-level controls and their `subControls`, applying `setdefault` for `room`/`cat` so subcontrols inherit from their parent.
- `custom_components/loxone/sensor.py` — `async_setup_entry` now uses `get_all_including_subcontrols(loxconfig, "Meter")` for meter discovery; rest of the meter-classification + repair-issue logic is unchanged.
- `tests/components/loxone/known_types.py` — added `"Meter": "sensor"` to `KNOWN_SUBCONTROL_TYPES`.
- `tests/components/loxone/test_known_types_sync.py` — `_extract_get_all_types` now also recognises calls to `get_all_including_subcontrols` so `Meter` stays mapped without being flagged as stale.
- `tests/components/loxone/fixtures/structure_sensors.json` — added a `PowerUnit` control `Power Supply & Backup` with one `Meter` subControl `Miniserver & Extensions` so the existing fixture exercises both top-level and subcontrol meters.
- `tests/components/loxone/test_helpers.py` — new `TestGetAllIncludingSubcontrols` with 7 unit tests (top-level + subcontrol discovery, room/cat inheritance vs explicit override, type filtering, empty input).
- `tests/components/loxone/test_sensor.py` — 4 new tests for sub-meter discovery: subsensor creation, state-from-event, energy-dashboard attrs, own-device identity.
- `docs/HA_INTEGRATION.md` — added a paragraph in the `sensor.py` section describing meter discovery walking subControls.
- `docs/ARCHITECTURE.md` — clarified the supported-control-types table to mention `PowerUnit` subControls feed `LoxoneMeterSensor`.
- `docs/WORKLOG.md` — this entry.

### Investigation notes

- Live diagnostics dump from the user's Miniserver shows `EFM` ("Energieflussmonitor") as a separate top-level control with aggregate states (`Ppwr` production, `Gpwr` grid, `Spwr` storage, `Pre`/`Pri` produced/consumed energy, `selfConsumption`, `actual0`–`actual7`). The screenshot in Loxone Config is the EFM block's view — it lists meters by association (Verbraucher / Erzeuger / Netz / Speicher), not by structural containment. Structurally, the meters live as either top-level `Meter` controls or `Meter` subControls of `PowerUnit`. Exposing `EFM` itself as a sensor cluster could come later but is out of scope for this fix; the per-meter data is the thing the user actually graphs.
- Existing dump fixture (`v16.1.11.6_2026-03-15_AABBCCDDEEFF.json`) has 0 `Meter` subControls so the `_compute_expectations` count in `test_structure_dumps.py` is unaffected. Future dumps containing `PowerUnit` will need their `_expected.json` regenerated; the dump-collection script already auto-counts top-level controls per platform, and we accept that subcontrol-derived entities aren't counted there — same as how light subcontrols are excluded from the dump platform counts.

### Testplan

- `python -m pytest tests/components/loxone/test_helpers.py tests/components/loxone/test_sensor.py tests/components/loxone/test_known_types_sync.py -v` → 98 passed.
- `python -m pytest tests/ -q` → 493 passed in ~51s (was 482 → +11: 7 new `TestGetAllIncludingSubcontrols` + 4 new sub-meter sensor tests).
- `ruff check custom_components/loxone tests/components/loxone` → clean (after one auto-fix to import order in `sensor.py`).
- Manual: deploy via `scripts/deploy`, confirm `sensor.miniserver_extensions_actual` etc. appear in HA's Energy dashboard alongside the existing `sensor.fronius_energy_flow_*` entities.

---

## 2026-05-25 — Merge upstream/master (0.9.12 → 0.9.14)

First sync with `JoDehli/PyLoxone` master since we diverged: 9 upstream commits, including [`d32f8cf`](https://github.com/JoDehli/PyLoxone/commit/d32f8cfa5d6fb6f6657758757af1e1c33c000df3) (Jaroslav Martasek) — a keyword-aware sensor classification engine that fixes a real bug we still carried. Took the refactor and integrated it with our existing extensions in the same merge, so the resulting tree is the actual intended state instead of "merge then partial fix later".

### Decisions

- **Merge, not rebase.** 85 commits ahead, 9 behind. A merge commit preserves the divergent history and clearly marks where we re-synced; rebasing would rewrite the whole feature lineage for cosmetic linearity.
- **Adopt upstream's sensor classification refactor.** `d32f8cf` replaced the broken `humidity_or_battery` `SENSOR_TYPES` entry (matched every `%` sensor, set no `device_class`) with a unit-and-keyword matching engine — one description per concept (`temperature`, `wind_speed`, `energy`, `power`, `volume_flow_rate`, `water`, `illuminance`, `carbon_dioxide`, `humidity`, `battery`). New `match_sensor_description(unit, name, category)` plus `UNAMBIGUOUS_UNITS` frozenset. We adopt it verbatim — no parallel infrastructure for a problem upstream already solved well, and it gives us a contribution-ready surface for any future locale-keyword extensions.
- **Keep `_METER_CLASSIFICATION` alongside, untouched.** The two systems are complementary, not overlapping: `match_sensor_description` classifies `InfoOnlyAnalog` value sensors by unit + name/category; our existing `_METER_CLASSIFICATION` classifies `Meter` subsensors (Actual / Total / TotalReturned / Level) by meter type. Different code paths, different inputs, both stay.
- **Move `_clean_unit` from `LoxoneEntity` to `helpers.clean_unit`.** Upstream's refactor extracts it to module level. Only one external caller (`LoxoneSensor.__init__`) and it lets the new test suite import it directly. `_get_format` stays on `LoxoneEntity` — it has three callers (`sensor`, `binary_sensor`, `fan`).
- **Read `name` / `cat` from kwargs in `LoxoneSensor.__init__`.** Not from `self.*` — the base class's dynamic `setattr(self, key, val)` only runs for keys actually present in kwargs, so `self.cat` may or may not exist on the instance. `kwargs.get("cat", "")` is unambiguous and side-effect-free.
- **Use `frozen_or_thawed=True` for `LoxoneEntityDescription`.** Upstream uses HA's class-arg syntax for subclassing the frozen `SensorEntityDescription` with new fields. Confirmed supported on our pinned HA version; removes the now-unnecessary `@dataclass(frozen=True)` + `LoxoneRequiredKeysMixin` pattern.
- **"Ours" wins on formatting-only conflicts.** All six formatting conflicts (`binary_sensor.py`, `climate.py`, `helpers.py`, `lights/lightcontroller.py`, `pyloxone_api/connection.py`, `pyloxone_api/message.py`) and the docstring tweak resolve to our version — we're Ruff-aligned to HA Core style, upstream's pre-Ruff formatting is not an upgrade.
- **`colorpickers.py` LumiTech: drop the legacy assignment.** Upstream still assigns `_attr_device_info` in `LumiTech.__init__`; our `RGBColorPicker` base now provides a dynamic `device_info` property that handles both standalone and LightControllerV2-subcontrol cases. The duplicate assignment is no longer needed.
- **Take upstream's version bump (`manifest.json`: 0.9.12 → 0.9.14).** Stays in sync with the upstream version line; we don't ship a separately versioned fork.
- **Skip upstream's new `pytest.ini` and root `conftest.py`.** `pytest.ini` would conflict with our `pyproject.toml` (no `asyncio_mode = "auto"` → tests break); root `conftest.py` is a venv-setup docstring not relevant to our devcontainer.
- **Take upstream's `tests/test_sensor_matching.py` content, place under `tests/components/loxone/`.** Matches our HA-style test layout. 50 pure-unit tests covering `match_sensor_description`, `UNAMBIGUOUS_UNITS`, `clean_unit`, and `SENSOR_TYPES` invariants — guards the classification table independent of integration setup.
- **Take upstream's new README "Sensor Device Class Detection" section, plus our `Meter` fallback paragraph.** The section accurately describes the new behavior; we extend it to also document the `Meter` fallback path that upstream doesn't have. Also updated `HA_INTEGRATION.md` to describe the new classification flow.
- **Already-have items confirmed identical.** Upstream's two bugfixes from this batch were already independently present on `dev`: `climate.py` `ATTR_TEMPERATURE` fix (#479) and `colorpickers.py` logging format fix (#482).
- **Future strategy.** Treat upstream as a baseline to re-sync periodically and a target for small, themed contribution PRs (translation_keys, keepalive fix, legacy meter model handling, CI cleanup) — not for the big architectural pieces (sync engine, frontend panel, runtime_data rewrite) which need a design dialogue with `@JoDehli` first.

### Changes

#### Sensor classification (from upstream `d32f8cf`)

- `custom_components/loxone/sensor.py` —
  - replaced `LoxoneRequiredKeysMixin` + `@dataclass(frozen=True)` `LoxoneEntityDescription` with `frozen_or_thawed=True` subclass carrying `loxone_format_strings`, `category_keywords`, `name_keywords`;
  - rebuilt `SENSOR_TYPES` (10 entries, one per concept) — collapsed prior per-unit duplicates (`kwh`/`wh`, `power`×2) into single descriptions with multi-unit tuples;
  - added `UNAMBIGUOUS_UNITS` frozenset + `match_sensor_description()`;
  - dropped `SENSOR_FORMATS` and `LoxoneSensor._get_entity_description`;
  - `LoxoneSensor.__init__` now calls `clean_unit` + `match_sensor_description` with name/category from kwargs;
  - added `CONCENTRATION_PARTS_PER_MILLION` and `UnitOfVolumeFlowRate` to imports.
- `custom_components/loxone/helpers.py` — new module-level `clean_unit(lox_format)`.
- `custom_components/loxone/__init__.py` — removed `LoxoneEntity._clean_unit` staticmethod (now `helpers.clean_unit`).
- `tests/components/loxone/test_sensor_matching.py` — 50 new pure-unit tests across `TestSensorMatching`, `TestUnambiguousUnits`, `TestUnitExtraction`, `TestSensorTypesStructure`.

#### Other upstream integration

- `custom_components/loxone/manifest.json` — version bumped to `0.9.14`.
- `custom_components/loxone/__init__.py` — auto-merged formatting (multi-line except clause).
- `custom_components/loxone/pyloxone_api/discover.py` — auto-merged formatting (removed redundant parens around tuple unpacking).
- `custom_components/loxone/lights/colorpickers.py` — LumiTech `else` branch no longer assigns `_attr_device_info`; the parent `RGBColorPicker.device_info` property already handles both standalone and LightControllerV2 cases.

#### Docs

- `README.md` — new "Sensor Device Class Detection" section with device class table, `Meter` fallback note, and `customize`/`customize_glob` override example.
- `docs/HA_INTEGRATION.md` — replaced stale "duplicate `power` keys" issue note with a one-paragraph description of the new classification flow.
- `docs/WORKLOG.md` — this entry.

### Testplan

- `ruff check .` → All checks passed.
- `python -m pytest tests/components/loxone/test_sensor_matching.py -v` → 50 passed in 0.47s.
- `python -m pytest tests/ -q --tb=short` → 482 passed in ~50s (was 432 before the merge; gained 50 new sensor classification tests).
- Existing `test_sensor_entity_description_matched` and `test_wind_sensor_unit` continue to pass — Temperature and WIND_SPEED classifications are equivalent under the new system.
- Merge commit graph preserves both lineages; future `git fetch upstream && git merge upstream/master` will only see commits added after this point.
- Manual: deploy + verify in HA UI that existing `%` sensors named "Vlhkost …" / "Battery …" pick up `humidity` / `battery` device classes after restart.

---

## 2026-05-21 — Add deploy SSH preflight

Made the deploy helper fail early with a clear `ssh-add` hint when the SSH key is not unlocked in the current session.

### Decisions

- **Check SSH before building.** If SSH cannot authenticate, there is no point rebuilding the frontend bundle first.
- **Use BatchMode for deploy validation.** The script now tests the same non-interactive behavior it needs later for rsync/scp and restart commands.
- **Document the recurring unlock step.** Passphrase-protected keys require `ssh-add` once after a host reboot in this setup.

### Changes

- `scripts/deploy` — added a non-interactive SSH preflight and actionable diagnostics for empty/locked SSH agent cases.
- `.devcontainer.json` — removed the explicit host `~/.ssh` bind mount; deploy now relies on the forwarded SSH agent.
- `README.md` — added the common `ssh-add` before `scripts/deploy` workflow and described checking the forwarded agent.
- `docs/WORKLOG.md` — recorded this cleanup.

### Testplan

- `bash -n scripts/deploy` — syntax OK.
- Reviewed script and README diffs.

---

## 2026-05-21 — Document development deploy SSH setup

Documented the local deploy workflow and the SSH-key failure mode hit while trying to deploy the RGB bridge panel update.

### Decisions

- **Keep deploy setup in the README.** The deploy script is developer-facing and depends on local `.deploy.env` plus SSH, so the top-level README is the easiest place to find it.
- **Call out non-interactive SSH.** `scripts/deploy` cannot prompt for a key or password during automation; `ssh "$HA_SSH" true` should work before running it.
- **Document the observed failure.** `Permission denied (publickey)` from the devcontainer means no accepted key was available to SSH, not that the frontend build failed.

### Changes

- `README.md` — added a Development deploys section with `.deploy.env`, restart/reload behavior, devcontainer SSH mount notes, and troubleshooting commands.
- `docs/WORKLOG.md` — recorded this documentation cleanup.

### Testplan

- Documentation-only change; no automated tests run.
- Reviewed README diff and existing deploy script behavior.

---

## 2026-05-21 — Show RGB diagnostics in bridge overview

Added compact RGB visibility to the frontend Bridges view so color-light bridges show both current HA color and bridge runtime color flow.

### Decisions

- **Keep conversion in the frontend.** The `loxone/get_bridges` endpoint already exposes runtime values, so the panel derives RGB display values without changing the backend payload.
- **Parse only the known color wire format.** Loxone runtime values are converted from `hsv(h,s,v)` with a strict parser; unsupported values such as `temp(...)`, `On`, or `Off` stay hidden in the color chips.
- **Prefer compact diagnostics.** RGB chips live under the existing state cell so the bridge table remains readable for non-light bridges.
- **Show retained color while off.** HA often keeps `rgb_color`/`hs_color` attributes on an off light, so the panel displays those last known values instead of hiding them.

### Changes

- `custom_components/loxone/frontend/src/types.ts` — typed the existing bridge runtime diagnostics returned by `loxone/get_bridges`.
- `custom_components/loxone/frontend/src/color-format.ts` — added HA/Loxone RGB conversion and display helpers.
- `custom_components/loxone/frontend/src/bridges-view.ts` — renders `HA`, `Sent`, and `Recv` RGB chips with color swatches when values are available.
- `custom_components/loxone/frontend/test/color-format.test.ts` — covers RGB formatting, HSV conversion, HA attribute fallback, off-state retained colors, invalid values, and Loxone runtime parsing.
- `docs/WORKLOG.md` — recorded this session.

### Testplan

- `npm run test && npm run typecheck && npm run build` in `custom_components/loxone/frontend` — 18 frontend tests passed, typecheck passed, panel bundle built.
- `python -m pytest tests/ -v` — 432 passed.
- IDE diagnostics — no linter errors in edited frontend files.

---

## 2026-05-21 — Guard disconnected WebSocket commands and migration tests

Closed the command-queue disconnect gap, added config-entry migration coverage, and reconciled the TODO docs with the CI workflows that already exist in the repository.

### Decisions

- **Drop commands before enqueueing when disconnected.** User and bridge commands during a closed WebSocket session are logged and discarded instead of piling up in the send queue.
- **Keep send-loop disconnect handling quiet.** If the connection closes between enqueue and send, `_send_text_command` returns after logging instead of attempting to write to a missing transport.
- **Treat CI as present.** The repo already has tests, lint, Hassfest, and HACS validation workflows, so the TODO docs were corrected instead of adding duplicate workflows.

### Changes

- `custom_components/loxone/pyloxone_api/connection.py` — added connection-state guards before queueing and before transport send.
- `tests/components/loxone/test_connection.py` — covered connected queueing, disconnected dropping, UUID validation, and send-loop disconnect behavior.
- `tests/components/loxone/test_init.py` — added v1→v3, v2→v3, and v3 no-op config-entry migration tests.
- `docs/ISSUES_AND_TODOS.md`, `docs/API_LAYER.md` — removed completed MED-013/ARCH-006 items and corrected CI status.

### Testplan

- `python -m pytest tests/components/loxone/test_connection.py tests/components/loxone/test_init.py -q --tb=short` — 21 passed.
- `python -m ruff check custom_components/loxone/__init__.py custom_components/loxone/pyloxone_api/connection.py tests/components/loxone/test_connection.py tests/components/loxone/test_init.py` — no issues.
- `python -m pytest tests/ -q --tb=short` — 432 passed.

---

## 2026-05-21 — Harden bridge sync loop prevention and diagnostics

Made the device bridge runtime direction-aware so bidirectional Hue/ColorPicker bridges settle instead of ping-ponging between Loxone and Home Assistant.

### Decisions

- **Compare semantic values, not raw wire strings.** Mappers now provide normalized values for bridge equality checks; `ColorPickerMapper` uses tolerant HSV/temp comparisons to absorb Hue/Loxone round-trip drift.
- **Suppress by direction and reason.** HA feedback from a Loxone-originated service call is suppressed for a short window, while Loxone echo suppression only applies when the incoming value matches the command PyLoxone just sent.
- **Loxone app actions take ownership.** Incoming Loxone values clear pending HA cooldown commands so stale HA changes cannot flush later and overwrite the user's Loxone-side action.
- **Diagnostics must show runtime state.** The bridge WebSocket API exposes subscribed UUIDs, last sent/received values, pending commands, suppression windows, and suppression reasons.

### Changes

- `custom_components/loxone/bridge.py` — added normalized runtime bookkeeping, direction-aware suppression, pending command cancellation, and richer bridge debug state.
- `custom_components/loxone/bridge_mappers.py`, `bridge_types.py` — added mapper-level normalization/equality hooks and tolerant ColorPickerV2 comparison.
- `custom_components/loxone/websocket.py` — expanded `loxone/get_bridges` with bridge state/subscription/runtime diagnostics.
- `tests/components/loxone/test_bridge.py`, `test_websocket.py` — covered echo suppression, Loxone ownership, pending command cancellation, color drift tolerance, and diagnostics output.
- `docs/HA_INTEGRATION.md`, `docs/ARCHITECTURE.md` — documented the bridge sync contract and runtime flow.

### Testplan

- `python -m pytest tests/components/loxone/test_bridge.py tests/components/loxone/test_websocket.py -q --tb=short` — 97 passed.
- `python -m ruff check custom_components/loxone/bridge.py custom_components/loxone/bridge_mappers.py custom_components/loxone/websocket.py tests/components/loxone/test_bridge.py tests/components/loxone/test_websocket.py` — no issues.
- Deployed with `scripts/deploy`; verified `light.infuse` Loxone → HA and HA → Loxone changes produce expected `Ceiling` events and settle with no follow-up events over a 12 second monitor window.

---

## 2026-05-21 — Clean up visible CI validation errors

Fixed repository-side lint and Hassfest issues found while checking CI status after the pytest teardown fixes.

### Decisions

- **Keep fixable repair translations schema-compliant.** `token_expired` uses a repair `fix_flow`, so its user-facing details live in the flow step instead of a top-level issue description.
- **Leave external HACS checks to repo settings.** Missing repository topics and disabled issues are GitHub repository configuration, not code changes.

### Changes

- `tests/components/loxone/test_websocket.py` — combined nested patch context managers to satisfy Ruff `SIM117`.
- `custom_components/loxone/translations/en.json`, `de.json` — removed top-level `token_expired.description` for the fixable repair issue.

### Testplan

- `python -m ruff check .` — no issues.
- `python -m pytest tests/ -q --tb=short` — 420 passed.

---

## 2026-05-21 — Remove config flow AsyncMock warnings

Cleaned up the config-flow HTTP response mock so successful credential validation tests no longer leak unawaited coroutine warnings.

### Decisions

- **Mock `resp.json()` as async.** The production config flow awaits `ClientResponse.json()`, so tests should provide an awaitable JSON method instead of relying on MagicMock's default coroutine behavior.

### Changes

- `tests/components/loxone/test_config_flow.py` — `_mock_response()` now attaches an `AsyncMock` JSON method returning an empty payload by default.

### Testplan

- `python -m pytest tests/components/loxone/test_config_flow.py -q --tb=short` — 27 passed.
- `python -m pytest tests/ -q --tb=short` — 420 passed, 0 warnings.

---

## 2026-05-21 — Fix pytest teardown hang in mocked Loxone tests

Stabilized the test fixture lifecycle so mocked WebSocket background tasks are cancelled during config-entry unload instead of lingering through Home Assistant teardown.

### Decisions

- **Mock listener stays pending until cancellation.** The shared `LoxoneConnection.start_listening` mock now behaves like the production WebSocket listener instead of returning immediately.
- **Shared integration fixture owns unload.** `init_integration` now yields the config entry and explicitly unloads it during fixture teardown.
- **Scene generation is opt-in for shared tests.** Default mock options disable delayed scene generation; dedicated scene tests still enable it explicitly.

### Changes

- `tests/components/loxone/conftest.py` — pending listener mock, yielding integration fixture, faster default scene options.
- `tests/components/loxone/test_coordinator.py` — fixed the reconnect cleanup test so it does not orphan a long-running task.

### Testplan

- `python -m pytest tests/components/loxone/test_alarm_control_panel.py -q --tb=short --timeout=15` — 12 passed.
- `python -m pytest tests/components/loxone/test_coordinator.py -q --tb=short --timeout=15` — 16 passed.
- `python -m pytest tests/ -q --tb=short` — 417 passed, 5 existing warnings.

---

## 2026-04-15 — Async compliance, keepalive fix, scene reconnect, architecture docs

Full async compliance sweep across all entity platforms, a Loxone protocol fix for the keepalive handshake, reliable scene generation after reconnects, and comprehensive architecture documentation.

### Decisions

- **`config_entry.async_create_background_task` for long-running tasks.** `hass.async_create_task` is tracked by HA's bootstrap watchdog and will block startup if the task never completes. The listen loop and reconnect loop are indefinite — they must use `async_create_background_task`, which is tied to the config entry lifecycle but does not block bootstrap.
- **Keepalive is bidirectional.** The Miniserver sends its own keepalive header every 30 seconds and expects a `"keepalive"` text response within ~3 seconds. The client was not responding, causing the Miniserver to close the connection every 30s. Added the response in `_do_start_listening`.
- **Scene regeneration via dispatcher signal.** Scenes were only generated once at startup. After a reconnect, moods re-arrive but nothing re-triggered scene generation. The coordinator now fires `loxone_{entry_id}_reconnected` after every successful connection; scene.py subscribes and re-runs scene gen (with delay, and dedup via entity registry).
- **Diagnostic sensors must stay `available`.** `LoxoneConnectionStateSensor` and `LoxoneReconnectCountSensor` report connection health — they should always show their value, not go `unavailable` when the coordinator is disconnected.

### Changes

- **`pyloxone_api/connection.py`** — respond to server KEEPALIVE header with `"keepalive"` text command.
- **`coordinator.py`** — `async_create_background_task` for listen and reconnect tasks; `async_dispatcher_send` for `_reconnected` signal; cleanup `miniserver.listeners` before replacing `MiniServer` on reconnect.
- **`__init__.py`** — fire `_reconnected` signal at end of `async_setup_entry`; `await` send commands directly; `asyncio.gather(..., return_exceptions=True)` for YAML platform loading and service reload.
- **`scene.py`** — signal-driven scene generation (`_on_reconnect` callback via `async_dispatcher_connect`); entity registry dedup before adding scenes; `config_entry.async_on_unload` for cleanup.
- **`sensor.py`** — `available = True` on diagnostic sensors; `@cached_property unique_id` override to avoid `uuidAction` AttributeError; pass `async_add_entities` directly to dispatcher (no wrapper).
- **`cover.py`, `switch.py`, `climate.py`, `fan.py`, `button.py`, `number.py`, `alarm_control_panel.py`** — all sync service methods converted to `async_*`; `hass.bus.async_fire` throughout; `async_schedule_update_ha_state` throughout.
- **`websocket.py`** — `_panel_js_hash_sync` called via executor; PLR1714 compound comparison fixes.
- **`binary_sensor.py`** — pass `async_add_entities` directly to dispatcher (no wrapper).
- **`docs/ARCHITECTURE.md`** — new sections: Connection Lifecycle, Keepalive Protocol, Task Management Rules, Reconnect & State Recovery, `_reconnected` signal contract.
- **`docs/HA_INTEGRATION.md`** — updated Setup Flow diagram, Coordinator section (reconnect flow, task lifecycle), Base Entity, Scene platform, async rules table.
- **Tests** — `test_scene.py` (new, 5 tests); `test_sensor.py` (+10 tests for diagnostic sensors); `test_websocket.py` (+3 tests for executor-wrapped hash).

### Testplan

- `python -m pytest tests/ -q` — 417 passed, 0 failed.
- Deployed; confirmed stable connection with no 30s disconnect cycle and no reboot loop.

---

## 2026-04-12 — Async safety audit and fixes

Comprehensive audit of all async usage against Home Assistant best practices, fixing thread-safety violations and modernizing entity service methods.

### Decisions

- **All entity service methods converted to async** — `def turn_on` → `async def async_turn_on`, etc. These no longer run in the executor; they fire events and schedule state updates directly on the event loop, avoiding unnecessary thread round-trips.
- **`asyncio.create_task` → `hass.async_create_task`** in coordinator — HA can now track the listening task for shutdown/cancellation.
- **`asyncio.wait` → `asyncio.gather`** for YAML platform loading — exceptions are no longer silently swallowed.
- **Dispatcher wrappers removed** in sensor.py/binary_sensor.py — `async_add_entities` is passed directly (same pattern as cover.py), removing unnecessary `@callback` indirection.

### Changes

- `scene.py` — replaced `async_call_later` + lambda callback with `hass.async_create_task` + `asyncio.sleep` coroutine (fixes the thread-safety crash).
- `cover.py` — converted 15 sync service methods to async (`async_open_cover`, `async_close_cover`, `async_stop_cover`, `async_set_cover_position`, tilt methods, sun automation methods); fixed `event_handler` to use `async_schedule_update_ha_state()`.
- `switch.py` — converted `turn_on`/`turn_off` to async across all 3 switch classes; fixed `event_handler`.
- `climate.py` — converted `set_temperature`, `set_hvac_mode`, `set_preset_mode`, `set_fan_mode`, `set_swing_mode` to async across all 3 climate classes; fixed `event_handler`.
- `fan.py` — converted `set_percentage`, `set_preset_mode`, `turn_off` to async; fixed `async_turn_on`/`async_turn_off` to await the helper methods; fixed `event_handler`.
- `button.py` — converted `press` to `async_press`; fixed `event_handler`.
- `number.py` — fixed `event_handler` and `async_set_native_value` to use `async_schedule_update_ha_state()`.
- `coordinator.py` — changed `asyncio.create_task` to `hass.async_create_task` in `async_start_listening`.
- `__init__.py` — moved `EVENT_COMPONENT_LOADED` listener into `coordinator.listeners` for cleanup on unload; replaced `asyncio.wait` with `asyncio.gather` for YAML platform loading.
- `sensor.py`, `binary_sensor.py` — removed unnecessary `@callback` wrappers around `async_add_entities`; removed unused `callback` import.
- `alarm_control_panel.py` — removed empty sync `alarm_disarm`/`alarm_arm_home`/`alarm_arm_away` methods that shadowed the working `async_alarm_*` versions.
- `__init__.py` `handle_reload` — added `return_exceptions=True` to both `asyncio.gather` calls to prevent partial reload on failure.
- `docs/HA_INTEGRATION.md` — updated sync/async inconsistency section to reflect resolved state.

### Additional fixes (from deploy testing)

- `sensor.py` — `LoxoneConnectionStateSensor` and `LoxoneReconnectCountSensor` crashed on startup because `LoxoneEntity.unique_id` accesses `self.uuidAction` but these sensors don't have one (they call `super().__init__()` with no kwargs). Added `unique_id` property override returning `_attr_unique_id`.
- `websocket.py` — `_panel_js_hash()` used `Path.read_bytes()` on the event loop, triggering HA's blocking I/O detector. Moved to `async_add_executor_job`.

### Testplan

- Run `python -m pytest tests/ -v` — verify no regressions.
- Deploy and verify all entity types respond correctly: covers open/close/stop, switches toggle, climate set temperature/mode, fan speed, button press, scene activation.
- Verify no `async_create_task from a thread` warnings in HA logs.
- Verify no `Detected blocking call to read_bytes` warnings in HA logs.
- Verify no `LoxoneConnectionStateSensor has no attribute 'uuidAction'` errors in HA logs.

---

## 2026-04-05 — Add page intro blurbs to all frontend panel views

Each of the eight panel tabs (Devices, Areas, Bridges, Monitor, Console, Logs, Structure, Status) now shows a short orienting paragraph at the top of the view, following the KNX integration pattern. Each blurb answers "what is this view?" and "what would I do here?" in one or two sentences.

### Changes

- `frontend/src/devices-view.ts`, `areas-view.ts`, `bridges-view.ts`, `monitor-view.ts`, `console-view.ts`, `logs-view.ts`, `structure-view.ts`, `status-view.ts` — added `.page-intro` CSS class and rendered `<p class="page-intro">` at the top of each view's render method.
- `frontend/loxone-panel.js` — rebuilt bundle (115 kb).

### Testplan

- Deploy and open each tab — intro text appears below the tab bar in muted secondary colour.

---

## 2026-04-05 — Velux cover bridge: compound VI/VO bridge for HA cover entities

Added `CoverMapper` — a compound bridge type that maps a HA `cover.*` entity (e.g. Velux shades via KLF200) to up to four Loxone VI/VO controls: one Slider VI for position feedback and up to three optional VOs (move-up, move-down, target position). The bridge panel gains cover-specific UX: a multi-picker form, a collapsible Loxone setup guide with naming suggestions, and a "Scan Loxone" button that auto-fills UUID fields by name-convention matching against the loaded structure file.

### Decisions

- **Compound bridge via `details` dict** — extra VO UUIDs stored in `DeviceBridge.details` (already `dict[str, Any]`, already persisted as JSON). No schema migration needed; backwards-compatible.
- **`loxone_type = "cover"` sentinel** — since there is no native Loxone "cover" control type for the bridge, the WS handler sets this sentinel when the entity domain is `cover` and the UUID lookup returns no type.
- **Position convention** — HA position 0–100 (0 = closed, 100 = open) mapped directly to the Slider VI value. No inversion needed (unlike native Loxone Jalousie which uses an inverted scale).
- **Up/down VOs trigger on rising edge only** — `loxone_value_to_ha` ignores the VO going back to 0 (motion-stopped signal) to avoid double-calling open/close.
- **HTTP template generation dropped** — VI_ polling has unacceptable lag for shade position feedback; the WebSocket bridge is strictly better.

### Changes

- `custom_components/loxone/bridge_mappers.py` — new `CoverMapper` class + `_COVER_VO_KEYS` constant; added `"cover"` to `_SUPPORTED_DOMAINS`; factory wired in `get_mapper`.
- `custom_components/loxone/bridge.py` — `bridged_uuids` property extended to include cover VO UUIDs; `unregister_bridge` re-enables all cover UUIDs on removal.
- `custom_components/loxone/websocket.py` — `ws_add_bridge` handler accepts optional `details: {str: str}` in voluptuous schema; passes it to `DeviceBridge`; sets `loxone_type = "cover"` sentinel for cover entities.
- `custom_components/loxone/frontend/src/api.ts` — `addBridge` accepts optional `details` param; forwards non-empty details to WS message.
- `custom_components/loxone/frontend/src/bridges-view.ts` — added `"cover"` to `BRIDGEABLE_DOMAINS`; cover-specific state + helpers (`_coverVoUuids`, `_isCoverEntity`, `_coverNamePrefix`, `_scanLoxoneForCover`); cover VO section renders when cover entity selected; Setup Guide collapsible; Scan button; `_addBridge` passes `details` for covers.
- `tests/components/loxone/test_bridge.py` — 20 new tests in `TestCoverMapper`.
- `docs/HA_INTEGRATION.md` — updated supported-mappings table; added cover bridge section with VI/VO layout table.

### Investigations

- Velux HA integration (KLF200): each KLF200 node is a separate HA device/entity. Window openers and blinds are always separate. `Blind` type supports tilt (slat angle); `Awning`/`RollerShutter` do not. Rain sensor is on `Window` type nodes, disabled by default, polled every 5 minutes.
- Loxone template format: VI_/VO_ XML templates are for HTTP/UDP virtual devices only — not for programming-block VIs (Slider/Switch type). Template download feature dropped in favour of the in-panel setup guide.

--

## 2026-04-05 — Fix devices view detail panel immediately closing
Tapping an entry in the Devices tab opened a brief loading overlay then immediately closed, with no drawer ever appearing.
### Decisions
- **Read from `structure_file` not `api.*`** — `coordinator.api` is a `LoxoneConnection`; it only exposes `structure_file`. The attributes `api.controls`, `api.rooms`, and `api.categories` don't exist — consistent with every other WS handler which reads `coordinator.api.structure_file`.
- **Resolve by `uuidAction`** — `ws_get_devices` exposes devices using `uuidAction` as the UUID. `ws_get_control_detail` was looking up by raw dict key, so sub-controls (whose `uuidAction` differs from their key) were never found. The lookup now searches both top-level and sub-controls by `uuidAction`.
- **Surface errors in frontend** — the silent `catch { this._detail = null; }` is replaced with one that sets `this._error`, making future backend failures visible.
### Changes
- `custom_components/loxone/websocket.py` — `ws_get_control_detail`: replaced `api.controls/.rooms/.categories` with `structure_file`; added `uuidAction`-aware lookup including sub-controls; added `uuidAction` and `subControls` to `safe_keys` exclusion list. `ws_get_structure`: same `structure_file` fix; UUIDs now use `uuidAction` for consistency with `ws_get_devices`.
- `custom_components/loxone/frontend/src/devices-view.ts` — `_openDetail` catch block now sets `this._error` instead of silently swallowing it.
- `custom_components/loxone/frontend/loxone-panel.js` — rebuilt bundle.
### Testplan
- Deploy and tap a device row in the Devices tab — drawer opens and shows UUID, states, and HA entities.
- Tap a sub-control row — drawer opens correctly (was "not found" before).
- All 398 unit tests pass.
---

## 2026-04-05 — Ruff: Home Assistant Core alignment and MED-014 (lint + pydocstyle)

Adopted Ruff **rule sets aligned with** [Home Assistant Core `pyproject.toml`](https://github.com/home-assistant/core/blob/dev/pyproject.toml) (curated `select` / `ignore`, not `select = ["ALL"]`). Burned down per-file suppressions on **`custom_components/loxone/**`** so only **`TID252`** remains—other issues are fixed or carry a tight inline `noqa`. Completed **MED-014**: non-docstring waivers, then pydocstyle on the integration; removed the MED-014 issue from `ISSUES_AND_TODOS.md`. **`ruff check .` is clean; `python -m pytest tests/ -q` → 378 passed.**

### Decisions

- **Policy:** Rebase `ruff.toml` from core when upstream changes; PyLoxone-only deltas stay in `docs/LINTING.md`.
- **Burn-down:** Dropped blanket `per-file-ignores` for `BLE001`, `PLC0415`, `TRY300`/`TRY301`, `C901`, `TRY203`, `G201`, `PLC0206`, and finally **`D100`–`D107` / `D205`** on the integration—prefer real fixes or scoped `noqa` with rationale.
- **Tests layout:** `tests/components/loxone/**` matches our flat paths (not core’s extra package segment under `tests/components/`).
- **`bridge_types.py`:** Holds `DeviceBridge` + `BridgeMapper` so `bridge_mappers` imports types without a cycle; `bridge.py` imports `get_mapper` at module level.
- **`async_setup_entry`:** `# noqa: C901`; bus listeners stay inner closures for readability.
- **`async_unload_entry`:** `except Exception  # noqa: BLE001` — unload must survive messy teardown.
- **WS / group helpers:** `# noqa: BLE001` only where a catch-all is required to respond safely.
- **Docstrings:** Broad pass over the integration; hand-fixed `bridge.py` (no docstring between `@callback` and inner `def`), **D205** / indentation in `cover.py` and `media_player.py`.
- **Test harness vs `homeassistant` pin:** `pytest-homeassistant-custom-component` declares an exact `Requires-Dist: homeassistant==…`. **`0.13.314`** required **2026.2.1** while **`requirements.txt`** had **2026.2.2**, so repeated installs bounced HA. Bumped to **`pytest-homeassistant-custom-component==0.13.315`** (matches **2026.2.2**).

### Changes (summary)

- **`ruff.toml`**, **`requirements.txt`**, **`requirements_test.txt`**, **`scripts/lint`**, **`docs/LINTING.md`**, **`AGENTS.md`**, **`docs/API_LAYER.md`**
- **`custom_components/loxone/**`** (incl. **`bridge_types.py`**, **`lights/__init__.py`** package docstring), **`tests/components/loxone/**`**, **`tests_e2e_miniserver/**`**
- **`docs/ISSUES_AND_TODOS.md`:** MED-014 removed; testing strategy note updated for pytest-hacc / HA version lockstep

### Testplan

- `ruff check .`
- `python -m pytest tests/ -q`

---

## 2026-04-04 — Panel accessibility (tabs, focus, labels)

### Decisions

- Use the WAI-ARIA tabs pattern with native `button` tabs: `role="tablist"`, `role="tab"`, `aria-selected`, roving `tabindex` (0 on the active tab, −1 on others), and `aria-controls` / `role="tabpanel"` linking.
- Arrow Left/Right (and Up/Down), Home, and End move focus and activate the target tab; `aria-labelledby` on the panel tracks the active tab for screen readers.

### Changes

- **`frontend/src/loxone-panel.ts`** — Replaced clickable `div` tabs with accessible buttons; keyboard navigation; labeled tablist (`aria-label="Loxone sections"`), miniserver `select` (`aria-label="Miniserver"`), refresh button (`aria-label="Refresh current view"`); `:focus-visible` outlines on tabs and refresh.
- **`frontend/src/devices-view.ts`** — `aria-label` (+ `type="button"`) on entity enable/disable toggles and drawer close control.
- **`frontend/src/logs-view.ts`**, **`frontend/src/monitor-view.ts`** — `aria-pressed` and `aria-label` on pause/resume; `type="button"` on toolbar buttons.
- **`frontend/test/api.test.ts`** — `mockHass` includes `connection.subscribeMessage` so `tsc` matches `HomeAssistant`.
- **`frontend/package.json`** — `esbuild` range aligned with `package-lock.json` (`^0.27.4`) so `npm ci` is valid.
- **`frontend/loxone-panel.js`** — Rebuilt bundle.

### Testplan

- `npm ci` → `npm run typecheck` → `npm test` → `node build.mjs` in `custom_components/loxone/frontend` (Linux arm64).
- Manual: open Loxone panel → Tab to tab bar → Arrow keys switch tabs; refresh and miniserver select expose correct names in screen reader / accessibility tree.

---

## 2026-04-03 — Frontend feature gap closure + DHCP fix

### Decisions
- Entity inspector drawer: state UUIDs shown but live values not populated (coordinator doesn't accumulate a state dict — values are dispatched per-UUID); structure metadata (room, category, states, entities) is fully available
- Log viewer: does not manipulate the logger level — users must set `custom_components.loxone: debug` in `configuration.yaml` for debug/info messages; by default only WARNING+ reaches the handler
- Bridges UX: added domain grouping, search, and a confirmation dialog for removals to improve usability with many bridges
- DHCP duplicate fix: IP-based de-duplication added alongside MAC-based unique_id check, since a Miniserver can present multiple MACs (dual NIC, Audio Server) for the same IP

### Changes
- **loxone-panel.ts** — URL routing via `window.location.hash` (deep-linkable tabs); added Logs and Structure tabs
- **devices-view.ts** — advanced filters (domain, room, status dropdowns); clickable rows open entity inspector drawer; toast notifications on enable/disable
- **bridges-view.ts** — summary line, table search, domain grouping, removal confirmation dialog, toast notifications
- **console-view.ts** — toast notifications on send success/error
- **areas-view.ts** — toast notifications on sync
- **status-view.ts** — diagnostics download button (JSON export of status + structure diff)
- **logs-view.ts** — new view: real-time log streamer with pause/resume, text filter, level filter (WARNING+ by default), hint about logger config
- **structure-view.ts** — new view: searchable/groupable/collapsible tree of Miniserver structure (rooms, categories, controls, sub-controls, states)
- **api.ts** — added `fetchControlDetail`, `fetchStructure` API functions
- **types.ts** — added `showToast` utility, `GetControlDetailResult`, `GetStructureResult`, `LogEntry`, and related interfaces
- **websocket.py** — registered 3 new WS commands: `loxone/get_control_detail`, `loxone/get_structure`, `loxone/subscribe_logs`
- **config_flow.py** — DHCP `async_step_dhcp` now checks existing entries by IP (via `entry.options`) before creating a new flow, preventing duplicate discovery cards for multi-NIC Miniservers
- **test_config_flow.py** — added `test_dhcp_discovery_aborts_second_nic_same_ip` covering the IP-based de-duplication

### Investigations
- Coordinator does not store a UUID→value map; live values are dispatched per-UUID via `async_dispatcher_send` and consumed directly by entities. The inspector drawer shows state names and UUIDs but not live values.
- Python logging hierarchy: `custom_components.loxone` logger defaults to WARNING in HA. The subscribe_logs handler attaches at DEBUG but only receives records that pass the logger's effective level.

---

## 2026-04-03 — Docs accuracy pass

### Changes
- **ARCHITECTURE.md** — updated runtime deps (httpx → async-upnp-client), added repairs.py and frontend monitor/console/status views to directory listing, updated panel tabs list, added coordinator lifecycle description, corrected event routing to dispatcher model, added scene platform section, added config flow validation/discovery/reconfigure descriptions
- **HA_INTEGRATION.md** — updated config flow to describe HTTP validation, reauth, reconfigure, DHCP discovery; updated coordinator section (removed debug print, added structure polling/repairs/dispatcher); corrected event routing from broadcast to per-UUID dispatcher; updated scene class name (LoxoneLightScene) and noted device_info/entry_id scoping; deprecated get_miniserver_from_hass in favor of runtime_data
- **ISSUES_AND_TODOS.md** — expanded test_config_flow.py coverage description with new tests (reauth, reconfigure, DHCP, duplicate serial, etc.); updated test_sensor.py with meter mismatch tests; updated ARCH-002 to reflect coordinator's active role; marked Tier 2 config flow tests largely complete; clarified IMP-007 sync/async intentional design

---

## 2026-04-03 — Gold/Platinum quality scale push

### Decisions
- EntityCategory.CONFIG is not needed — no entities represent Loxone configuration settings
- DHCP discovery (MAC prefix 50:4F:94) chosen over SSDP as it's simpler and more reliable
- Stale device removal now validates against the current structure file before allowing removal
- `token_expired` repair issue made fixable with a RepairsFlow that triggers reauth

### Changes
- **Config flow: reconfigure step** — added `async_step_reconfigure` so users can update connection settings from the integration "..." menu without removing/re-adding
- **Config flow: DHCP discovery** — added `async_step_dhcp` and `dhcp` manifest entry for automatic discovery of Loxone Miniservers on the network via their MAC prefix
- **Options flow error keys** — replaced hardcoded English error strings with translation keys (`username_not_latin1`, `password_not_latin1`)
- **Fixable repair issue** — `token_expired` is now `is_fixable=True` with a `RepairsFlow` in new `repairs.py` that triggers reauth when the user clicks "Fix"
- **Stale device cleanup** — `async_remove_config_entry_device` now checks whether the device's identifiers match active Loxone controls before allowing removal
- **Scene hardening** — `LoxoneLightScene` now has `device_info` (linked via Miniserver serial) and scopes `SENDDOMAIN` events with `miniserver` entry_id for multi-entry safety
- **LoxoneConfigEntry typing** — all 14 platform files, `__init__.py`, and `diagnostics.py` now use `LoxoneConfigEntry` instead of bare `ConfigEntry`
- **Config flow test coverage** — added 11 new tests: reauth success/failure, reconfigure success/failure, duplicate serial abort, HTTP 500, options latin-1 username/password, bridge unknown control, DHCP discovery, DHCP already-configured abort

### Test results
- 376 tests pass (was 365)

---

## 2026-04-03 — Type `LoxoneConfigEntry` on platform setup and core hooks

### Changes

- **`__init__.py`:** `async_setup_entry` and `async_remove_config_entry_device` now annotate `config_entry` as `LoxoneConfigEntry`; `async_setup_entry` adds `hass` / return type annotations.
- **Platform modules + `diagnostics.py`:** Import `LoxoneConfigEntry` from the package and use it for `async_setup_entry` (or `async_get_config_entry_diagnostics` in diagnostics). Removed unused `ConfigEntry` imports where only the setup signature used it.

### Testplan

- `python -m pytest tests/ -q` — 365 passed.

---

## 2026-04-03 — Panel: structure diff in status view

### Decisions

- Structure diff is computed in the coordinator before triggering a config entry reload. The diff (added/removed/changed controls) is stored in `hass.data` keyed by entry_id so it survives the reload (which creates a new coordinator instance).
- On initial connect, a baseline snapshot of controls is stored. The first structure change produces a meaningful diff; before that, "No changes detected" is shown.
- The diff is displayed in the Status tab of the Loxone panel, below the diagnostics section. Shows added (+), removed (−), and changed (~) controls with names, types, and rooms.

### Changes

- **`coordinator.py`:** Added `STRUCTURE_DIFF_KEY`, `_snapshot_controls()` (called on connect), `_compute_structure_diff()` (called before reload). Diff stored in `hass.data`.
- **`websocket.py`:** Added `ws_get_structure_diff` handler, registered in `register_panel`.
- **`types.ts`:** Added `StructureDiffEntry`, `StructureChangedEntry`, `GetStructureDiffResult` interfaces.
- **`api.ts`:** Added `fetchStructureDiff` function.
- **`status-view.ts`:** Added `_renderStructureDiff()` method, fetches diff alongside status, renders added/removed/changed controls.
- **`loxone-panel.js`:** Rebuilt.

### Testplan

- `python -m pytest tests/ -v` — 363 passed, 3 warnings.
- Deploy, open Status tab — verify "No changes detected" on fresh load.
- Modify a control in Loxone Config, wait for structure poll, verify diff appears.

---

## 2026-04-03 — Panel: live monitor + command console

### Decisions

- Live monitor uses HA's WS subscription pattern (`subscribeMessage`). The coordinator fires a `loxone_{entry_id}_monitor` signal on every message batch, and the `loxone/subscribe_events` handler forwards events to subscribed panel connections with resolved control names and rooms.
- Command console uses a new `loxone/send_command` WS command (admin-only) that wraps `coordinator.api.send_websocket_command(uuid, command)`. Accepts any command string the Loxone WS API supports (On, Off, pulse, numeric values, etc.).
- Both views support multi-Miniserver via the `miniserver` param.
- Console includes UUID autocomplete from known controls (fetched from `loxone/get_devices`) and persistent command history in localStorage.
- Monitor keeps the last 500 events in a ring buffer with pause/resume and text filtering by name, room, or UUID.

### Changes

- **`coordinator.py`:** Added `monitor_signal` property. `_message_callback` now also fires the monitor signal with the full message batch.
- **`websocket.py`:** Added `ws_subscribe_events` (subscription handler) and `ws_send_command` (async response). Registered both in `register_panel`.
- **`types.ts`:** Added `MonitorEvent`, `MonitorEventMessage`, `SendCommandResult` interfaces. Extended `HomeAssistant` type with `connection.subscribeMessage`.
- **`api.ts`:** Added `sendCommand` function.
- **`monitor-view.ts`:** New — scrolling event log with pause/resume, filter, auto-scroll, status indicator.
- **`console-view.ts`:** New — UUID input with autocomplete, command input, send button, persistent history table.
- **`loxone-panel.ts`:** Added Monitor and Console tabs between Bridges and Status.
- **`loxone-panel.js`:** Rebuilt.

### Testplan

- `python -m pytest tests/ -v` — 363 passed, 3 warnings.
- Deploy, open Loxone panel, switch to Monitor tab — verify events stream in real-time.
- Switch to Console tab, type a UUID or control name, send a command, verify history persists.

---

## 2026-04-03 — Energy dashboard integration for Loxone meters

### Decisions

- Meter subsensors now get guaranteed `device_class` + `state_class` classification based on `details["type"]` from the Loxone structure file ("energy", "water", "gas"), not just the format string. This makes them reliably visible in HA's Energy, Water, and Gas dashboards even if the Loxone format string doesn't exactly match known units.
- Renamed "Total Neg" subsensor to "Total Returned" — clearer for energy dashboard configuration where it represents returned/exported energy.
- The format-string-based detection (from `SENSOR_TYPES`) takes priority when it matches. The new `_METER_CLASSIFICATION` fallback only kicks in when the format string doesn't produce a match, ensuring no regressions for existing setups.
- Fallback also provides a canonical unit (e.g. kWh, W, L) when `_clean_unit` can't parse one from the format string.

### Changes

- **`sensor.py`:** Added `_METER_CLASSIFICATION` mapping (energy/water/gas × actual/total/totalNeg/storage → device_class + state_class + fallback unit). `LoxoneMeterSensor.__init__` applies classification when `entity_description` wasn't assigned by format matching. Meter setup loop passes `meter_type` and `meter_state_key` to each subsensor. `totalNeg` suffix renamed "Total Neg" → "Total Returned". Added `UnitOfVolume` import.
- **`test_sensor.py`:** Added 4 new tests: `test_meter_total_energy_dashboard_attrs`, `test_meter_total_returned_energy_dashboard_attrs`, `test_meter_actual_state_class`, `test_meter_fallback_classification_from_type`. Updated entity ID reference for renamed Total Returned subsensor.

### Testplan

- `python -m pytest tests/ -v` — 363 passed, 3 warnings.
- Deploy and verify meter sensors appear in HA Energy Dashboard config as eligible energy sources.

---

## 2026-04-03 — Phase 7: Multi-Miniserver hardening + panel

### Decisions

- Every entity now stores a direct reference to its `LoxoneCoordinator` (passed via `coordinator=coordinator` kwarg), eliminating all use of the global `get_miniserver_from_hass` helper. Platform `async_setup_entry` functions retrieve the coordinator from `config_entry.runtime_data`.
- Dispatcher signals are namespaced by entry_id: `loxone_{entry_id}_uuid_{uuid}`. Prevents cross-talk when multiple Miniservers are configured.
- Repair issue IDs are namespaced: `token_expired_{entry_id}`, `persistent_disconnect_{entry_id}`. Each Miniserver's issues are tracked independently.
- `_get_coordinator()` in websocket.py now accepts an optional `entry_id` parameter to select among multiple entries. Defaults to the first entry when not specified.
- All WebSocket API handlers (`ws_get_devices`, `ws_get_areas`, `ws_get_bridges`, `ws_get_status`, etc.) accept an optional `entry_id` field.
- New `loxone/list_entries` WS command returns all configured Loxone entries (entry_id, title, host, serial, name).
- Frontend panel shows an entry selector dropdown when multiple Miniservers are configured. All API calls pass the selected `entry_id`.
- System health aggregates info from all configured entries when multiple are present.
- `_async_sync_device_names` and `_async_sync_areas` accept an optional `coordinator` parameter for per-entry context.
- `loxone_send` bus listener filters by `entry_id` to prevent cross-Miniserver command execution.

### Changes

- **`__init__.py`:** Removed `get_miniserver_from_hass`. `LoxoneEntity` stores `_coordinator`, uses `_resolve_coordinator()` fallback. `_dispatcher_prefix()` returns entry-scoped signal prefix. `loxone_send` handler filters by `entry_id`. Sync functions accept optional coordinator.
- **`coordinator.py`:** Added `dispatcher_prefix` property. Namespaced repair issue IDs in `_async_reconnect`.
- **Platform files (all 12):** Replaced `get_miniserver_from_hass` → `config_entry.runtime_data`. Pass `coordinator=coordinator` to every entity constructor.
- **`bridge.py`:** Uses `self.coordinator.dispatcher_prefix` for dispatcher subscriptions.
- **`websocket.py`:** All handlers accept `entry_id`. Added `ws_list_entries`. `_get_coordinator` resolves by `entry_id`.
- **`system_health.py`:** Iterates all entries; shows per-Miniserver details when multiple are configured.
- **Frontend (`api.ts`, `types.ts`, `loxone-panel.ts`, all views):** Added `fetchEntries`, entry selector UI, `entryId` property on all views, `entry_id` in all API calls.
- **Tests:** `conftest.py:fire_loxone_event` accepts `entry_id`, uses namespaced signals. `test_repairs.py` asserts namespaced issue IDs. `test_bridge.py` sets `mock_coordinator.dispatcher_prefix` to match entry.

### Testplan

- `python -m pytest tests/ -v` — 359 passed, 3 warnings.
- Deploy and verify single-Miniserver setup works unchanged.
- If available, configure a second Miniserver and verify panel selector, independent state updates, and separate repair issues.

---

## 2026-04-03 — Phase 6: Bridge improvements + system health

### Decisions

- Added `NumberMapper` (number/input_number ↔ Slider VI, bidirectional) and `InputBooleanMapper` (input_boolean ↔ Switch VI, bidirectional) to bridge mappers.
- Added mapper validation at add-time in WebSocket `add_bridge` handler — returns `unsupported_bridge` error with a clear message before attempting activation.
- Trimmed frontend `BRIDGEABLE_DOMAINS` to match backend mapper support (removed climate, cover, fan, media_player, lock, button, select, input_select which have no mappers).
- Wired up `system_health.py` by adding `"system_health"` to `manifest.json` dependencies. Enhanced to show connection state.
- IMP-007 (sync/async bus.fire) deferred — entity service methods run in threads, so `hass.bus.fire` (thread-safe) is correct. Needs per-method analysis, not blanket replace.

### Changes

- **`bridge_mappers.py`:** Added `NumberMapper` and `InputBooleanMapper`. Added `_SUPPORTED_DOMAINS` frozenset. Extended `get_mapper` factory.
- **`websocket.py`:** Pre-validates mapper compatibility in `ws_add_bridge` before activation.
- **`bridges-view.ts` + `loxone-panel.js`:** Reduced `BRIDGEABLE_DOMAINS` to supported set. Rebuilt panel JS.
- **`system_health.py`:** Enhanced to show connection state. Fixed to work when miniserver is None.
- **`manifest.json`:** Added `"system_health"` dependency.

### Testplan

- `python -m pytest tests/ -v` — 358 passed, 3 warnings.
- Deploy and test: add a number/input_boolean bridge in the panel.
- Verify System Health page shows Loxone info.

---

## 2026-04-03 — Phase 5b: Structure hash polling

### Decisions

- Detect Miniserver structure changes by polling the lightweight `jdev/sps/LoxAPPversion3` endpoint and comparing the `lastModified` value. On change, trigger `async_reload` for a clean entity re-setup. There is no WebSocket push event for structure changes — polling is the documented Loxone approach (per the "Communicating with the Miniserver" PDF).
- Used HA's `async_track_time_interval` instead of a raw asyncio loop — idiomatic, properly tracked, doesn't block `async_block_till_done()` in tests.
- Poll interval is configurable via the options flow (default 300s / 5 minutes, 0 = disabled). Stored as `structure_poll_interval`.
- Errors during polling are silently logged at DEBUG — the integration stays healthy even when the check fails.

### Changes

- **`coordinator.py`:** Added `_start_structure_poll` using `async_track_time_interval`, `_async_poll_structure` callback, and `_check_structure_change` that fetches the structure file via HTTP and compares `lastModified`. Unsubscribes on cleanup. Stores `_structure_last_modified` on initial connect.
- **`const.py`:** Added `CONF_STRUCTURE_POLL_INTERVAL` and `DEFAULT_STRUCTURE_POLL_INTERVAL`.
- **`config_flow.py`:** Added structure poll interval to the settings schema with NumberSelector (0–3600s, box mode).
- **`translations/en.json`, `translations/de.json`:** Added label for `structure_poll_interval`.
- **`tests/test_structure_poll.py`:** New — 4 tests covering change detection, no-change, HTTP error resilience, and skip-when-disconnected.

### Testplan

- `python -m pytest tests/ -v` — 358 passed, 3 warnings.
- Deploy and verify new option appears in settings. Modify a control in Loxone Config and observe auto-reload within 5 minutes.

---

## 2026-04-03 — Phase 5: Redacted diagnostics + repair issues

### Decisions

- Diagnostics now redact sensitive data (credentials, host, token, msInfo, users) while preserving debug-useful info (control types, states, rooms, connection state).
- Repair issues created for two scenarios: token expiration (WARNING) and persistent disconnect after 3 failed reconnects (ERROR). Both auto-clear on successful reconnect.
- Phase 4 (custom device triggers/actions/conditions) skipped — HA auto-provides these through entity platforms now that `has_entity_name=True` and `DeviceInfo` are properly configured.

### Changes

- **`diagnostics.py`:** Rewrote to use `async_redact_data` for config, `_redact_structure` for LoxAPP3.json (redacts msInfo/users, summarises controls without raw details). Includes connection state and miniserver metadata.
- **`coordinator.py`:** Added `ir.async_create_issue` on token error and after 3 reconnect failures. `ir.async_delete_issue` on successful reconnect.
- **`translations/en.json`, `translations/de.json`:** Added `issues` section with `token_expired` and `persistent_disconnect` repair issue strings.
- **`tests/test_diagnostics.py`:** New — 4 tests covering redaction, connection state, miniserver info, and structure sanitisation.
- **`tests/test_repairs.py`:** New — 2 tests covering repair issue creation on token error and clearance on reconnect.

### Testplan

- `python -m pytest tests/ -v` — 354 passed, 3 warnings.
- Deploy to HA and verify diagnostics download redacts sensitive data.
- Simulate disconnection to verify repair issue appears.

---

## 2026-04-03 — Phase 3: Complete has_entity_name migration

### Decisions

- Migrated all structure-file entity classes to `has_entity_name=True`, separating device name from entity name.
- Legacy YAML entities (`LoxoneCustomSensor`, `LoxoneCustomBinarySensor`) intentionally excluded — they're a deprecated configuration path with no device to separate from.
- Light entities under a LightControllerV2 use the channel name as `_attr_name` (suffix) and the controller name as `DeviceInfo.name`. Standalone lights use `_attr_name = None`.
- Meter subsensors use `name_suffix` kwarg for the entity suffix (e.g. "Actual", "Total") while the device name stays the meter control name.
- Removed the old `{room} Climate` name override in `LoxoneRoomController` — the room is already conveyed via `suggested_area` in `DeviceInfo`.

### Changes

- **cover.py:** `LoxoneGate`, `LoxoneWindow`, `LoxoneJalousie` — `_attr_has_entity_name = True`, `_attr_name = None`.
- **climate.py:** `LoxoneRoomController`, `LoxoneRoomControllerV2`, `LoxoneAcControl` — same pattern.
- **fan.py:** `LoxoneVentilation` — same pattern.
- **sensor.py:** `LoxoneTextSensor`, `LoxoneSensor` — same pattern. `LoxoneMeterSensor` — `_attr_name` set from `name_suffix` kwarg.
- **binary_sensor.py:** `LoxoneDigitalSensor` — same pattern. `LoxoneCustomBinarySensor` — removed redundant `_name` field and `name` property override.
- **lights/lightcontroller.py:** `LoxoneLightControllerV2` — `_attr_name = None`.
- **lights/switch.py, dimmer.py, colorpickers.py:** Dual-mode: under controller → `_attr_name = channel name`, `DeviceInfo.name = controller name`; standalone → `_attr_name = None`, `DeviceInfo` from base.

### Testplan

- `python -m pytest tests/ -v` — 348 passed, 3 warnings.
- Deploy to HA and verify entity naming in UI.

---

## 2026-04-03 — Remove _DispatchEvent shim, pass raw dict to event_handler

### Decisions

- The `_DispatchEvent` shim was introduced in Phase 1 so all 26 existing `event_handler(self, e)` methods could work unchanged with `e.data` while migrating from the event bus to dispatchers. Now that the migration is stable and tested, the shim is unnecessary indirection — every handler should just accept the raw `dict` directly.

### Changes

- **`__init__.py`:** Deleted `_DispatchEvent` class. `_dispatch_handler` now calls `event_handler(message)` directly. Base `event_handler` signature updated to `event_handler(self, data: dict) -> None`. Removed unused `EVENT` import.
- **All 26 `event_handler` implementations** across 14 files: replaced `e.data[...]` / `event.data[...]` with `e[...]` / `event[...]`. Files: `sensor.py`, `binary_sensor.py`, `climate.py`, `fan.py`, `cover.py`, `switch.py`, `alarm_control_panel.py`, `media_player.py`, `button.py`, `number.py`, `text.py`, `lights/lightcontroller.py`, `lights/colorpickers.py`, `lights/switch.py`, `lights/dimmer.py`.
- **`docs/ARCHITECTURE.md`:** Updated event-flow diagram to reflect raw dict forwarding.
- Removed stale commented-out `_LOGGER.debug` lines referencing `event.data` in climate and fan handlers.

### Testplan

- `python -m pytest tests/ -v` — 348 passed, 3 warnings (harmless mock coroutine noise).

---

## 2026-04-03 — Phase 2+3a: API decomposition, typed model, has_entity_name migration

### Decisions

- Extracted crypto into `crypto.py` (pure functions), deleted dead code (`helper.py`, `api.py`), consolidated duplicate exception hierarchy.
- Created typed structure model (`structure.py`) with `LoxoneStructure`, `MsInfo`, `LoxoneRoom`, `LoxoneCategory`, `LoxoneControl` dataclasses.  Integrated into `MiniServer` alongside backward-compatible dict access.
- Cleaned up `message.py` (removed unused timer classes, improved type annotations).
- Started Phase 3 `has_entity_name=True` migration on 6 simple platforms: button, number, text, switch, alarm_control_panel, media_player.  Each entity class now properly separates device name (from `_loxone_name`) from entity name (`None` for single-entity-per-device).
- Fixed a subtle init ordering bug: `_attr_name` must be set before any `hasattr(self, "name")` check to avoid caching stale values.  Restructured `LoxoneEntity.__init__` to handle "name" early and skip it in the generic kwarg loop.

### Changes

- **`pyloxone_api/crypto.py`:** New — pure AES/RSA/HMAC functions.
- **`pyloxone_api/structure.py`:** New — typed LoxAPP3.json model.
- **`pyloxone_api/connection.py`:** Single class, uses crypto imports, `_handle_text_event()` extracted.
- **`pyloxone_api/exceptions.py`:** Consolidated; legacy names are aliases.
- **`pyloxone_api/message.py`:** Removed AsyncTimer/SyncTimer, improved annotations.
- **`miniserver.py`:** Properties delegate to `self.structure`, `LoxoneStructure` integrated.
- **`__init__.py`:** `_loxone_name` stored separately for `device_info`; `_attr_name` set conditionally (only when kwargs has "name"); removed `@cached_property def name` override.
- **Platforms (button, number, text, switch, alarm, media_player):** `_attr_has_entity_name = True`, `_attr_name = None`, removed boilerplate properties (`icon`, `should_poll`, `assumed_state`).
- **Deleted:** `helper.py`, `api.py`.
- **Tests:** 39 new tests (crypto + structure). Total: 348 passing.

---

## 2026-04-03 — Phase 2a: Decompose connection.py, typed structure model

### Decisions

- Extracted all cryptographic operations from the 1420-line `connection.py` "god object" into a new `crypto.py` module with pure, stateless functions.  This makes crypto operations independently testable and reduces `connection.py` to ~500 lines focused on the WebSocket lifecycle.
- Eliminated the `LoxoneBaseConnection` → `LoxoneConnection` inheritance hierarchy in favor of a single `LoxoneConnection` class that composes crypto functions via imports.
- Consolidated the dual exception hierarchy: `ConnectionFailure`, `UnauthorizedError`, `ResponseError`, `HttpApiError`, `MessageError` are now aliases pointing to the canonical `Loxone*` exceptions.  All exceptions now properly inherit from `LoxoneException`.
- Deleted dead code: `helper.py` (never imported), `api.py` (empty placeholder).
- Created typed structure file model (`structure.py`) with `LoxoneStructure`, `MsInfo`, `LoxoneRoom`, `LoxoneCategory`, `LoxoneControl` dataclasses.  Integrated into `MiniServer` as a `structure` attribute while preserving backward-compatible `lox_config.json` dict access.

### Changes

- **`pyloxone_api/crypto.py`:** New module — `generate_aes_key()`, `generate_iv()`, `generate_salt()`, `new_salt_needed()`, `encrypt_command()`, `decrypt_command()`, `make_session_key()`, `parse_public_key()`, `hash_credentials()`, `hash_token()`, `hash_secure_command()`.
- **`pyloxone_api/structure.py`:** New module — `LoxoneStructure.from_dict()`, `MsInfo`, `LoxoneRoom`, `LoxoneCategory`, `LoxoneControl` with `get_state_uuids()`, `controls_by_type()`, `room_name()`, `category_name()`.
- **`pyloxone_api/connection.py`:** Rewritten — single `LoxoneConnection` class using `crypto.py` functions.  Removed `LoxoneBaseConnection`.  Extracted `_handle_text_event()` from the 250-line `_websocket_event()` for readability.
- **`pyloxone_api/exceptions.py`:** All exceptions inherit from `LoxoneException`.  Legacy names are aliases.
- **`miniserver.py`:** Properties now delegate to `self.structure` (typed model) instead of raw dict traversal.
- **Deleted:** `pyloxone_api/helper.py`, `pyloxone_api/api.py`.
- **Tests:** 39 new tests — 21 for `crypto.py` (key gen, salt expiry, AES roundtrip, HMAC hashing, RSA, public key parsing), 18 for `structure.py` (parsing, lookups, edge cases).  Total suite: 348 tests (up from 309).
- **Docs:** Updated `API_LAYER.md` (module map, crypto/structure sections, exception tree, resolved design concerns), `ISSUES_AND_TODOS.md` (removed IMP-001, IMP-005, trimmed IMP-006).

### Test Results

- 348 tests pass, 3 pre-existing warnings (mock coroutine noise).

---

## 2026-04-03 — Phase 0+1: runtime_data, O(1) dispatch, reauth, config flow rewrite

### Decisions

- Adopted `ConfigEntry.runtime_data` as the typed storage for `LoxoneCoordinator`, eliminating `hass.data[DOMAIN][entry_id]` lookups across 20+ files.
- Switched from `SchemaConfigFlowHandler` to standard `ConfigFlow` to enable `async_step_reauth` and proper `unique_id` fetching via Miniserver serial (MAC).
- Replaced `hass.bus.async_fire(EVENT, message)` O(entities×events) broadcast with per-UUID `async_dispatcher_send` for O(1) entity routing — the single highest-impact performance change.
- Used a `_DispatchEvent` shim so all 25 existing `event_handler` implementations work unchanged with the new dispatcher.
- Fixed listener leak in `LoxoneEntity.async_will_remove_from_hass` — bus listener was set to `None` without calling the unsubscribe callable.
- Set `PARALLEL_UPDATES = 0` on all 12 platform files (required for non-polling integrations on the HA Quality Scale).

### Changes

- **`__init__.py`:** `type LoxoneConfigEntry`, `_DispatchEvent` shim, `_get_state_uuids()` + `_dispatch_handler()` on `LoxoneEntity`, `_get_coordinator` iterates config entries, listener leak fix, reauth trigger on `LoxoneUnauthorisedError`.
- **`coordinator.py`:** `_message_callback` now dispatches `loxone_uuid_{uuid}` per UUID instead of bus fire.
- **`miniserver.py`:** `get_miniserver_from_hass` iterates config entries instead of `hass.data[DOMAIN]`.
- **`websocket.py`:** `_get_coordinator` iterates config entries.
- **`diagnostics.py`:** Uses `config_entry.runtime_data`.
- **`system_health.py`:** Iterates config entries with typed coordinator access.
- **`config_flow.py`:** Full rewrite — `LoxoneFlowHandler(ConfigFlow)` with live connection test, serial-based `unique_id`, `async_step_reauth`/`reauth_confirm`, `LoxoneOptionsFlowHandler` with menu (settings + device bridges).
- **`bridge.py`:** Loxone-side listeners use `async_dispatcher_connect` per subscribe UUID.
- **`alarm_control_panel.py`:** Removed redundant `hass.bus.async_listen(EVENT, ...)` — base class handles it.
- **All 12 platform files:** Added `PARALLEL_UPDATES = 0`.
- **`translations/en.json`, `de.json`:** Added `reauth_confirm` step, `already_configured`/`reauth_successful` abort reasons, `username_not_latin1`/`password_not_latin1` errors.
- **Tests:** All `hass.data[DOMAIN][entry.entry_id]` → `entry.runtime_data`, all `hass.bus.async_fire(EVENT, ...)` → `fire_loxone_event(hass, ...)` helper, updated error expectations for new config flow.

### Test results

- 309 passed, 0 failures, 3 warnings (mock coroutine noise from serial fetch)

---

## 2026-04-02 — Panel polish, Status tab, sync fixes

### Decisions

- Switched panel to `embed_iframe=False` so it renders in HA's DOM and inherits theme CSS variables (dark mode fix).
- Added MD5-based cache-busting hash to the panel JS URL so browser always loads the latest bundle after a deploy.
- Deploy script now builds the frontend (`node build.mjs`) automatically before syncing, with `npm ci` on first run.
- Area sync now also reads the Loxone structure file's `rooms` dict directly, so empty rooms (no controls/entities) still get HA areas created.
- Diagnostics separates disabled entities from enabled-but-stateless entities to avoid false positives from bridged controls.

### Changes

- **`websocket.py`:** `embed_iframe=False`, cache-busting `?v=<md5>` on `module_url`, new `loxone/get_status` WS command (connection health, Miniserver metadata, diagnostics).
- **`__init__.py`:** `_async_sync_areas` now creates HA areas for all Loxone rooms from the structure file (not just rooms that have entities).
- **`scripts/deploy`:** Added `npm ci` + `node build.mjs` step before rsync.
- **`frontend/bridges-view.ts`:** Replaced raw text inputs with searchable combo boxes for both HA entities (grouped by domain) and Loxone controls (grouped by room). Added state column with live entity values and direction arrow (→).
- **`frontend/devices-view.ts`:** Sortable column headers (name, type, room, entities). Refresh button. Domain breakdown in summary (e.g. "42 sensor, 18 light, 12 switch").
- **`frontend/status-view.ts` (new):** Status tab with Connection/Configuration cards and Diagnostics section (connection health, entities without state, disabled entity count, bridge count, integration summary).
- **`frontend/loxone-panel.ts`:** Added Status tab.
- **`frontend/src/api.ts`, `types.ts`:** Added `fetchStatus` and `GetStatusResult`.

### Test results

- 16 WS Python tests pass, 14 init tests pass
- 10 Vitest frontend tests pass
- Deployed and verified on live HA instance (dark mode, area sync, entity picker, status tab)

---

## 2026-03-31 — Loxone Custom Panel (sidebar dashboard)

### Decisions

- Built a custom panel (sidebar app) for managing Loxone integration, similar to the KNX integration's approach.
- Used **Lit/TypeScript** for the frontend, bundled with **esbuild** (Rollup was too slow for Lit's dependency tree). Frontend source lives in `custom_components/loxone/frontend/src/`, bundle outputs to `frontend/loxone-panel.js`.
- **Hybrid API approach**: WebSocket commands (`loxone/get_devices`, `loxone/get_areas`, `loxone/get_bridges`, `loxone/set_entity_enabled`, `loxone/add_bridge`, `loxone/remove_bridge`) for data queries and mutations; existing HA services (`loxone.sync_areas`, `loxone.sync_device_names`) for sync actions.
- WS commands registered in `async_setup` (always available), panel registration in `async_setup_entry` (gracefully fails if `panel_custom` unavailable, e.g. in tests).
- Panel registration is optional — `panel_custom` is NOT in manifest dependencies to avoid breaking tests (no `hass_frontend` in test env). Instead, `async_setup_component` is called dynamically.
- Multi-layer testing: **pytest** for WS API commands (16 tests), **Vitest** for frontend API helpers (10 tests), TypeScript type checking via `tsc --noEmit`.
- **Aligned with KNX platinum pattern:** single `register_panel()` coroutine (WS + panel), `after_dependencies: ["panel_custom"]`, `dependencies: ["http", "websocket_api"]`, `frontend_panels` guard for double-registration prevention.

### Changes

- **`websocket.py` (new):** Single `register_panel()` entry point (KNX pattern) — registers WS commands and sidebar panel together from `async_setup_entry`.
- **`frontend/` (new):** Lit/TypeScript panel with four tabs — Devices (side-by-side table with enable/disable), Areas (room mapping + sync), Bridges (CRUD), Status (connection health + diagnostics).
- **`__init__.py`:** Calls `register_panel(hass)` from `async_setup_entry`.
- **`manifest.json`:** Added `after_dependencies: ["panel_custom"]`, `dependencies: ["http", "websocket_api"]`.
- **`.gitignore`:** Added `frontend/node_modules/`.
- **`test_websocket.py` (new):** 16 tests covering all WS commands.
- **`frontend/test/api.test.ts` (new):** 10 Vitest tests for all API functions.

### Test results

- 309 Python tests pass (16 new)
- 10 Vitest frontend tests pass (all new)
- TypeScript typechecks clean

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

