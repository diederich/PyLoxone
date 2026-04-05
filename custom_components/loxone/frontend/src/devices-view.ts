import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, LoxoneDevice, GetControlDetailResult } from "./types";
import { showToast } from "./types";
import { fetchDevices, setEntityEnabled, fetchControlDetail } from "./api";

type SortKey = "name" | "type" | "room" | "entities";
type SortDir = "asc" | "desc";

@customElement("devices-view")
export class DevicesView extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property({ type: Number }) refreshKey = 0;
  @property({ type: String }) miniserverId?: string;
  @state() private _devices: LoxoneDevice[] = [];
  @state() private _filter = "";
  @state() private _filterDomain = "";
  @state() private _filterRoom = "";
  @state() private _filterStatus = "";
  @state() private _loading = true;
  @state() private _error = "";
  @state() private _sortKey: SortKey = "room";
  @state() private _sortDir: SortDir = "asc";
  @state() private _detail: GetControlDetailResult | null = null;
  @state() private _detailLoading = false;

  static styles = css`
    :host {
      display: block;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }
    input[type="search"] {
      padding: 8px 12px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      font-size: 14px;
      flex: 1;
      min-width: 200px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
    }
    .filter-select {
      padding: 8px 10px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 13px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      cursor: pointer; min-width: 100px;
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
      background: var(--table-header-background-color, var(--card-background-color, #fff));
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }
    th:hover {
      color: var(--primary-text-color, #212121);
    }
    th.active {
      color: var(--primary-color, #03a9f4);
    }
    .sort-arrow {
      font-size: 10px;
      margin-left: 4px;
    }
    td {
      padding: 10px 16px;
      font-size: 14px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      vertical-align: top;
    }
    tr:last-child td {
      border-bottom: none;
    }
    tr.sub-control td:first-child {
      padding-left: 32px;
    }
    .entity-chip {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 12px;
      background: var(--primary-color, #03a9f4);
      color: #fff;
      margin: 2px 2px;
    }
    .entity-chip.disabled {
      background: var(--disabled-text-color, #bdbdbd);
    }
    .toggle-btn {
      border: none;
      background: none;
      cursor: pointer;
      font-size: 16px;
      padding: 2px 4px;
      border-radius: 4px;
      line-height: 1;
    }
    .toggle-btn:hover {
      background: var(--divider-color, #e0e0e0);
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
    .count {
      font-weight: 500;
      color: var(--primary-color, #03a9f4);
    }
    .summary {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin-bottom: 8px;
    }
    .domain-breakdown {
      color: var(--secondary-text-color, #727272);
      font-size: 12px;
    }
    tr.clickable { cursor: pointer; }
    tr.clickable:hover td { background: var(--table-row-alternative-background-color, #fafafa); }
    .drawer-overlay {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.4); z-index: 100;
    }
    .drawer {
      position: fixed; top: 0; right: 0; bottom: 0; width: min(520px, 90vw);
      background: var(--primary-background-color, #fafafa);
      box-shadow: -4px 0 20px rgba(0,0,0,0.15); z-index: 101;
      overflow-y: auto; padding: 24px; box-sizing: border-box;
    }
    .drawer h2 { font-size: 18px; font-weight: 500; margin: 0 0 4px; }
    .drawer .sub-title { font-size: 13px; color: var(--secondary-text-color); margin-bottom: 16px; }
    .drawer .close-btn {
      position: absolute; top: 16px; right: 16px;
      border: none; background: none; font-size: 20px; cursor: pointer;
      color: var(--secondary-text-color);
    }
    .drawer .section-title {
      font-size: 12px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.5px; color: var(--secondary-text-color);
      margin: 16px 0 8px; border-bottom: 1px solid var(--divider-color, #e0e0e0);
      padding-bottom: 4px;
    }
    .drawer .detail-row {
      display: flex; justify-content: space-between; align-items: baseline;
      padding: 4px 0; font-size: 13px;
    }
    .drawer .detail-label { color: var(--secondary-text-color); }
    .drawer .detail-value {
      font-family: var(--ha-font-family-code, monospace); font-size: 12px;
      color: var(--primary-text-color); max-width: 60%; text-align: right; word-break: break-all;
    }
    .drawer .entity-row {
      padding: 6px 0; border-bottom: 1px solid var(--divider-color, #e0e0e0); font-size: 13px;
    }
    .drawer .entity-row:last-child { border-bottom: none; }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    this._loadDevices();
  }

  updated(changed: Map<string, unknown>): void {
    if (changed.has("refreshKey") && changed.get("refreshKey") !== undefined) {
      this._loadDevices();
    }
  }

  async _loadDevices(): Promise<void> {
    this._loading = true;
    this._error = "";
    try {
      const result = await fetchDevices(this.hass, this.miniserverId);
      this._devices = result.devices;
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    } finally {
      this._loading = false;
    }
  }

  private get _allDomains(): string[] {
    const s = new Set<string>();
    for (const d of this._devices) for (const e of d.ha_entities) s.add(e.entity_id.split(".")[0]);
    return [...s].sort();
  }

  private get _allRooms(): string[] {
    const s = new Set<string>();
    for (const d of this._devices) if (d.room) s.add(d.room);
    return [...s].sort();
  }

  private get _filteredDevices(): LoxoneDevice[] {
    let devices = this._devices;
    if (this._filter) {
      const lower = this._filter.toLowerCase();
      devices = devices.filter(
        (d) =>
          d.name.toLowerCase().includes(lower) ||
          d.type.toLowerCase().includes(lower) ||
          d.room.toLowerCase().includes(lower) ||
          d.ha_entities.some((e) => e.entity_id.toLowerCase().includes(lower)),
      );
    }
    if (this._filterDomain) {
      const dom = this._filterDomain;
      devices = devices.filter((d) => d.ha_entities.some((e) => e.entity_id.startsWith(dom + ".")));
    }
    if (this._filterRoom) devices = devices.filter((d) => d.room === this._filterRoom);
    if (this._filterStatus) {
      switch (this._filterStatus) {
        case "enabled": devices = devices.filter((d) => d.ha_entities.length > 0 && d.ha_entities.some((e) => !e.disabled_by)); break;
        case "disabled": devices = devices.filter((d) => d.ha_entities.some((e) => !!e.disabled_by)); break;
        case "no-entity": devices = devices.filter((d) => d.ha_entities.length === 0); break;
      }
    }
    return this._sortDevices(devices);
  }

  private _sortDevices(devices: LoxoneDevice[]): LoxoneDevice[] {
    const dir = this._sortDir === "asc" ? 1 : -1;
    const cmpFn = (a: LoxoneDevice, b: LoxoneDevice): number => {
      let cmp = 0;
      switch (this._sortKey) {
        case "name":
          cmp = a.name.localeCompare(b.name);
          break;
        case "type":
          cmp = a.type.localeCompare(b.type) || a.name.localeCompare(b.name);
          break;
        case "room":
          cmp =
            (a.room || "").localeCompare(b.room || "") ||
            a.name.localeCompare(b.name);
          break;
        case "entities":
          cmp = a.ha_entities.length - b.ha_entities.length;
          break;
      }
      return cmp * dir;
    };

    const parentUuids = new Set(
      devices.filter((d) => !d.parent).map((d) => d.uuid),
    );
    const childrenByParent = new Map<string, LoxoneDevice[]>();
    const topLevel: LoxoneDevice[] = [];

    for (const d of devices) {
      if (d.parent && parentUuids.has(d.parent)) {
        const siblings = childrenByParent.get(d.parent) || [];
        siblings.push(d);
        childrenByParent.set(d.parent, siblings);
      } else {
        topLevel.push(d);
      }
    }

    topLevel.sort(cmpFn);
    for (const children of childrenByParent.values()) {
      children.sort(cmpFn);
    }

    const result: LoxoneDevice[] = [];
    for (const d of topLevel) {
      result.push(d);
      const children = childrenByParent.get(d.uuid);
      if (children) {
        result.push(...children);
      }
    }
    return result;
  }

  private _toggleSort(key: SortKey): void {
    if (this._sortKey === key) {
      this._sortDir = this._sortDir === "asc" ? "desc" : "asc";
    } else {
      this._sortKey = key;
      this._sortDir = "asc";
    }
  }

  private _sortIndicator(key: SortKey): unknown {
    if (this._sortKey !== key) return nothing;
    return html`<span class="sort-arrow"
      >${this._sortDir === "asc" ? "▲" : "▼"}</span
    >`;
  }

  private async _openDetail(uuid: string): Promise<void> {
    this._detailLoading = true;
    this._detail = null;
    try {
      this._detail = await fetchControlDetail(this.hass, uuid, this.miniserverId);
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    } finally {
      this._detailLoading = false;
    }
  }

  private _closeDetail(): void { this._detail = null; }

  private async _toggleEntity(
    entityId: string,
    currentlyDisabled: boolean,
  ): Promise<void> {
    try {
      await setEntityEnabled(this.hass, entityId, currentlyDisabled);
      showToast(this, `${entityId} ${currentlyDisabled ? "enabled" : "disabled"}`);
      await this._loadDevices();
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    }
  }

  protected render() {
    if (this._loading) {
      return html`<p class="status">Loading devices…</p>`;
    }
    if (this._error) {
      return html`<p class="status error">Error: ${this._error}</p>`;
    }

    const devices = this._filteredDevices;
    const visibleUuids = new Set(devices.map((d) => d.uuid));

    const domainCounts = new Map<string, number>();
    for (const d of this._devices) {
      for (const ent of d.ha_entities) {
        const domain = ent.entity_id.split(".")[0];
        domainCounts.set(domain, (domainCounts.get(domain) || 0) + 1);
      }
    }
    const totalEntities = [...domainCounts.values()].reduce(
      (a, b) => a + b,
      0,
    );
    const domainSummary = [...domainCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([domain, count]) => `${count} ${domain}`)
      .join(", ");

    return html`
      <div class="toolbar">
        <input
          type="search"
          placeholder="Filter by name, type, room, or entity…"
          .value=${this._filter}
          @input=${(e: Event) => { this._filter = (e.target as HTMLInputElement).value; }}
        />
        <select class="filter-select" .value=${this._filterDomain}
          @change=${(e: Event) => { this._filterDomain = (e.target as HTMLSelectElement).value; }}>
          <option value="">All domains</option>
          ${this._allDomains.map((d) => html`<option value=${d}>${d}</option>`)}
        </select>
        <select class="filter-select" .value=${this._filterRoom}
          @change=${(e: Event) => { this._filterRoom = (e.target as HTMLSelectElement).value; }}>
          <option value="">All rooms</option>
          ${this._allRooms.map((r) => html`<option value=${r}>${r}</option>`)}
        </select>
        <select class="filter-select" .value=${this._filterStatus}
          @change=${(e: Event) => { this._filterStatus = (e.target as HTMLSelectElement).value; }}>
          <option value="">All statuses</option>
          <option value="enabled">Enabled</option>
          <option value="disabled">Disabled</option>
          <option value="no-entity">No entity</option>
        </select>
      </div>
      <p class="summary">
        <span class="count">${this._devices.length}</span> controls,
        <span class="count">${totalEntities}</span> HA entities
        ${domainSummary
          ? html`<span class="domain-breakdown">(${domainSummary})</span>`
          : ""}
      </p>
      <table>
        <thead>
          <tr>
            <th
              class=${this._sortKey === "name" ? "active" : ""}
              @click=${() => this._toggleSort("name")}
            >
              Name${this._sortIndicator("name")}
            </th>
            <th
              class=${this._sortKey === "type" ? "active" : ""}
              @click=${() => this._toggleSort("type")}
            >
              Type${this._sortIndicator("type")}
            </th>
            <th
              class=${this._sortKey === "room" ? "active" : ""}
              @click=${() => this._toggleSort("room")}
            >
              Room${this._sortIndicator("room")}
            </th>
            <th
              class=${this._sortKey === "entities" ? "active" : ""}
              @click=${() => this._toggleSort("entities")}
            >
              HA Entities${this._sortIndicator("entities")}
            </th>
          </tr>
        </thead>
        <tbody>
          ${devices.map(
            (d) => html`
              <tr class="${d.parent && visibleUuids.has(d.parent) ? "sub-control" : ""} clickable"
                  @click=${() => this._openDetail(d.uuid)}>
                <td>${d.name}</td>
                <td><span class="badge">${d.type}</span></td>
                <td>${d.room || "—"}</td>
                <td>
                  ${d.ha_entities.length === 0
                    ? html`<span style="color: var(--secondary-text-color)"
                        >—</span
                      >`
                    : d.ha_entities.map(
                        (ent) => html`
                          <span
                            class="entity-chip ${ent.disabled_by
                              ? "disabled"
                              : ""}"
                          >
                            ${ent.entity_id}
                            <button
                              type="button"
                              class="toggle-btn"
                              title=${ent.disabled_by ? "Enable" : "Disable"}
                              aria-label=${ent.disabled_by
                                ? `Enable ${ent.entity_id}`
                                : `Disable ${ent.entity_id}`}
                              @click=${(ev: Event) => {
                                ev.stopPropagation();
                                this._toggleEntity(ent.entity_id, !!ent.disabled_by);
                              }}
                            >
                              ${ent.disabled_by ? "⬚" : "✓"}
                            </button>
                          </span>
                        `,
                      )}
                </td>
              </tr>
            `,
          )}
        </tbody>
      </table>
      ${this._detailLoading ? html`<div class="drawer-overlay"><div class="drawer"><p class="status">Loading…</p></div></div>` : ""}
      ${this._detail ? this._renderDrawer(this._detail) : ""}
    `;
  }

  private _renderDrawer(d: GetControlDetailResult) {
    const stateEntries = Object.entries(d.states);
    return html`
      <div class="drawer-overlay" @click=${this._closeDetail}></div>
      <div class="drawer" @click=${(e: Event) => e.stopPropagation()}>
        <button
          type="button"
          class="close-btn"
          aria-label="Close control details"
          @click=${this._closeDetail}
        >
          ✕
        </button>
        <h2>${d.name}</h2>
        <div class="sub-title">
          <span class="badge">${d.type}</span>
          ${d.room ? html` — ${d.room}` : ""}
          ${d.category ? html` — ${d.category}` : ""}
          ${d.is_sub_control && d.parent_name ? html` (sub-control of ${d.parent_name})` : ""}
        </div>
        <div class="detail-row">
          <span class="detail-label">UUID</span>
          <span class="detail-value">${d.uuid}</span>
        </div>
        ${stateEntries.length > 0 ? html`
          <div class="section-title">States (${stateEntries.length})</div>
          ${stateEntries.map(([name, sv]) => html`
            <div class="detail-row">
              <span class="detail-label">${name}</span>
              <span class="detail-value">${sv.value ?? "—"}${sv.last_changed
                ? html` <span style="opacity:0.5;font-size:11px">${new Date(sv.last_changed).toLocaleTimeString()}</span>` : ""}</span>
            </div>
          `)}
        ` : ""}
        ${d.ha_entities.length > 0 ? html`
          <div class="section-title">HA Entities (${d.ha_entities.length})</div>
          ${d.ha_entities.map((ent) => html`
            <div class="entity-row">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span>${ent.entity_id}</span>
                <span class="badge" style="${ent.disabled_by ? "background:var(--disabled-text-color,#bdbdbd)" : "background:var(--success-color,#4caf50);color:#fff"}">${ent.disabled_by ? "disabled" : ent.state ?? "—"}</span>
              </div>
              ${ent.last_changed ? html`<div style="font-size:11px;color:var(--secondary-text-color);margin-top:2px">Last changed: ${new Date(ent.last_changed).toLocaleString()}</div>` : ""}
            </div>
          `)}
        ` : html`<div class="section-title">No HA entities</div>`}
        ${Object.keys(d.details).length > 0 ? html`
          <div class="section-title">Details</div>
          ${Object.entries(d.details).map(([k, v]) => html`
            <div class="detail-row">
              <span class="detail-label">${k}</span>
              <span class="detail-value">${typeof v === "object" ? JSON.stringify(v) : String(v)}</span>
            </div>
          `)}
        ` : ""}
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "devices-view": DevicesView;
  }
}
