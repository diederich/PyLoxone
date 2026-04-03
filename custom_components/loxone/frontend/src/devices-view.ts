import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, LoxoneDevice } from "./types";
import { fetchDevices, setEntityEnabled } from "./api";

type SortKey = "name" | "type" | "room" | "entities";
type SortDir = "asc" | "desc";

@customElement("devices-view")
export class DevicesView extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property({ type: Number }) refreshKey = 0;
  @property({ type: String }) miniserverId?: string;
  @state() private _devices: LoxoneDevice[] = [];
  @state() private _filter = "";
  @state() private _loading = true;
  @state() private _error = "";
  @state() private _sortKey: SortKey = "room";
  @state() private _sortDir: SortDir = "asc";

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

  private async _toggleEntity(
    entityId: string,
    currentlyDisabled: boolean,
  ): Promise<void> {
    try {
      await setEntityEnabled(this.hass, entityId, currentlyDisabled);
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
          @input=${(e: Event) => {
            this._filter = (e.target as HTMLInputElement).value;
          }}
        />
        
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
              <tr class=${d.parent && visibleUuids.has(d.parent) ? "sub-control" : ""}>
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
                              class="toggle-btn"
                              title=${ent.disabled_by ? "Enable" : "Disable"}
                              @click=${() =>
                                this._toggleEntity(
                                  ent.entity_id,
                                  !!ent.disabled_by,
                                )}
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
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "devices-view": DevicesView;
  }
}
