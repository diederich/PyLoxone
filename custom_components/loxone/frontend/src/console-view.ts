import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, LoxoneDevice } from "./types";
import { fetchDevices, sendCommand } from "./api";

interface HistoryEntry {
  uuid: string;
  command: string;
  result: string;
  ok: boolean;
  timestamp: string;
}

const HISTORY_KEY = "loxone_console_history";
const MAX_HISTORY = 50;

@customElement("console-view")
export class ConsoleView extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property({ type: String }) miniserverId?: string;
  @state() private _uuid = "";
  @state() private _command = "";
  @state() private _sending = false;
  @state() private _history: HistoryEntry[] = [];
  @state() private _devices: LoxoneDevice[] = [];
  @state() private _suggestions: LoxoneDevice[] = [];

  static styles = css`
    :host {
      display: block;
    }
    .card {
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.1));
      margin-bottom: 16px;
    }
    .card-title {
      font-size: 13px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 16px;
    }
    .form {
      display: flex;
      gap: 8px;
      align-items: flex-end;
      flex-wrap: wrap;
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 4px;
      flex: 1;
      min-width: 150px;
      position: relative;
    }
    .field label {
      font-size: 12px;
      font-weight: 500;
      color: var(--secondary-text-color, #727272);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .field input {
      padding: 8px 12px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      font-size: 14px;
      font-family: var(--ha-font-family-code, "Roboto Mono", monospace);
      background: var(--primary-background-color, #fafafa);
      color: var(--primary-text-color, #212121);
    }
    .field input:focus {
      outline: none;
      border-color: var(--primary-color, #03a9f4);
    }
    .suggestions {
      position: absolute;
      top: 100%;
      left: 0;
      right: 0;
      background: var(--card-background-color, #fff);
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 0 0 8px 8px;
      max-height: 200px;
      overflow-y: auto;
      z-index: 10;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .suggestion {
      padding: 6px 12px;
      cursor: pointer;
      font-size: 13px;
      display: flex;
      justify-content: space-between;
    }
    .suggestion:hover {
      background: var(--table-row-alternative-background-color, #f5f5f5);
    }
    .suggestion .name {
      color: var(--primary-text-color, #212121);
    }
    .suggestion .type {
      color: var(--secondary-text-color, #727272);
      font-size: 11px;
    }
    button.send {
      padding: 8px 24px;
      border: none;
      border-radius: 8px;
      background: var(--primary-color, #03a9f4);
      color: #fff;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      white-space: nowrap;
    }
    button.send:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .history-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    .history-table th {
      padding: 8px 12px;
      text-align: left;
      font-weight: 500;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
      border-bottom: 2px solid var(--divider-color, #e0e0e0);
    }
    .history-table td {
      padding: 6px 12px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      font-family: var(--ha-font-family-code, "Roboto Mono", monospace);
      font-size: 12px;
    }
    .result-ok { color: var(--success-color, #4caf50); }
    .result-err { color: var(--error-color, #db4437); }
    .empty {
      text-align: center;
      color: var(--secondary-text-color, #727272);
      padding: 16px;
      font-size: 14px;
    }
    .hint {
      font-size: 12px;
      color: var(--secondary-text-color, #727272);
      margin-top: 8px;
    }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    this._loadHistory();
    this._loadDevices();
  }

  updated(changed: Map<string, unknown>): void {
    if (changed.has("miniserverId")) {
      this._loadDevices();
    }
  }

  private _loadHistory(): void {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      if (raw) this._history = JSON.parse(raw);
    } catch {
      // ignore
    }
  }

  private _saveHistory(): void {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(this._history.slice(-MAX_HISTORY)));
    } catch {
      // ignore
    }
  }

  private async _loadDevices(): Promise<void> {
    try {
      const result = await fetchDevices(this.hass, this.miniserverId);
      this._devices = result.devices;
    } catch {
      // non-critical
    }
  }

  private _onUuidInput(e: Event): void {
    this._uuid = (e.target as HTMLInputElement).value;
    const q = this._uuid.toLowerCase();
    if (q.length >= 2) {
      this._suggestions = this._devices
        .filter(
          (d) =>
            d.name.toLowerCase().includes(q) ||
            d.uuid.toLowerCase().includes(q) ||
            d.type.toLowerCase().includes(q),
        )
        .slice(0, 8);
    } else {
      this._suggestions = [];
    }
  }

  private _selectSuggestion(device: LoxoneDevice): void {
    this._uuid = device.uuid;
    this._suggestions = [];
  }

  private _onCommandInput(e: Event): void {
    this._command = (e.target as HTMLInputElement).value;
  }

  private _onKeyDown(e: KeyboardEvent): void {
    if (e.key === "Enter" && this._uuid && this._command) {
      this._send();
    }
    if (e.key === "Escape") {
      this._suggestions = [];
    }
  }

  private async _send(): Promise<void> {
    if (!this._uuid || !this._command || this._sending) return;
    this._sending = true;
    this._suggestions = [];
    const ts = new Date().toLocaleTimeString(this.hass.language || "en", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });

    try {
      const result = await sendCommand(this.hass, this._uuid, this._command, this.miniserverId);
      this._history = [
        ...this._history,
        { uuid: this._uuid, command: this._command, result: "OK", ok: true, timestamp: ts },
      ].slice(-MAX_HISTORY);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      this._history = [
        ...this._history,
        { uuid: this._uuid, command: this._command, result: msg, ok: false, timestamp: ts },
      ].slice(-MAX_HISTORY);
    } finally {
      this._sending = false;
      this._saveHistory();
    }
  }

  private _clearHistory(): void {
    this._history = [];
    this._saveHistory();
  }

  protected render() {
    return html`
      <div class="card">
        <h3 class="card-title">Send Command</h3>
        <div class="form">
          <div class="field">
            <label>UUID / Control</label>
            <input
              type="text"
              placeholder="Type UUID or control name…"
              .value=${this._uuid}
              @input=${this._onUuidInput}
              @keydown=${this._onKeyDown}
              @blur=${() => setTimeout(() => (this._suggestions = []), 200)}
            />
            ${this._suggestions.length > 0
              ? html`
                  <div class="suggestions">
                    ${this._suggestions.map(
                      (d) => html`
                        <div class="suggestion" @mousedown=${() => this._selectSuggestion(d)}>
                          <span class="name">${d.name}</span>
                          <span class="type">${d.type}</span>
                        </div>
                      `,
                    )}
                  </div>
                `
              : ""}
          </div>
          <div class="field">
            <label>Command</label>
            <input
              type="text"
              placeholder="On, Off, pulse, 50, …"
              .value=${this._command}
              @input=${this._onCommandInput}
              @keydown=${this._onKeyDown}
            />
          </div>
          <button
            class="send"
            ?disabled=${!this._uuid || !this._command || this._sending}
            @click=${this._send}
          >
            ${this._sending ? "Sending…" : "Send"}
          </button>
        </div>
        <p class="hint">
          Send a raw command to any Loxone control by UUID. Commands are the same
          as WebSocket/HTTP API values: On, Off, pulse, numeric values, etc.
        </p>
      </div>

      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <h3 class="card-title" style="margin:0">History</h3>
          ${this._history.length > 0
            ? html`<button
                style="font-size:12px;border:none;background:none;color:var(--secondary-text-color);cursor:pointer;text-decoration:underline"
                @click=${this._clearHistory}
              >Clear</button>`
            : ""}
        </div>
        ${this._history.length === 0
          ? html`<div class="empty">No commands sent yet</div>`
          : html`
              <table class="history-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>UUID</th>
                    <th>Command</th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  ${[...this._history].reverse().map(
                    (h) => html`
                      <tr>
                        <td>${h.timestamp}</td>
                        <td>${h.uuid}</td>
                        <td>${h.command}</td>
                        <td class="${h.ok ? "result-ok" : "result-err"}">${h.result}</td>
                      </tr>
                    `,
                  )}
                </tbody>
              </table>
            `}
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "console-view": ConsoleView;
  }
}
