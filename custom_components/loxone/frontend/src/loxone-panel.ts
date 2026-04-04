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
import "./logs-view";
import "./structure-view";

type TabId = "devices" | "areas" | "bridges" | "monitor" | "console" | "logs" | "structure" | "status";
const TABS: TabId[] = ["devices", "areas", "bridges", "monitor", "console", "logs", "structure", "status"];

const TAB_PANEL_ID = "loxone-main-tabpanel";

function _tabId(tab: TabId): string {
  return `loxone-tab-${tab}`;
}

function _readTabFromHash(): TabId {
  const raw = window.location.hash.replace(/^#/, "").split("?")[0];
  return TABS.includes(raw as TabId) ? (raw as TabId) : "devices";
}

@customElement("loxone-panel")
export class LoxonePanel extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @state() private _activeTab: TabId = _readTabFromHash();
  @state() private _refreshKey = 0;
  @state() private _entries: LoxoneEntry[] = [];
  @state() private _selectedMiniserver: string | undefined;

  private _onHashChange = () => {
    this._activeTab = _readTabFromHash();
  };

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
    .refresh-btn:focus-visible {
      outlineOffset: 2px;
      outline: 2px solid var(--primary-color, #03a9f4);
    }
    .tabs {
      display: flex;
      gap: 0;
      margin-bottom: 24px;
      border-bottom: 2px solid var(--divider-color, #e0e0e0);
      overflow-x: auto;
    }
    .tab {
      margin: 0;
      padding: 10px 20px;
      cursor: pointer;
      font: inherit;
      font-size: 14px;
      font-weight: 500;
      color: var(--secondary-text-color, #727272);
      border: none;
      border-bottom: 2px solid transparent;
      margin-bottom: -2px;
      background: transparent;
      border-radius: 0;
      transition: color 0.2s, border-color 0.2s;
      user-select: none;
      white-space: nowrap;
      appearance: none;
      -webkit-appearance: none;
    }
    .tab:hover {
      color: var(--primary-text-color, #212121);
    }
    .tab.active {
      color: var(--primary-color, #03a9f4);
      border-bottom-color: var(--primary-color, #03a9f4);
    }
    .tab:focus-visible {
      outlineOffset: 2px;
      outline: 2px solid var(--primary-color, #03a9f4);
    }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    window.addEventListener("hashchange", this._onHashChange);
    this._loadEntries();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    window.removeEventListener("hashchange", this._onHashChange);
  }

  private async _loadEntries(): Promise<void> {
    try {
      const result = await fetchEntries(this.hass);
      this._entries = result.entries;
      if (!this._selectedMiniserver && this._entries.length > 0) {
        this._selectedMiniserver = this._entries[0].miniserver;
      }
    } catch {
      // Single-entry fallback
    }
  }

  private _setTab(tab: TabId): void {
    this._activeTab = tab;
    window.location.hash = tab === "devices" ? "" : tab;
  }

  private _refresh(): void {
    this._refreshKey++;
  }

  private _onTabKeydown(e: KeyboardEvent, tab: TabId): void {
    const idx = TABS.indexOf(tab);
    if (idx < 0) return;

    let nextIdx: number | null = null;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      nextIdx = (idx + 1) % TABS.length;
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      nextIdx = (idx - 1 + TABS.length) % TABS.length;
    } else if (e.key === "Home") {
      nextIdx = 0;
    } else if (e.key === "End") {
      nextIdx = TABS.length - 1;
    }
    if (nextIdx === null) return;

    e.preventDefault();
    const nextTab = TABS[nextIdx]!;
    this._setTab(nextTab);
    void this.updateComplete.then(() => {
      this.shadowRoot?.querySelector<HTMLButtonElement>(`#${_tabId(nextTab)}`)?.focus();
    });
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
                  aria-label="Miniserver"
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
        <button
          type="button"
          class="refresh-btn"
          aria-label="Refresh current view"
          @click=${this._refresh}
        >
          ↻ Refresh
        </button>
      </div>
      <div class="tabs" role="tablist" aria-label="Loxone sections">
        ${TABS.map(
          (tab) => {
            const selected = this._activeTab === tab;
            const label = tab.charAt(0).toUpperCase() + tab.slice(1);
            return html`
              <button
                type="button"
                role="tab"
                id=${_tabId(tab)}
                class="tab ${selected ? "active" : ""}"
                aria-selected=${selected ? "true" : "false"}
                aria-controls=${TAB_PANEL_ID}
                tabindex=${selected ? 0 : -1}
                @click=${() => this._setTab(tab)}
                @keydown=${(e: KeyboardEvent) => this._onTabKeydown(e, tab)}
              >
                ${label}
              </button>
            `;
          },
        )}
      </div>
      <div
        role="tabpanel"
        id=${TAB_PANEL_ID}
        aria-labelledby=${_tabId(this._activeTab)}
      >
        ${this._renderTab()}
      </div>
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
      case "logs":
        return html`<logs-view .hass=${this.hass}></logs-view>`;
      case "structure":
        return html`<structure-view .hass=${this.hass} .refreshKey=${k} .miniserverId=${eid}></structure-view>`;
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
