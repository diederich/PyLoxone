/** Minimal typing for the Home Assistant `hass` object passed to panels. */
export interface HomeAssistant {
  callWS<T = unknown>(msg: Record<string, unknown>): Promise<T>;
  callService(
    domain: string,
    service: string,
    data?: Record<string, unknown>,
  ): Promise<void>;
  connection: {
    subscribeMessage(
      callback: (msg: unknown) => void,
      msg: Record<string, unknown>,
    ): Promise<() => void>;
  };
  language: string;
  states: Record<string, HassState>;
}

export function showToast(el: HTMLElement, message: string): void {
  el.dispatchEvent(
    new CustomEvent("hass-notification", {
      bubbles: true, composed: true,
      detail: { message, duration: 4000 },
    }),
  );
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

export interface MonitorEvent {
  uuid: string;
  name: string;
  room: string;
  value: unknown;
  timestamp: string;
}

export interface MonitorEventMessage {
  events: MonitorEvent[];
}

export interface SendCommandResult {
  sent: boolean;
  uuid: string;
  command: string;
}

export interface StructureDiffEntry {
  uuid: string;
  name: string;
  type: string;
  room: string;
}

export interface StructureChangedEntry {
  uuid: string;
  old: { name: string; type: string; room: string };
  new: { name: string; type: string; room: string };
}

export interface GetStructureDiffResult {
  has_diff: boolean;
  timestamp: string | null;
  added: StructureDiffEntry[];
  removed: StructureDiffEntry[];
  changed: StructureChangedEntry[];
}

export interface ControlStateValue {
  uuid: string;
  value: string | null;
  last_changed: string | null;
}

export interface ControlEntityInfo {
  entity_id: string;
  domain: string;
  disabled_by: string | null;
  state: string | null;
  last_changed: string | null;
}

export interface GetControlDetailResult {
  uuid: string;
  name: string;
  type: string;
  room: string;
  category: string;
  is_sub_control: boolean;
  parent_name: string | null;
  states: Record<string, ControlStateValue>;
  ha_entities: ControlEntityInfo[];
  details: Record<string, unknown>;
}

export interface StructureControl {
  uuid: string;
  name: string;
  type: string;
  room: string;
  category: string;
  states: string[];
  sub_controls: { uuid: string; name: string; type: string; states: string[] }[];
}

export interface GetStructureResult {
  rooms: { uuid: string; name: string }[];
  categories: { uuid: string; name: string }[];
  controls: StructureControl[];
}

export interface LogEntry {
  name: string;
  level: string;
  message: string;
  timestamp: number;
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
