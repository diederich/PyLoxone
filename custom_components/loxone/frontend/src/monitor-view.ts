import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, MonitorEvent, MonitorEventMessage } from "./types";

const MAX_EVENTS = 500;

@customElement("monitor-view")
export class MonitorView extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property({ type: String }) miniserverId?: string;
  @state() private _events: MonitorEvent[] = [];
  @state() private _paused = false;
  @state() private _filter = "";
  @state() private _connected = false;
  @state() private _error = "";

  private _unsub?: () => void;
  private _pendingEvents: MonitorEvent[] = [];

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
    .toolbar button {
      padding: 6px 16px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
    }
    .toolbar button.active {
      background: var(--primary-color, #03a9f4);
      color: #fff;
      border-color: var(--primary-color, #03a9f4);
    }
    .toolbar input {
      padding: 6px 12px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      font-size: 13px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      flex: 1;
      min-width: 150px;
      max-width: 300px;
    }
    .count {
      font-size: 12px;
      color: var(--secondary-text-color, #727272);
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
    }
    .status-dot.on {
      background: var(--success-color, #4caf50);
    }
    .status-dot.off {
      background: var(--error-color, #db4437);
    }
    .log-container {
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.1));
      overflow: hidden;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    thead {
      position: sticky;
      top: 0;
      z-index: 1;
    }
    th {
      background: var(--primary-color, #03a9f4);
      padding: 10px 12px;
      text-align: left;
      font-weight: 600;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #fff;
      border-bottom: none;
    }
    td {
      padding: 6px 12px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      color: var(--primary-text-color, #212121);
      font-family: var(--ha-font-family-code, "Roboto Mono", monospace);
      font-size: 12px;
    }
    tr:hover td {
      background: var(--table-row-alternative-background-color, #fafafa);
    }
    .ts {
      white-space: nowrap;
      color: var(--secondary-text-color, #727272);
      width: 90px;
    }
    .name { min-width: 120px; }
    .room {
      color: var(--secondary-text-color, #727272);
      min-width: 80px;
    }
    .uuid {
      color: var(--secondary-text-color, #727272);
      font-size: 11px;
      max-width: 180px;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .value {
      font-weight: 500;
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .scroll-box {
      max-height: 600px;
      overflow-y: auto;
    }
    .empty {
      padding: 24px;
      text-align: center;
      color: var(--secondary-text-color, #727272);
      font-size: 14px;
    }
    .error {
      color: var(--error-color, #db4437);
      font-size: 13px;
    }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    this._subscribe();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this._unsubscribe();
  }

  updated(changed: Map<string, unknown>): void {
    if (changed.has("miniserverId")) {
      this._unsubscribe();
      this._events = [];
      this._subscribe();
    }
  }

  private async _subscribe(): Promise<void> {
    this._error = "";
    try {
      this._unsub = await this.hass.connection.subscribeMessage(
        (msg: unknown) => {
          const data = msg as MonitorEventMessage;
          if (!data.events) return;
          if (this._paused) {
            this._pendingEvents.push(...data.events);
            if (this._pendingEvents.length > MAX_EVENTS) {
              this._pendingEvents = this._pendingEvents.slice(-MAX_EVENTS);
            }
            return;
          }
          this._events = [...data.events, ...this._events].slice(0, MAX_EVENTS);
        },
        {
          type: "loxone/subscribe_events",
          ...(this.miniserverId ? { miniserver: this.miniserverId } : {}),
        },
      );
      this._connected = true;
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
      this._connected = false;
    }
  }

  private _unsubscribe(): void {
    if (this._unsub) {
      this._unsub();
      this._unsub = undefined;
    }
    this._connected = false;
  }

  private _togglePause(): void {
    this._paused = !this._paused;
    if (!this._paused && this._pendingEvents.length > 0) {
      this._events = [...this._pendingEvents, ...this._events].slice(0, MAX_EVENTS);
      this._pendingEvents = [];
    }
  }

  private _clear(): void {
    this._events = [];
    this._pendingEvents = [];
  }

  private _onFilterInput(e: Event): void {
    this._filter = (e.target as HTMLInputElement).value.toLowerCase();
  }

  private _formatTime(iso: string): string {
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString(this.hass.language || "en", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        fractionalSecondDigits: 1,
      });
    } catch {
      return iso;
    }
  }

  private _formatValue(v: unknown): string {
    if (v === null || v === undefined) return "—";
    if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toFixed(2);
    if (typeof v === "object") return JSON.stringify(v);
    return String(v);
  }

  protected render() {
    const filter = this._filter;
    const filtered = filter
      ? this._events.filter(
          (ev) =>
            ev.name.toLowerCase().includes(filter) ||
            ev.room.toLowerCase().includes(filter) ||
            ev.uuid.toLowerCase().includes(filter),
        )
      : this._events;

    return html`
      <div class="toolbar">
        <span class="status-dot ${this._connected ? "on" : "off"}"></span>
        <button
          type="button"
          class="${this._paused ? "active" : ""}"
          aria-pressed=${this._paused ? "true" : "false"}
          aria-label=${this._paused ? "Resume event stream" : "Pause event stream"}
          @click=${this._togglePause}
        >
          ${this._paused ? "▶ Resume" : "⏸ Pause"}
        </button>
        <button type="button" @click=${this._clear}>Clear</button>
        <input
          type="text"
          placeholder="Filter by name, room, UUID…"
          .value=${this._filter}
          @input=${this._onFilterInput}
        />
        <span class="count">${filtered.length} event${filtered.length !== 1 ? "s" : ""}</span>
        ${this._error ? html`<span class="error">${this._error}</span>` : ""}
      </div>
      <div class="log-container">
        ${filtered.length === 0
          ? html`<div class="empty">
              ${this._connected ? "Waiting for events…" : "Not connected"}
            </div>`
          : html`
              <div class="scroll-box">
                <table>
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Name</th>
                      <th>Room</th>
                      <th>Value</th>
                      <th>UUID</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${filtered.map(
                      (ev) => html`
                        <tr>
                          <td class="ts">${this._formatTime(ev.timestamp)}</td>
                          <td class="name">${ev.name || "—"}</td>
                          <td class="room">${ev.room || "—"}</td>
                          <td class="value">${this._formatValue(ev.value)}</td>
                          <td class="uuid" title=${ev.uuid}>${ev.uuid}</td>
                        </tr>
                      `,
                    )}
                  </tbody>
                </table>
              </div>
            `}
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "monitor-view": MonitorView;
  }
}
