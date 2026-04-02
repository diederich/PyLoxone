import type {
  AddBridgeResult,
  GetAreasResult,
  GetBridgesResult,
  GetDevicesResult,
  GetStatusResult,
  HomeAssistant,
  RemoveBridgeResult,
  SetEntityEnabledResult,
} from "./types";

export async function fetchDevices(
  hass: HomeAssistant,
): Promise<GetDevicesResult> {
  return hass.callWS<GetDevicesResult>({ type: "loxone/get_devices" });
}

export async function setEntityEnabled(
  hass: HomeAssistant,
  entityId: string,
  enabled: boolean,
): Promise<SetEntityEnabledResult> {
  return hass.callWS<SetEntityEnabledResult>({
    type: "loxone/set_entity_enabled",
    entity_id: entityId,
    enabled,
  });
}

export async function fetchAreas(
  hass: HomeAssistant,
): Promise<GetAreasResult> {
  return hass.callWS<GetAreasResult>({ type: "loxone/get_areas" });
}

export async function syncAreas(
  hass: HomeAssistant,
  createAreas: boolean,
): Promise<void> {
  await hass.callService("loxone", "sync_areas", {
    create_areas: createAreas,
  });
}

export async function syncDeviceNames(hass: HomeAssistant): Promise<void> {
  await hass.callService("loxone", "sync_device_names");
}

export async function fetchBridges(
  hass: HomeAssistant,
): Promise<GetBridgesResult> {
  return hass.callWS<GetBridgesResult>({ type: "loxone/get_bridges" });
}

export async function addBridge(
  hass: HomeAssistant,
  entityId: string,
  loxoneUuid: string,
): Promise<AddBridgeResult> {
  return hass.callWS<AddBridgeResult>({
    type: "loxone/add_bridge",
    entity_id: entityId,
    loxone_uuid: loxoneUuid,
  });
}

export async function removeBridge(
  hass: HomeAssistant,
  entityId: string,
): Promise<RemoveBridgeResult> {
  return hass.callWS<RemoveBridgeResult>({
    type: "loxone/remove_bridge",
    entity_id: entityId,
  });
}

export async function fetchStatus(
  hass: HomeAssistant,
): Promise<GetStatusResult> {
  return hass.callWS<GetStatusResult>({ type: "loxone/get_status" });
}
