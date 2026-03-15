# Lights Subsystem Deep Dive

> Technical analysis of `custom_components/loxone/light.py` and `custom_components/loxone/lights/`

## Overview

The lights subsystem maps Loxone light controls to Home Assistant `LightEntity` instances. It supports five distinct light types with varying color modes, grouped under an optional `LightControllerV2` mood/scene controller.

## Architecture

```
light.py (platform entry point)
│
├── async_setup_entry()
│     │
│     ├── Standalone Dimmers ──────────► LoxoneDimmer / EIBDimmer
│     │
│     └── For each LightControllerV2:
│           │
│           ├── LoxoneLightControllerV2 (mood/scene controller)
│           │
│           └── If subcontrols enabled:
│                 ├── Switch subcontrol ──► LoxoneLightSwitch
│                 ├── Dimmer subcontrol ──► LoxoneDimmer / EIBDimmer
│                 └── ColorPickerV2 ──────► RGBColorPicker
│                                           TunableWhiteLight
│                                           LumiTech
│
lights/
├── __init__.py          (empty)
├── switch.py            LoxoneLightSwitch      — ColorMode.ONOFF
├── dimmer.py            LoxoneDimmer/EIBDimmer  — ColorMode.BRIGHTNESS
├── colorpickers.py      TunableWhiteLight       — ColorMode.COLOR_TEMP
│                        RGBColorPicker          — ColorMode.HS + COLOR_TEMP
│                        LumiTech                — (extends RGBColorPicker)
└── lightcontroller.py   LoxoneLightControllerV2 — ONOFF/BRIGHTNESS + EFFECT
```

## Entity Type Matrix

| Entity                    | Color Modes              | Brightness | Effects    | WS Commands                        |
|---------------------------|--------------------------|------------|------------|------------------------------------|
| `LoxoneLightSwitch`       | `ONOFF`                  | No         | No         | `on`, `off`                        |
| `LoxoneDimmer`            | `BRIGHTNESS`             | 0–100      | No         | `{value}`, `On`, `Off`             |
| `EIBDimmer`               | `BRIGHTNESS`             | 0–100      | No         | Same as Dimmer                     |
| `TunableWhiteLight`       | `COLOR_TEMP`             | Yes        | No         | `temp(brightness%,kelvin)`, `setBrightness/0`, `On` |
| `RGBColorPicker`          | `HS`, `COLOR_TEMP`       | Yes        | No         | `hsv(h,s,v)`, `temp(brightness%,kelvin)`, `setBrightness/0`, `On` |
| `LumiTech`                | `HS`, `COLOR_TEMP`       | Yes        | No         | Same as RGBColorPicker             |
| `LoxoneLightControllerV2` | `ONOFF` or `BRIGHTNESS`  | If master  | Yes (moods)| `changeTo/{mood_id}`, `addMood/{id}` |

## Discovery Flow (`light.py`)

```python
async_setup_entry(hass, config_entry, async_add_entities):
    # 1. Check if subcontrol generation is enabled
    generate_subcontrols = options.get("generate_lightcontroller_subcontrols", False)

    # 2. Collect standalone dimmers
    dimmers = get_all("Dimmer") + get_all("EIBDimmer")

    # 3. For each LightControllerV2
    for controller in get_all("LightControllerV2"):
        entities.append(LoxoneLightControllerV2(controller))

        if generate_subcontrols:
            for uuid, sub in controller["subControls"].items():
                # Skip master controls
                if uuid.find("masterValue") > -1:
                    ...  # use as master dimmer for controller
                if uuid.find("masterColor") > 1:  # BUG: should be > -1
                    continue

                # Remove from standalone dimmers list
                dimmers = [d for d in dimmers if d["uuidAction"] != sub["uuidAction"]]

                # Create appropriate entity based on type
                match sub["type"]:
                    case "Switch":     → LoxoneLightSwitch
                    case "Dimmer":     → LoxoneDimmer
                    case "EIBDimmer":  → EIBDimmer
                    case "ColorPickerV2":
                        match sub["details"]["pickerType"]:
                            case "Lumitech":      → LumiTech
                            case "Rgb":            → RGBColorPicker
                            case "TunableWhite":   → TunableWhiteLight

    # 4. Create remaining standalone dimmers
    for dimmer in dimmers:
        entities.append(LoxoneDimmer(dimmer) or EIBDimmer(dimmer))
```

## Light Switch (`lights/switch.py`)

The simplest light type — binary on/off.

### State Flow

```
Event: states["active"] = 1.0 → is_on = True
Event: states["active"] = 0.0 → is_on = False
```

### Commands

```python
async_turn_on():  hass.bus.async_fire("loxone_send", {"uuid": uuidAction, "value": "on"})
async_turn_off(): hass.bus.async_fire("loxone_send", {"uuid": uuidAction, "value": "off"})
```

**Note:** Uses lowercase `"on"` / `"off"` while dimmers use capitalized `"On"` / `"Off"`. Both work with the Miniserver, but the inconsistency is worth noting.

## Dimmer (`lights/dimmer.py`)

Supports brightness via a 0–100 Loxone value mapped to HA's 0–255 range.

### State UUIDs

| State Key  | Purpose             |
|------------|---------------------|
| `position` | Current brightness  |
| `min`      | Minimum value       |
| `max`      | Maximum value       |
| `step`     | Step increment      |

### Brightness Mapping

```
Loxone: 0–100 (or custom min–max)
   ↕
HA:     0–255

Incoming:  lox2hass_mapped(position, min, max)  or  lox_to_hass(position)
Outgoing:  round(hass_to_lox(brightness))
```

When `min` and `max` are known (from events), `lox2hass_mapped` scales proportionally. Otherwise, simple `lox_to_hass` assumes 0–100.

### Commands

```python
async_turn_on(brightness=None):
    if brightness:
        value = round(hass_to_lox(brightness))  # 0–255 → 0–100
    else:
        value = "On"
    hass.bus.async_fire("loxone_send", {"uuid": uuidAction, "value": value})

async_turn_off():
    hass.bus.async_fire("loxone_send", {"uuid": uuidAction, "value": "Off"})
```

## Color Pickers (`lights/colorpickers.py`)

### TunableWhiteLight

Supports color temperature only (2000–6500 K).

**State parsing** — Loxone sends strings like `temp(50,3000)`:

```python
def event_handler(self, event):
    color_str = event.data[states["color"]]
    _color = eval(color_str)  # ⚠ eval() — returns tuple (brightness%, kelvin)
    self._attr_brightness = round(255 * _color[0] / 100)
    self._attr_color_temp_kelvin = _color[1]
```

**Commands:**

```python
async_turn_on(color_temp_kelvin=None, brightness=None):
    if color_temp_kelvin:
        bri = hass_to_lox(brightness or self._attr_brightness)
        cmd = f"temp({bri},{color_temp_kelvin})"
    elif brightness:
        cmd = f"temp({hass_to_lox(brightness)},{self._attr_color_temp_kelvin})"
    else:
        cmd = "On"

async_turn_off():
    cmd = "setBrightness/0"
```

### RGBColorPicker

Supports both HS color and color temperature modes, switching based on the last command type.

**State parsing** — Loxone sends either `hsv(180,100,80)` or `temp(50,3000)`:

```python
def event_handler(self, event):
    color_str = event.data[states["color"]]
    if color_str.startswith("hsv"):
        _color = eval(color_str)  # (h, s, v)
        self._attr_color_mode = ColorMode.HS
        self._attr_hs_color = (_color[0], _color[1])
        self._attr_brightness = lox_to_hass(_color[2])
    elif color_str.startswith("temp"):
        _color = eval(color_str)  # (brightness%, kelvin)
        self._attr_color_mode = ColorMode.COLOR_TEMP
        ...
```

**Commands:**

```python
# HS color mode
cmd = f"hsv({hs_color[0]},{hs_color[1]},{hass_to_lox(brightness)})"

# Color temp mode
cmd = f"temp({hass_to_lox(brightness)},{color_temp_kelvin})"
```

### LumiTech

Subclass of `RGBColorPicker` with only a different device info block and icon. Functionally identical.

## Light Controller V2 (`lights/lightcontroller.py`)

A mood/scene controller that manages groups of lights. Each mood is exposed as an HA "effect".

### State UUIDs

| State Key          | Purpose                          |
|--------------------|----------------------------------|
| `activeMoods`      | List of active mood IDs          |
| `moodList`         | Available moods with metadata    |
| `additionalMoods`  | Extra moods from subcontrols     |

### Master Dimmer

If any subcontrol has `masterValue` in its UUID and is a Dimmer/EIBDimmer type, it serves as the controller's brightness control:

```python
if sub_uuid.find("masterValue") > -1 and sub["type"] in ("Dimmer", "EIBDimmer"):
    self._master_value_uuid = sub["uuidAction"]
    self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    # instead of ONOFF
```

### Mood Management

```python
# Effect list (moods)
effect_list = [mood["name"] for mood in self._moodlist]

# Turn on specific mood
async_turn_on(effect=mood_name):
    mood_id = next(m["id"] for m in self._moodlist if m["name"] == mood_name)
    cmd = f"changeTo/{mood_id}"

# Turn on (default)
async_turn_on():
    if state == STATE_OFF:
        cmd = "changeTo/99"   # All-on mood

# Turn off
async_turn_off():
    cmd = "changeTo/0"        # All-off mood
```

### Is-On Logic

```python
@property
def is_on(self):
    return self._active_moods != [778]  # 778 = "All Off" mood ID
```

This is fragile — `[778]` is a magic number, and empty/uninitialized `_active_moods` will incorrectly report as "on".

### State Parsing (eval!)

Mood lists come as string representations of Python data structures:

```python
# Loxone sends: "[{'id': 1, 'name': 'Bright', 'static': true}]"
# Code does:
mood_list_str = mood_list_str.replace("true", "True").replace("false", "False")
self._moodlist = eval(mood_list_str)
```

## Issues Summary

### Critical

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 1 | `eval()` used to parse Loxone data strings | colorpickers.py, lightcontroller.py | Security: arbitrary code execution if data is crafted |
| 2 | `RGBColorPicker.async_turn_on` — `self._attr_brightness` can be `None` when setting HS color | colorpickers.py:177-179 | `TypeError` crash |
| 3 | `RGBColorPicker.async_turn_on` — `self._attr_hs_color` can be `None` when setting brightness in HS mode | colorpickers.py:201-204 | `TypeError` crash |

### High

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 4 | `masterColor` filter uses `> 1` instead of `> -1` | light.py | masterColor subcontrols incorrectly included as entities |
| 5 | Standalone `ColorPickerV2` controls never discovered | light.py | Missing light entities |
| 6 | `TunableWhiteLight.async_turn_on` — brightness/color_temp can be `None` on first call | colorpickers.py:72-83 | Crash or wrong command |

### Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 7 | `_LOGGER.error("msg ->", value)` — second arg not a format arg | colorpickers.py:103,243 | Broken log messages |
| 8 | `LoxoneLightControllerV2.is_on` — magic number 778, fragile for empty list | lightcontroller.py | Incorrect on/off state |
| 9 | `get_or_create_device(None, ...)` when no light controller | colorpickers.py:45-47 | Device registry pollution |
| 10 | Inconsistent command casing: `"on"`/`"off"` vs `"On"`/`"Off"` | switch.py vs dimmer.py | Works but confusing |

### Low

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 11 | `__color_mode_reported` — unused attribute | colorpickers.py:115 | Dead code |
| 12 | `_sequence_uuid` — set but never used | colorpickers.py:129 | Dead code |
| 13 | `async_setup_platform` returns `True` instead of `None` | light.py | HA convention violation |
| 14 | Deprecated `DeviceInfo` import path | dimmer.py, lightcontroller.py | Future HA version breakage |

## Recommendations

1. **Replace all `eval()` calls** with `ast.literal_eval()` or regex-based parsers for `hsv()`, `temp()`, mood lists

2. **Add `None` guards** for brightness and color attributes before using them in commands — provide sensible defaults (e.g., brightness=255, color_temp=4000K, hs_color=(0,0))

3. **Fix the `masterColor` filter** — change `> 1` to `> -1`

4. **Add standalone ColorPickerV2 discovery** — currently only subcontrols of LightControllerV2 are found

5. **Replace magic number 778** with a named constant and handle edge cases (empty list, None)

6. **Fix logger calls** — use `%s` format strings: `_LOGGER.error("Not handled command -> %s", _color)`

7. **Standardize command casing** — pick `"On"`/`"Off"` or `"on"`/`"off"` consistently
