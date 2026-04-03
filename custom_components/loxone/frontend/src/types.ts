/** Minimal typing for the Home Assistant `hass` object passed to panels. */
export interface HomeAssistant {
  callWS<T = unknown>(msg: Record<string, unknown>): Promise<T>;
  callService(
    domain: string,
    service: string,
    data?: Record<string, unknown>,
  ): Promise<void>;
  language: string;
  states: Record<string, HassState>;
}

export interface LoxoneEntry {
  miniserver: string;
  title: string;
  host: string;
  serial: string | null;
  name: string | null;
}

export interface ListEntriesResult {
  entries: LoxoneEntry[];
}

export interface HassState {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
}

export interface LoxoneDevice {
  uuid: string;
  name: string;
  type: string;
  room: string;
  parent?: string;
  ha_entities: HaEntityInfo[];
}

export interface HaEntityInfo {
  entity_id: string;
  disabled_by: string | null;
  area_id: string | null;
}

export interface GetDevicesResult {
  devices: LoxoneDevice[];
}

export interface SetEntityEnabledResult {
  entity_id: string;
  disabled_by: string | null;
}

export interface LoxoneRoom {
  uuid: string;
  name: string;
  ha_area_id: string | null;
  ha_area_name: string | null;
  device_count: number;
}

export interface HaArea {
  id: string;
  name: string;
}

export interface GetAreasResult {
  rooms: LoxoneRoom[];
  ha_areas: HaArea[];
}

export interface BridgeInfo {
  entity_id: string;
  loxone_uuid: string;
  loxone_name: string;
  loxone_type: string;
}

export interface GetBridgesResult {
  bridges: BridgeInfo[];
}

export interface AddBridgeResult {
  entity_id: string;
  loxone_uuid: string;
  loxone_name: string;
  loxone_type: string;
}

export interface RemoveBridgeResult {
  removed: string;
}

export interface GetStatusResult {
  connection_state: string;
  host: string;
  miniserver_name: string;
  project_name: string;
  location: string;
  serial_number: string;
  miniserver_type: string;
  software_version: string;
  controls_count: number;
  rooms_count: number;
  entities_total: number;
  entities_enabled: number;
  entities_disabled: number;
  entities_without_state: string[];
  bridge_count: number;
}
