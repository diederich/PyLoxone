import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, BridgeInfo, LoxoneDevice } from "./types";
import { showToast } from "./types";
import { fetchBridges, addBridge, removeBridge, fetchDevices } from "./api";

const BRIDGEABLE_DOMAINS = [
  "sensor",
  "binary_sensor",
  "switch",
  "light",
  "number",
  "input_boolean",
  "input_number",
];

interface HaEntityOption {
  entity_id: string;
  friendly_name: string;
  domain: string;
}

interface LoxoneOption {
  uuid: string;
  name: string;
  type: string;
  room: string;
}

@customElement("bridges-view")
export class BridgesView extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property({ type: Number }) refreshKey = 0;
  @property({ type: String }) miniserverId?: string;
  @state() private _bridges: BridgeInfo[] = [];
  @state() private _devices: LoxoneDevice[] = [];
  @state() private _loading = true;
  @state() private _error = "";
  @state() private _message = "";
  @state() private _newEntityId = "";
  @state() private _newLoxoneUuid = "";
  @state() private _entityFilter = "";
  @state() private _loxoneFilter = "";
  @state() private _showEntityDropdown = false;
  @state() private _showLoxoneDropdown = false;
  @state() private _tableFilter = "";
  @state() private _confirmRemove: string | null = null;

  static styles = css`
    :host {
      display: block;
    }
    .add-form {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
      flex-wrap: wrap;
      align-items: flex-end;
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 4px;
      flex: 1;
      min-width: 240px;
    }
    .field label {
      font-size: 11px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
    }
    input {
      padding: 8px 12px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      font-size: 14px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      width: 100%;
      box-sizing: border-box;
    }
    .combo-wrapper {
      position: relative;
    }
    .combo-dropdown {
      position: absolute;
      top: 100%;
      left: 0;
      right: 0;
      max-height: 260px;
      overflow-y: auto;
      background: var(--card-background-color, #fff);
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 0 0 8px 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      z-index: 10;
      margin-top: -1px;
    }
    .combo-group {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
      padding: 8px 12px 4px;
      background: var(--primary-background-color, #fafafa);
    }
    .combo-option {
      padding: 8px 12px;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .combo-option:hover {
      background: var(--primary-color, #03a9f4);
      color: #fff;
    }
    .combo-option .secondary {
      color: var(--secondary-text-color, #727272);
      font-size: 12px;
      margin-left: 8px;
      flex-shrink: 0;
    }
    .combo-option:hover .secondary {
      color: rgba(255, 255, 255, 0.8);
    }
    .combo-empty {
      padding: 12px;
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      text-align: center;
    }
    button {
      padding: 8px 16px;
      border: none;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      background: var(--primary-color, #03a9f4);
      color: #fff;
      transition: opacity 0.2s;
      white-space: nowrap;
    }
    button:hover {
      opacity: 0.85;
    }
    button.danger {
      background: var(--error-color, #db4437);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.1));
    }
    th {
      text-align: left;
      padding: 12px 16px;
      font-size: 12px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    td {
      padding: 10px 16px;
      font-size: 14px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    tr:last-child td {
      border-bottom: none;
    }
    .state-value {
      font-family: var(--ha-font-family-code, monospace);
      font-size: 13px;
      padding: 2px 8px;
      border-radius: 8px;
      background: var(--success-color, #4caf50);
      color: #fff;
    }
    .state-value.state-warn {
      background: var(--warning-color, #ff9800);
    }
    .direction {
      text-align: center;
      font-size: 18px;
      color: var(--secondary-text-color, #727272);
      padding-left: 4px;
      padding-right: 4px;
    }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 500;
      background: var(--divider-color, #e0e0e0);
      color: var(--secondary-text-color, #727272);
    }
    .status {
      color: var(--secondary-text-color, #727272);
      font-size: 14px;
      padding: 16px;
    }
    .error {
      color: var(--error-color, #db4437);
    }
    .message {
      color: var(--success-color, #4caf50);
      font-size: 13px;
      margin-bottom: 8px;
    }
    .empty {
      color: var(--secondary-text-color, #727272);
      font-size: 14px;
      padding: 24px;
      text-align: center;
    }
    .table-toolbar {
      display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap;
    }
    .table-toolbar input {
      padding: 8px 12px; border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 13px; background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121); flex: 1; min-width: 180px; max-width: 350px;
    }
    .summary { font-size: 13px; color: var(--secondary-text-color, #727272); margin-bottom: 12px; }
    .summary .count { font-weight: 500; color: var(--primary-color, #03a9f4); }
    .group-label td {
      padding: 8px 16px; font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.5px; color: var(--secondary-text-color, #727272);
      background: var(--table-header-background-color, var(--primary-background-color, #fafafa));
    }
    .confirm-overlay {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.4); z-index: 100;
      display: flex; align-items: center; justify-content: center;
    }
    .confirm-dialog {
      background: var(--card-background-color, #fff); border-radius: 12px;
      padding: 24px; min-width: 320px; box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    .confirm-dialog h3 { margin: 0 0 12px; font-size: 16px; font-weight: 500; }
    .confirm-dialog p { font-size: 14px; margin: 0 0 20px; color: var(--secondary-text-color); }
    .confirm-dialog .actions { display: flex; gap: 8px; justify-content: flex-end; }
    .confirm-dialog button.secondary {
      background: var(--card-background-color, #fff); color: var(--primary-text-color, #212121);
      border: 1px solid var(--divider-color, #e0e0e0);
    }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    this._load();
  }

  updated(changed: Map<string, unknown>): void {
    if (changed.has("refreshKey") && changed.get("refreshKey") !== undefined) {
      this._load();
    }
  }

  private async _load(): Promise<void> {
    this._loading = true;
    this._error = "";
    try {
      const [bridgeResult, deviceResult] = await Promise.all([
        fetchBridges(this.hass, this.miniserverId),
        fetchDevices(this.hass, this.miniserverId),
      ]);
      this._bridges = bridgeResult.bridges;
      this._devices = deviceResult.devices;
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    } finally {
      this._loading = false;
    }
  }

  // -- HA Entity combo helpers ------------------------------------------------

  private get _availableEntities(): HaEntityOption[] {
    const bridgedIds = new Set(this._bridges.map((b) => b.entity_id));
    const loxoneIds = new Set<string>();
    for (const dev of this._devices) {
      for (const ent of dev.ha_entities) {
        loxoneIds.add(ent.entity_id);
      }
    }

    const result: HaEntityOption[] = [];
    for (const [entityId, st] of Object.entries(this.hass.states)) {
      const domain = entityId.split(".")[0];
      if (!BRIDGEABLE_DOMAINS.includes(domain)) continue;
      if (loxoneIds.has(entityId)) continue;
      if (bridgedIds.has(entityId)) continue;
      result.push({
        entity_id: entityId,
        friendly_name:
          (st.attributes["friendly_name"] as string) || "",
        domain,
      });
    }
    result.sort((a, b) => {
      if (a.domain !== b.domain) return a.domain.localeCompare(b.domain);
      return a.entity_id.localeCompare(b.entity_id);
    });
    return result;
  }

  private get _filteredEntities(): HaEntityOption[] {
    if (!this._entityFilter) return this._availableEntities;
    const lower = this._entityFilter.toLowerCase();
    return this._availableEntities.filter(
      (e) =>
        e.entity_id.toLowerCase().includes(lower) ||
        e.friendly_name.toLowerCase().includes(lower),
    );
  }

  private _groupByKey<T>(
    items: T[],
    keyFn: (item: T) => string,
  ): Map<string, T[]> {
    const groups = new Map<string, T[]>();
    for (const item of items) {
      const key = keyFn(item);
      const list = groups.get(key) || [];
      list.push(item);
      groups.set(key, list);
    }
    return groups;
  }

  // -- Loxone control combo helpers -------------------------------------------

  private get _availableLoxoneControls(): LoxoneOption[] {
    const bridgedUuids = new Set(this._bridges.map((b) => b.loxone_uuid));
    const result: LoxoneOption[] = [];
    for (const dev of this._devices) {
      if (bridgedUuids.has(dev.uuid)) continue;
      result.push({
        uuid: dev.uuid,
        name: dev.name,
        type: dev.type,
        room: dev.room || "—",
      });
    }
    result.sort((a, b) => {
      if (a.room !== b.room) return a.room.localeCompare(b.room);
      return a.name.localeCompare(b.name);
    });
    return result;
  }

  private get _filteredLoxoneControls(): LoxoneOption[] {
    if (!this._loxoneFilter) return this._availableLoxoneControls;
    const lower = this._loxoneFilter.toLowerCase();
    return this._availableLoxoneControls.filter(
      (c) =>
        c.name.toLowerCase().includes(lower) ||
        c.type.toLowerCase().includes(lower) ||
        c.room.toLowerCase().includes(lower),
    );
  }

  // -- Dropdown event handlers ------------------------------------------------

  private _onEntityFocus(): void {
    this._showEntityDropdown = true;
  }

  private _onEntityBlur(): void {
    setTimeout(() => {
      this._showEntityDropdown = false;
    }, 200);
  }

  private _selectEntity(entityId: string): void {
    this._newEntityId = entityId;
    this._entityFilter = entityId;
    this._showEntityDropdown = false;
  }

  private _onLoxoneFocus(): void {
    this._showLoxoneDropdown = true;
  }

  private _onLoxoneBlur(): void {
    setTimeout(() => {
      this._showLoxoneDropdown = false;
    }, 200);
  }

  private _selectLoxone(uuid: string, name: string): void {
    this._newLoxoneUuid = uuid;
    this._loxoneFilter = name;
    this._showLoxoneDropdown = false;
  }

  // -- Actions ----------------------------------------------------------------

  private get _filteredBridges(): BridgeInfo[] {
    if (!this._tableFilter) return this._bridges;
    const lower = this._tableFilter.toLowerCase();
    return this._bridges.filter(
      (b) => b.entity_id.toLowerCase().includes(lower) ||
             (b.loxone_name || "").toLowerCase().includes(lower) ||
             b.loxone_type.toLowerCase().includes(lower),
    );
  }

  private async _addBridge(): Promise<void> {
    if (!this._newEntityId || !this._newLoxoneUuid) return;
    this._error = "";
    this._message = "";
    try {
      await addBridge(this.hass, this._newEntityId, this._newLoxoneUuid, this.miniserverId);
      showToast(this, `Bridge added: ${this._newEntityId}`);
      this._message = `Bridge added: ${this._newEntityId}`;
      this._newEntityId = "";
      this._newLoxoneUuid = "";
      this._entityFilter = "";
      this._loxoneFilter = "";
      await this._load();
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    }
  }

  private _requestRemove(entityId: string): void {
    this._confirmRemove = entityId;
  }

  private async _confirmAndRemove(): Promise<void> {
    const entityId = this._confirmRemove;
    if (!entityId) return;
    this._confirmRemove = null;
    this._error = "";
    this._message = "";
    try {
      await removeBridge(this.hass, entityId, this.miniserverId);
      showToast(this, `Bridge removed: ${entityId}`);
      this._message = `Bridge removed: ${entityId}`;
      await this._load();
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    }
  }

  // -- Render -----------------------------------------------------------------

  protected render() {
    if (this._loading) {
      return html`<p class="status">Loading bridges…</p>`;
    }
    if (this._error) {
      return html`<p class="status error">Error: ${this._error}</p>`;
    }

    const filteredEntities = this._filteredEntities;
    const groupedEntities = this._groupByKey(filteredEntities, (e) => e.domain);

    const filteredLoxone = this._filteredLoxoneControls;
    const groupedLoxone = this._groupByKey(filteredLoxone, (c) => c.room);

    return html`
      <div class="add-form">
        <div class="field">
          <label>HA Entity</label>
          <div class="combo-wrapper">
            <input
              type="text"
              placeholder="Search entities…"
              .value=${this._entityFilter}
              @input=${(e: Event) => {
                this._entityFilter = (e.target as HTMLInputElement).value;
                this._newEntityId = this._entityFilter;
                this._showEntityDropdown = true;
              }}
              @focus=${this._onEntityFocus}
              @blur=${this._onEntityBlur}
              autocomplete="off"
            />
            ${this._showEntityDropdown
              ? html`
                  <div class="combo-dropdown">
                    ${filteredEntities.length === 0
                      ? html`<div class="combo-empty">No matching entities</div>`
                      : Array.from(groupedEntities.entries()).map(
                          ([domain, entities]) => html`
                            <div class="combo-group">${domain}</div>
                            ${entities.map(
                              (ent) => html`
                                <div
                                  class="combo-option"
                                  @mousedown=${(ev: Event) => {
                                    ev.preventDefault();
                                    this._selectEntity(ent.entity_id);
                                  }}
                                >
                                  <span>${ent.entity_id}</span>
                                  ${ent.friendly_name
                                    ? html`<span class="secondary"
                                        >${ent.friendly_name}</span
                                      >`
                                    : ""}
                                </div>
                              `,
                            )}
                          `,
                        )}
                  </div>
                `
              : ""}
          </div>
        </div>
        <div class="field">
          <label>Loxone Control</label>
          <div class="combo-wrapper">
            <input
              type="text"
              placeholder="Search controls…"
              .value=${this._loxoneFilter}
              @input=${(e: Event) => {
                this._loxoneFilter = (e.target as HTMLInputElement).value;
                this._newLoxoneUuid = "";
                this._showLoxoneDropdown = true;
              }}
              @focus=${this._onLoxoneFocus}
              @blur=${this._onLoxoneBlur}
              autocomplete="off"
            />
            ${this._showLoxoneDropdown
              ? html`
                  <div class="combo-dropdown">
                    ${filteredLoxone.length === 0
                      ? html`<div class="combo-empty">No matching controls</div>`
                      : Array.from(groupedLoxone.entries()).map(
                          ([room, controls]) => html`
                            <div class="combo-group">${room}</div>
                            ${controls.map(
                              (ctrl) => html`
                                <div
                                  class="combo-option"
                                  @mousedown=${(ev: Event) => {
                                    ev.preventDefault();
                                    this._selectLoxone(ctrl.uuid, ctrl.name);
                                  }}
                                >
                                  <span>${ctrl.name}</span>
                                  <span class="secondary">${ctrl.type}</span>
                                </div>
                              `,
                            )}
                          `,
                        )}
                  </div>
                `
              : ""}
          </div>
        </div>
        <button @click=${this._addBridge}>Add Bridge</button>
      </div>
      ${this._message ? html`<p class="message">${this._message}</p>` : ""}
      ${this._bridges.length > 0 ? html`
        <p class="summary"><span class="count">${this._bridges.length}</span> bridge${this._bridges.length !== 1 ? "s" : ""} configured</p>
        <div class="table-toolbar">
          <input type="text" placeholder="Search bridges…"
            .value=${this._tableFilter}
            @input=${(e: Event) => { this._tableFilter = (e.target as HTMLInputElement).value; }} />
        </div>
      ` : ""}
      ${this._bridges.length === 0
        ? html`<p class="empty">No device bridges configured.</p>`
        : (() => {
            const filtered = this._filteredBridges;
            const grouped = this._groupByKey(filtered, (b) => b.entity_id.split(".")[0]);
            return html`
              <table>
                <thead>
                  <tr>
                    <th>HA Entity</th>
                    <th>State</th>
                    <th></th>
                    <th>Loxone Control</th>
                    <th>Type</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  ${Array.from(grouped.entries()).map(([domain, bridges]) => html`
                    <tr class="group-label"><td colspan="6">${domain} (${bridges.length})</td></tr>
                    ${bridges.map((b) => {
                      const st = this.hass.states[b.entity_id];
                      const stateStr = st ? st.state : "unavailable";
                      const stateClass =
                        !st || stateStr === "unavailable" || stateStr === "unknown"
                          ? "state-warn" : "";
                      return html`
                        <tr>
                          <td>${b.entity_id}</td>
                          <td><span class="state-value ${stateClass}">${stateStr}</span></td>
                          <td class="direction">→</td>
                          <td>${b.loxone_name || b.loxone_uuid}</td>
                          <td><span class="badge">${b.loxone_type}</span></td>
                          <td><button class="danger" @click=${() => this._requestRemove(b.entity_id)}>Remove</button></td>
                        </tr>
                      `;
                    })}
                  `)}
                </tbody>
              </table>
            `;
          })()}
      ${this._confirmRemove ? html`
        <div class="confirm-overlay" @click=${() => { this._confirmRemove = null; }}>
          <div class="confirm-dialog" @click=${(e: Event) => e.stopPropagation()}>
            <h3>Remove bridge?</h3>
            <p>This will remove the bridge for <strong>${this._confirmRemove}</strong>. The entity will no longer be bridged to its Loxone control.</p>
            <div class="actions">
              <button class="secondary" @click=${() => { this._confirmRemove = null; }}>Cancel</button>
              <button class="danger" @click=${this._confirmAndRemove}>Remove</button>
            </div>
          </div>
        </div>
      ` : ""}
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "bridges-view": BridgesView;
  }
}
