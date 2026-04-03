import type {
  AddBridgeResult,
  GetAreasResult,
  GetBridgesResult,
  GetDevicesResult,
  GetStatusResult,
  HomeAssistant,
  ListEntriesResult,
  RemoveBridgeResult,
  SetEntityEnabledResult,
} from "./types";

export async function fetchEntries(
  hass: HomeAssistant,
): Promise<ListEntriesResult> {
  return hass.callWS<ListEntriesResult>({ type: "loxone/list_entries" });
}

export async function fetchDevices(
  hass: HomeAssistant,
  miniserverId?: string,
): Promise<GetDevicesResult> {
  return hass.callWS<GetDevicesResult>({
    type: "loxone/get_devices",
    ...(miniserverId ? { miniserver: miniserverId } : {}),
  });
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
  miniserverId?: string,
): Promise<GetAreasResult> {
  return hass.callWS<GetAreasResult>({
    type: "loxone/get_areas",
    ...(miniserverId ? { miniserver: miniserverId } : {}),
  });
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
  miniserverId?: string,
): Promise<GetBridgesResult> {
  return hass.callWS<GetBridgesResult>({
    type: "loxone/get_bridges",
    ...(miniserverId ? { miniserver: miniserverId } : {}),
  });
}

export async function addBridge(
  hass: HomeAssistant,
  entityId: string,
  loxoneUuid: string,
  miniserverId?: string,
): Promise<AddBridgeResult> {
  return hass.callWS<AddBridgeResult>({
    type: "loxone/add_bridge",
    entity_id: entityId,
    loxone_uuid: loxoneUuid,
    ...(miniserverId ? { miniserver: miniserverId } : {}),
  });
}

export async function removeBridge(
  hass: HomeAssistant,
  entityId: string,
  miniserverId?: string,
): Promise<RemoveBridgeResult> {
  return hass.callWS<RemoveBridgeResult>({
    type: "loxone/remove_bridge",
    entity_id: entityId,
    ...(miniserverId ? { miniserver: miniserverId } : {}),
  });
}

export async function fetchStatus(
  hass: HomeAssistant,
  miniserverId?: string,
): Promise<GetStatusResult> {
  return hass.callWS<GetStatusResult>({
    type: "loxone/get_status",
    ...(miniserverId ? { miniserver: miniserverId } : {}),
  });
}
