import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant } from "./types";
import "./devices-view";
import "./areas-view";
import "./bridges-view";
import "./status-view";

type TabId = "devices" | "areas" | "bridges" | "status";

@customElement("loxone-panel")
export class LoxonePanel extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @state() private _activeTab: TabId = "devices";

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
    h1 {
      font-size: 24px;
      font-weight: 400;
      margin: 0 0 16px;
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
    .placeholder {
      color: var(--secondary-text-color, #727272);
      font-size: 14px;
      padding: 24px;
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.1));
    }
  `;

  private _setTab(tab: TabId): void {
    this._activeTab = tab;
  }

  protected render() {
    return html`
      <h1>Loxone</h1>
      <div class="tabs">
        ${(["devices", "areas", "bridges", "status"] as TabId[]).map(
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
    switch (this._activeTab) {
      case "devices":
        return html`<devices-view .hass=${this.hass}></devices-view>`;
      case "areas":
        return html`<areas-view .hass=${this.hass}></areas-view>`;
      case "bridges":
        return html`<bridges-view .hass=${this.hass}></bridges-view>`;
      case "status":
        return html`<status-view .hass=${this.hass}></status-view>`;
    }
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "loxone-panel": LoxonePanel;
  }
}
