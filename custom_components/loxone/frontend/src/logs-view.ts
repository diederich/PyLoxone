import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, LogEntry } from "./types";

const MAX_LOGS = 500;

const LEVEL_COLORS: Record<string, string> = {
  DEBUG: "var(--secondary-text-color, #727272)",
  INFO: "var(--primary-color, #03a9f4)",
  WARNING: "var(--warning-color, #ff9800)",
  ERROR: "var(--error-color, #db4437)",
  CRITICAL: "var(--error-color, #db4437)",
};

const LEVEL_ORDER: Record<string, number> = {
  DEBUG: 10, INFO: 20, WARNING: 30, ERROR: 40, CRITICAL: 50,
};

@customElement("logs-view")
export class LogsView extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @state() private _logs: LogEntry[] = [];
  @state() private _paused = false;
  @state() private _filter = "";
  @state() private _levelFilter = "";
  @state() private _connected = false;
  @state() private _error = "";

  private _unsub?: () => void;
  private _pending: LogEntry[] = [];

  static styles = css`
    :host { display: block; }
    .toolbar {
      display: flex; align-items: center; gap: 12px;
      margin-bottom: 16px; flex-wrap: wrap;
    }
    .toolbar button {
      padding: 6px 16px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      cursor: pointer; font-size: 13px; font-weight: 500;
    }
    .toolbar button.active {
      background: var(--primary-color, #03a9f4);
      color: #fff; border-color: var(--primary-color, #03a9f4);
    }
    .toolbar input {
      padding: 6px 12px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 13px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      flex: 1; min-width: 120px; max-width: 300px;
    }
    .toolbar select {
      padding: 6px 10px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 13px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      cursor: pointer;
    }
    .count { font-size: 12px; color: var(--secondary-text-color, #727272); }
    .status-dot {
      width: 8px; height: 8px; border-radius: 50%; display: inline-block;
    }
    .status-dot.on { background: var(--success-color, #4caf50); }
    .status-dot.off { background: var(--error-color, #db4437); }
    .log-container {
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,0.1));
      overflow: hidden;
    }
    .scroll-box { max-height: 600px; overflow-y: auto; }
    .log-line {
      padding: 4px 12px; font-size: 12px;
      font-family: var(--ha-font-family-code, "Roboto Mono", monospace);
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      display: flex; gap: 8px; align-items: baseline;
    }
    .log-line:hover { background: var(--table-row-alternative-background-color, #fafafa); }
    .log-ts { color: var(--secondary-text-color); white-space: nowrap; min-width: 80px; }
    .log-level {
      font-weight: 600; font-size: 11px; min-width: 55px;
      text-transform: uppercase;
    }
    .log-name { color: var(--secondary-text-color); min-width: 100px; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .log-msg { flex: 1; word-break: break-word; }
    .empty {
      padding: 24px; text-align: center;
      color: var(--secondary-text-color); font-size: 14px;
      line-height: 1.6;
    }
    .hint {
      font-size: 12px; color: var(--secondary-text-color);
      margin-bottom: 12px;
    }
    .hint code {
      background: var(--secondary-background-color, #e8e8e8);
      padding: 1px 5px; border-radius: 4px;
      font-family: var(--ha-font-family-code, monospace);
      font-size: 11px;
    }
    .error { color: var(--error-color, #db4437); font-size: 13px; }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    this._subscribe();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this._unsubscribe();
  }

  private async _subscribe(): Promise<void> {
    this._error = "";
    try {
      this._unsub = await this.hass.connection.subscribeMessage(
        (msg: unknown) => {
          const data = msg as LogEntry;
          if (!data.message) return;
          const entry: LogEntry = {
            name: data.name,
            level: data.level,
            message: data.message,
            timestamp: data.timestamp,
          };
          if (this._paused) {
            this._pending.push(entry);
            if (this._pending.length > MAX_LOGS)
              this._pending = this._pending.slice(-MAX_LOGS);
            return;
          }
          this._logs = [entry, ...this._logs].slice(0, MAX_LOGS);
        },
        { type: "loxone/subscribe_logs" },
      );
      this._connected = true;
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
      this._connected = false;
    }
  }

  private _unsubscribe(): void {
    if (this._unsub) { this._unsub(); this._unsub = undefined; }
    this._connected = false;
  }

  private _togglePause(): void {
    this._paused = !this._paused;
    if (!this._paused && this._pending.length > 0) {
      this._logs = [...this._pending.reverse(), ...this._logs].slice(0, MAX_LOGS);
      this._pending = [];
    }
  }

  private _clear(): void {
    this._logs = [];
    this._pending = [];
  }

  private _formatTime(ts: number): string {
    try {
      return new Date(ts * 1000).toLocaleTimeString(this.hass.language || "en", {
        hour: "2-digit", minute: "2-digit", second: "2-digit",
      });
    } catch { return String(ts); }
  }

  private _shortName(name: string): string {
    return name.replace(/^custom_components\.loxone\.?/, "");
  }

  protected render() {
    const filter = this._filter.toLowerCase();
    const levelFilter = this._levelFilter;
    let logs = this._logs;
    if (filter) {
      logs = logs.filter(
        (l) => l.message.toLowerCase().includes(filter) ||
               l.name.toLowerCase().includes(filter),
      );
    }
    if (levelFilter) {
      const minLevel = LEVEL_ORDER[levelFilter] ?? 0;
      logs = logs.filter((l) => (LEVEL_ORDER[l.level] ?? 0) >= minLevel);
    }

    return html`
      <div class="toolbar">
        <span class="status-dot ${this._connected ? "on" : "off"}"></span>
        <button class="${this._paused ? "active" : ""}" @click=${this._togglePause}>
          ${this._paused ? "▶ Resume" : "⏸ Pause"}
        </button>
        <button @click=${this._clear}>Clear</button>
        <input type="text" placeholder="Filter…" .value=${this._filter}
          @input=${(e: Event) => { this._filter = (e.target as HTMLInputElement).value; }} />
        <select .value=${this._levelFilter}
          @change=${(e: Event) => { this._levelFilter = (e.target as HTMLSelectElement).value; }}>
          <option value="">All levels</option>
          <option value="DEBUG">DEBUG+</option>
          <option value="INFO">INFO+</option>
          <option value="WARNING">WARNING+</option>
          <option value="ERROR">ERROR+</option>
        </select>
        <span class="count">${logs.length} log${logs.length !== 1 ? "s" : ""}</span>
        ${this._error ? html`<span class="error">${this._error}</span>` : ""}
      </div>
      <p class="hint">Showing warnings and errors by default. For debug/info logs, add <code>custom_components.loxone: debug</code> to your <code>logger:</code> in <code>configuration.yaml</code>.</p>
      <div class="log-container">
        ${logs.length === 0
          ? html`<div class="empty">${this._connected ? "Waiting for log messages…<br>Warnings and errors will appear here." : "Not connected"}</div>`
          : html`
            <div class="scroll-box">
              ${logs.map((l) => html`
                <div class="log-line">
                  <span class="log-ts">${this._formatTime(l.timestamp)}</span>
                  <span class="log-level" style="color:${LEVEL_COLORS[l.level] || "inherit"}">${l.level}</span>
                  <span class="log-name" title=${l.name}>${this._shortName(l.name)}</span>
                  <span class="log-msg">${l.message}</span>
                </div>
              `)}
            </div>
          `}
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "logs-view": LogsView;
  }
}
