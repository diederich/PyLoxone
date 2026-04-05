import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, LoxoneRoom, HaArea } from "./types";
import { showToast } from "./types";
import { fetchAreas, syncAreas, syncDeviceNames } from "./api";

@customElement("areas-view")
export class AreasView extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property({ type: Number }) refreshKey = 0;
  @property({ type: String }) miniserverId?: string;
  @state() private _rooms: LoxoneRoom[] = [];
  @state() private _haAreas: HaArea[] = [];
  @state() private _loading = true;
  @state() private _syncing = false;
  @state() private _error = "";
  @state() private _message = "";

  static styles = css`
    :host {
      display: block;
    }
    .page-intro {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 20px;
      line-height: 1.6;
      max-width: 800px;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
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
    }
    button:hover {
      opacity: 0.85;
    }
    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    button.secondary {
      background: var(--divider-color, #e0e0e0);
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
    }
    td {
      padding: 10px 16px;
      font-size: 14px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    tr:last-child td {
      border-bottom: none;
    }
    .mapped {
      color: var(--success-color, #4caf50);
      font-weight: 500;
    }
    .unmapped {
      color: var(--warning-color, #ff9800);
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
    .summary {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin-bottom: 8px;
    }
    .count {
      font-weight: 500;
      color: var(--primary-color, #03a9f4);
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
      const result = await fetchAreas(this.hass, this.miniserverId);
      this._rooms = result.rooms;
      this._haAreas = result.ha_areas;
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    } finally {
      this._loading = false;
    }
  }

  private async _syncAreas(createAreas: boolean): Promise<void> {
    this._syncing = true;
    this._message = "";
    this._error = "";
    try {
      await syncDeviceNames(this.hass);
      await syncAreas(this.hass, createAreas);
      this._message = createAreas
        ? "Synced areas and created missing ones."
        : "Synced devices to existing areas.";
      showToast(this, this._message);
      await this._load();
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    } finally {
      this._syncing = false;
    }
  }

  protected render() {
    if (this._loading) {
      return html`<p class="status">Loading areas…</p>`;
    }
    if (this._error) {
      return html`<p class="status error">Error: ${this._error}</p>`;
    }

    const mapped = this._rooms.filter((r) => r.ha_area_id).length;
    const total = this._rooms.length;

    return html`
      <p class="page-intro">
        Maps Loxone rooms to Home Assistant areas.
        <em>Sync to existing areas</em> links rooms to HA areas by name;
        <em>Sync and create</em> also creates new HA areas for any unmatched rooms.
        After syncing, assign devices to areas via the HA device registry.
      </p>
      <div class="toolbar">
        <button
          ?disabled=${this._syncing}
          @click=${() => this._syncAreas(false)}
        >
          Sync to existing areas
        </button>
        <button
          class="secondary"
          ?disabled=${this._syncing}
          @click=${() => this._syncAreas(true)}
        >
          Sync + create missing areas
        </button>
      </div>
      ${this._message ? html`<p class="message">${this._message}</p>` : ""}
      <p class="summary">
        <span class="count">${mapped}</span> / ${total} Loxone rooms mapped to
        HA areas
      </p>
      <table>
        <thead>
          <tr>
            <th>Loxone Room</th>
            <th>HA Area</th>
            <th>Devices</th>
          </tr>
        </thead>
        <tbody>
          ${this._rooms.map(
            (room) => html`
              <tr>
                <td>${room.name}</td>
                <td>
                  ${room.ha_area_name
                    ? html`<span class="mapped">${room.ha_area_name}</span>`
                    : html`<span class="unmapped">Not mapped</span>`}
                </td>
                <td>${room.device_count}</td>
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
    "areas-view": AreasView;
  }
}
