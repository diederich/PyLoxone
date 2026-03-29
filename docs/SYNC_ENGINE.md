# Sync Engine

> How PyLoxone synchronizes Loxone Miniserver data with Home Assistant.
>
> For connection internals, see [API_LAYER.md](API_LAYER.md).
> For entity platforms, see [HA_INTEGRATION.md](HA_INTEGRATION.md).

## Overview

"Sync" in PyLoxone operates at three distinct layers:

| Layer | What it does | When it runs |
| --- | --- | --- |
| **Structure sync** | Fetches `LoxAPP3.json`, creates/removes HA entities | Integration setup and reload |
| **Registry sync** | Aligns HA device names and areas with Loxone rooms | Automatically on setup/reload; also callable as services |
| **Device bridges** | Maps non-Loxone HA entities to Loxone controls | Continuously while integration is running |

```
┌──────────────────────────────────────────────────────────────────┐
│                    Sync Lifecycle                                 │
│                                                                  │
│  1. async_setup_entry()                                          │
│     ├── coordinator.async_config_entry_first_refresh()           │
│     │   └── api.open() → HTTP GET /data/LoxAPP3.json            │
│     │       → self.structure_file = parsed JSON    [STRUCTURE]   │
│     │                                                            │
│     ├── MiniServer(structure_file)                               │
│     │   → device registry: gateway device                       │
│     │                                                            │
│     ├── async_forward_entry_setups(platforms)                    │
│     │   → each platform reads structure_file.controls            │
│     │   → async_add_entities(...)                  [STRUCTURE]   │
│     │                                                            │
│     ├── sync_device_names()                        [REGISTRY]    │
│     ├── sync_areas(create_areas=True)              [REGISTRY]    │
│     │                                                            │
│     ├── BridgeRuntime.async_setup()                [BRIDGES]     │
│     │                                                            │
│     └── api.start_listening(callback)                            │
│         → WebSocket events → entity state updates               │
└──────────────────────────────────────────────────────────────────┘
```

## Layer 1: Structure Sync

The Miniserver's entire configuration lives in `LoxAPP3.json` (the "structure file"). The integration fetches it once during `api.open()` and uses it to create HA entities.

### What happens

1. `LoxoneConnection.open()` makes an HTTP GET to `/data/LoxAPP3.json`
2. The JSON is parsed into `connection.structure_file`
3. `MiniServer` wraps the structure file for attribute-style access
4. Each platform's `async_setup_entry` iterates `controls` by type and calls `async_add_entities`

### Key data from the structure file

- **`controls`** — UUID-keyed dict of all Loxone controls (switches, dimmers, covers, etc.)
- **`rooms`** — UUID-keyed dict of rooms, referenced by controls via `room` key
- **`cats`** — UUID-keyed dict of categories, referenced by controls via `cat` key
- **`msInfo`** — Miniserver metadata (serial, name, type, software version)

### When structure changes

If you add/remove/rename controls in Loxone Config, the structure file changes. To pick up those changes:

1. Call the `loxone.reload` service (or restart HA)
2. The integration unloads, reconnects, re-fetches `LoxAPP3.json`, and recreates entities
3. Registry sync runs automatically after reload

## Layer 2: Registry Sync

Registry sync aligns HA's device and area registries with the Loxone structure. It runs automatically during setup and reload, and is also available as manual services.

### `sync_device_names`

Updates HA device display names to match control names in the structure file.

- Iterates all HA devices with `(DOMAIN, uuid)` identifiers
- Looks up the `name` field from the matching control in `controls`
- Updates the device name if it differs

**Service:** `loxone.sync_device_names` (no parameters)

### `sync_areas`

Maps Loxone rooms to HA areas on devices.

- Reads the `room` attribute from each Loxone entity's state
- Groups entities by their parent device
- For each device, finds or creates the HA area matching the Loxone room name
- Assigns the area to the **device** (not individual entities)
- Clears any stale entity-level area overrides so entities inherit from their device

**Service:** `loxone.sync_areas`

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `create_areas` | boolean | `false` | Create HA areas that don't exist yet |

### Auto-sync behavior

Registry sync runs automatically at the end of `async_setup_entry`:

1. `sync_device_names()` — ensures device names match the structure file
2. `sync_areas(create_areas=...)` — assigns devices to HA areas

The `create_areas` behavior depends on whether this is the first setup or a restart:

- **First setup:** Uses the user's preference from the config flow checkbox "Create HA areas from Loxone rooms" (defaults to `true`). After the initial sync, a `initial_sync_done` flag is stored in `config_entry.data`.
- **Subsequent restarts/reloads:** Always uses `create_areas=false` — devices are assigned to existing HA areas, but no new areas are created. This avoids re-creating areas the user intentionally deleted.

Users can always run `loxone.sync_areas` manually with `create_areas: true` to re-create the full area structure from Loxone rooms.

## Layer 3: Device Bridges

Device bridges map a non-Loxone HA entity (e.g. a Hue light, Zigbee sensor) to a Loxone control or sub-control. This enables bidirectional state synchronization between HA devices and the Miniserver.

For full details on bridge architecture, supported mappings, and configuration, see the [Device Bridge section in HA_INTEGRATION.md](HA_INTEGRATION.md#device-bridge-bridgepy--bridge_mapperspy).

### Summary

- Configured via the options flow UI (Settings → Devices & services → PyLoxone → Configure → Device Bridges)
- Persisted in `config_entry.options["bridges"]`
- `BridgeRuntime` manages listeners, cooldown, and echo protection
- When a Loxone control is bridged, its native HA entity is disabled (marked `disabled_by: integration`) rather than deleted. The entity remains visible in the entity registry and is automatically re-enabled if the bridge is removed.

## Connection Validation

The config flow validates the Miniserver connection during initial setup. After the user enters host, port, username, and password, the integration makes a test HTTP request to `/jdev/cfg/apiKey` to verify:

- The Miniserver is reachable at the given host and port
- The credentials are accepted (HTTP Basic Auth)

If the connection fails, the user sees an error in the config flow UI before the entry is created.

## Known Limitations

- **Structure is a snapshot.** The integration does not poll for structure changes. If you modify controls in Loxone Config, you must reload the integration to pick up changes.
- **No selective entity management.** All controls from the structure file are created as entities. There is no UI to include/exclude specific controls.
- **No side-by-side view.** There is no panel showing Loxone controls alongside their HA counterparts. A custom panel (similar to KNX/Insteon) is planned for the future.
- **Bridge management is one-at-a-time.** The options flow adds/removes bridges individually. Bulk bridge management is a future improvement.
