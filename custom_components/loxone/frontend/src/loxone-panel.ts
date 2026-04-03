import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, LoxoneEntry } from "./types";
import { fetchEntries } from "./api";
import "./devices-view";
import "./areas-view";
import "./bridges-view";
import "./status-view";
import "./monitor-view";
import "./console-view";

type TabId = "devices" | "areas" | "bridges" | "monitor" | "console" | "status";

@customElement("loxone-panel")
export class LoxonePanel extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @state() private _activeTab: TabId = "devices";
  @state() private _refreshKey = 0;
  @state() private _entries: LoxoneEntry[] = [];
  @state() private _selectedMiniserver: string | undefined;

  static styles = css`
    :host {
      display: block;
      padding: 24px;
      font-family: var(--ha-font-family, Roboto, sans-serif);
      color: var(--primary-text-color, #212121);
      background: var(--primary-background-color, #fafafa);
      min-height: 100vh;
      box-sizing: border-box;
    }
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 12px;
    }
    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    h1 {
      font-size: 24px;
      font-weight: 400;
      margin: 0;
    }
    .entry-select {
      padding: 6px 10px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      font-size: 13px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      cursor: pointer;
    }
    .refresh-btn {
      padding: 6px 14px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      transition: opacity 0.2s;
    }
    .refresh-btn:hover {
      opacity: 0.75;
    }
    .tabs {
      display: flex;
      gap: 0;
      margin-bottom: 24px;
      border-bottom: 2px solid var(--divider-color, #e0e0e0);
    }
    .tab {
      padding: 10px 20px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      color: var(--secondary-text-color, #727272);
      border-bottom: 2px solid transparent;
      margin-bottom: -2px;
      transition: color 0.2s, border-color 0.2s;
      user-select: none;
    }
    .tab:hover {
      color: var(--primary-text-color, #212121);
    }
    .tab.active {
      color: var(--primary-color, #03a9f4);
      border-bottom-color: var(--primary-color, #03a9f4);
    }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    this._loadEntries();
  }

  private async _loadEntries(): Promise<void> {
    try {
      const result = await fetchEntries(this.hass);
      this._entries = result.entries;
      if (!this._selectedMiniserver && this._entries.length > 0) {
        this._selectedMiniserver = this._entries[0].miniserver;
      }
    } catch {
      // Single-entry fallback: leave _selectedEntryId undefined
    }
  }

  private _setTab(tab: TabId): void {
    this._activeTab = tab;
  }

  private _refresh(): void {
    this._refreshKey++;
  }

  private _onEntryChange(e: Event): void {
    const select = e.target as HTMLSelectElement;
    this._selectedMiniserver = select.value;
    this._refreshKey++;
  }

  protected render() {
    const showSelector = this._entries.length > 1;
    return html`
      <div class="header">
        <div class="header-left">
          <h1>Loxone</h1>
          ${showSelector
            ? html`
                <select
                  class="entry-select"
                  .value=${this._selectedMiniserver ?? ""}
                  @change=${this._onEntryChange}
                >
                  ${this._entries.map(
                    (e) => html`
                      <option value=${e.miniserver}>
                        ${e.name || e.title || e.host}
                      </option>
                    `,
                  )}
                </select>
              `
            : nothing}
        </div>
        <button class="refresh-btn" @click=${this._refresh}>↻ Refresh</button>
      </div>
      <div class="tabs">
        ${(["devices", "areas", "bridges", "monitor", "console", "status"] as TabId[]).map(
          (tab) => html`
            <div
              class="tab ${this._activeTab === tab ? "active" : ""}"
              @click=${() => this._setTab(tab)}
            >
              ${tab.charAt(0).toUpperCase() + tab.slice(1)}
            </div>
          `,
        )}
      </div>
      ${this._renderTab()}
    `;
  }

  private _renderTab() {
    const k = this._refreshKey;
    const eid = this._selectedMiniserver;
    switch (this._activeTab) {
      case "devices":
        return html`<devices-view .hass=${this.hass} .refreshKey=${k} .miniserverId=${eid}></devices-view>`;
      case "areas":
        return html`<areas-view .hass=${this.hass} .refreshKey=${k} .miniserverId=${eid}></areas-view>`;
      case "bridges":
        return html`<bridges-view .hass=${this.hass} .refreshKey=${k} .miniserverId=${eid}></bridges-view>`;
      case "monitor":
        return html`<monitor-view .hass=${this.hass} .miniserverId=${eid}></monitor-view>`;
      case "console":
        return html`<console-view .hass=${this.hass} .miniserverId=${eid}></console-view>`;
      case "status":
        return html`<status-view .hass=${this.hass} .refreshKey=${k} .miniserverId=${eid}></status-view>`;
    }
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "loxone-panel": LoxonePanel;
  }
}
