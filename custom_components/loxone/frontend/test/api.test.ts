import { describe, it, expect, vi } from "vitest";
import {
  fetchDevices, setEntityEnabled, fetchAreas, syncAreas, syncDeviceNames,
  fetchBridges, addBridge, removeBridge,
} from "../src/api";
import type { HomeAssistant } from "../src/types";

function mockHass(
  wsResponse: unknown = { devices: [] },
): HomeAssistant {
  return {
    callWS: vi.fn().mockResolvedValue(wsResponse),
    callService: vi.fn().mockResolvedValue(undefined),
    connection: {
      subscribeMessage: vi.fn().mockResolvedValue(() => {}),
    },
    language: "en",
    states: {},
  };
}

describe("fetchDevices", () => {
  it("calls loxone/get_devices and returns devices", async () => {
    const devices = [
      { uuid: "aaa", name: "Switch", type: "Switch", room: "Living Room", ha_entities: [] },
    ];
    const hass = mockHass({ devices });
    const result = await fetchDevices(hass);

    expect(hass.callWS).toHaveBeenCalledWith({ type: "loxone/get_devices" });
    expect(result.devices).toHaveLength(1);
    expect(result.devices[0].name).toBe("Switch");
  });

  it("propagates errors from callWS", async () => {
    const hass = mockHass();
    (hass.callWS as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("not_connected"),
    );

    await expect(fetchDevices(hass)).rejects.toThrow("not_connected");
  });
});

describe("setEntityEnabled", () => {
  it("sends loxone/set_entity_enabled with correct params", async () => {
    const hass = mockHass({ entity_id: "switch.wall_switch", disabled_by: null });
    const result = await setEntityEnabled(hass, "switch.wall_switch", true);

    expect(hass.callWS).toHaveBeenCalledWith({
      type: "loxone/set_entity_enabled",
      entity_id: "switch.wall_switch",
      enabled: true,
    });
    expect(result.entity_id).toBe("switch.wall_switch");
    expect(result.disabled_by).toBeNull();
  });

  it("disables entity and returns disabled_by", async () => {
    const hass = mockHass({
      entity_id: "switch.wall_switch",
      disabled_by: "integration",
    });
    const result = await setEntityEnabled(hass, "switch.wall_switch", false);

    expect(hass.callWS).toHaveBeenCalledWith({
      type: "loxone/set_entity_enabled",
      entity_id: "switch.wall_switch",
      enabled: false,
    });
    expect(result.disabled_by).toBe("integration");
  });
});

describe("fetchAreas", () => {
  it("calls loxone/get_areas and returns rooms and ha_areas", async () => {
    const response = {
      rooms: [{ uuid: "r1", name: "Living", ha_area_id: "a1", ha_area_name: "Living", device_count: 2 }],
      ha_areas: [{ id: "a1", name: "Living" }],
    };
    const hass = mockHass(response);
    const result = await fetchAreas(hass);

    expect(hass.callWS).toHaveBeenCalledWith({ type: "loxone/get_areas" });
    expect(result.rooms).toHaveLength(1);
    expect(result.ha_areas).toHaveLength(1);
  });
});

describe("syncAreas", () => {
  it("calls loxone.sync_areas service with create_areas", async () => {
    const hass = mockHass();
    await syncAreas(hass, true);

    expect(hass.callService).toHaveBeenCalledWith("loxone", "sync_areas", {
      create_areas: true,
    });
  });
});

describe("syncDeviceNames", () => {
  it("calls loxone.sync_device_names service", async () => {
    const hass = mockHass();
    await syncDeviceNames(hass);

    expect(hass.callService).toHaveBeenCalledWith("loxone", "sync_device_names");
  });
});

describe("fetchBridges", () => {
  it("calls loxone/get_bridges", async () => {
    const hass = mockHass({ bridges: [] });
    const result = await fetchBridges(hass);

    expect(hass.callWS).toHaveBeenCalledWith({ type: "loxone/get_bridges" });
    expect(result.bridges).toEqual([]);
  });
});

describe("addBridge", () => {
  it("calls loxone/add_bridge with correct params", async () => {
    const hass = mockHass({
      entity_id: "sensor.temp",
      loxone_uuid: "aaa",
      loxone_name: "Switch",
      loxone_type: "Switch",
    });
    await addBridge(hass, "sensor.temp", "aaa");

    expect(hass.callWS).toHaveBeenCalledWith({
      type: "loxone/add_bridge",
      entity_id: "sensor.temp",
      loxone_uuid: "aaa",
    });
  });
});

describe("removeBridge", () => {
  it("calls loxone/remove_bridge with entity_id", async () => {
    const hass = mockHass({ removed: "sensor.temp" });
    await removeBridge(hass, "sensor.temp");

    expect(hass.callWS).toHaveBeenCalledWith({
      type: "loxone/remove_bridge",
      entity_id: "sensor.temp",
    });
  });
});
