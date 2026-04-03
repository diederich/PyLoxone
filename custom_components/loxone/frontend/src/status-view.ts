import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, GetStatusResult, GetStructureDiffResult } from "./types";
import { showToast } from "./types";
import { fetchStatus, fetchStructureDiff } from "./api";

@customElement("status-view")
export class StatusView extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property({ type: Number }) refreshKey = 0;
  @property({ type: String }) miniserverId?: string;
  @state() private _status: GetStatusResult | null = null;
  @state() private _diff: GetStructureDiffResult | null = null;
  @state() private _loading = true;
  @state() private _error = "";

  static styles = css`
    :host {
      display: block;
    }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 24px;
    }
    @media (max-width: 800px) {
      .grid {
        grid-template-columns: 1fr;
      }
    }
    .card {
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.1));
    }
    .card-title {
      font-size: 13px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 16px;
    }
    .info-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    .info-row:last-child {
      border-bottom: none;
    }
    .info-label {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
    }
    .info-value {
      font-size: 14px;
      font-weight: 500;
      color: var(--primary-text-color, #212121);
    }
    .conn-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }
    .conn-connected {
      background: var(--success-color, #4caf50);
      color: #fff;
    }
    .conn-reconnecting {
      background: var(--warning-color, #ff9800);
      color: #fff;
    }
    .conn-disconnected {
      background: var(--error-color, #db4437);
      color: #fff;
    }
    .diagnostics-title {
      font-size: 13px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 12px;
    }
    .diag-card {
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.1));
    }
    .diag-item {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 10px 0;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    .diag-item:last-child {
      border-bottom: none;
    }
    .diag-icon {
      font-size: 18px;
      flex-shrink: 0;
      width: 24px;
      text-align: center;
    }
    .diag-ok {
      color: var(--success-color, #4caf50);
    }
    .diag-warn {
      color: var(--warning-color, #ff9800);
    }
    .diag-label {
      font-size: 14px;
      color: var(--primary-text-color, #212121);
    }
    .diag-detail {
      font-size: 12px;
      color: var(--secondary-text-color, #727272);
      margin-top: 2px;
    }
    .status {
      color: var(--secondary-text-color, #727272);
      font-size: 14px;
      padding: 16px;
    }
    .error {
      color: var(--error-color, #db4437);
    }
    .download-btn {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 8px 16px; border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer;
      background: var(--card-background-color, #fff); color: var(--primary-text-color, #212121);
      transition: opacity 0.2s; margin-top: 16px;
    }
    .download-btn:hover { opacity: 0.75; }
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
      const [status, diff] = await Promise.all([
        fetchStatus(this.hass, this.miniserverId),
        fetchStructureDiff(this.hass, this.miniserverId).catch(() => null),
      ]);
      this._status = status;
      this._diff = diff;
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    } finally {
      this._loading = false;
    }
  }

  protected render() {
    if (this._loading) {
      return html`<p class="status">Loading status…</p>`;
    }
    if (this._error) {
      return html`<p class="status error">Error: ${this._error}</p>`;
    }
    if (!this._status) {
      return html`<p class="status">No status available.</p>`;
    }

    const s = this._status;
    const connClass =
      s.connection_state === "connected"
        ? "conn-connected"
        : s.connection_state === "reconnecting"
          ? "conn-reconnecting"
          : "conn-disconnected";

    const orphanCount = s.entities_without_state.length;

    return html`
      <div class="grid">
        <div class="card">
          <h3 class="card-title">Connection</h3>
          <div class="info-row">
            <span class="info-label">Status</span>
            <span class="conn-badge ${connClass}">${s.connection_state}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Host</span>
            <span class="info-value">${s.host}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Miniserver</span>
            <span class="info-value"
              >${s.miniserver_name || "—"}</span
            >
          </div>
          <div class="info-row">
            <span class="info-label">Serial</span>
            <span class="info-value">${s.serial_number || "—"}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Type</span>
            <span class="info-value">${s.miniserver_type || "—"}</span>
          </div>
        </div>

        <div class="card">
          <h3 class="card-title">Configuration</h3>
          <div class="info-row">
            <span class="info-label">Firmware</span>
            <span class="info-value">${s.software_version || "—"}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Project</span>
            <span class="info-value">${s.project_name || "—"}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Location</span>
            <span class="info-value">${s.location || "—"}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Controls</span>
            <span class="info-value">${s.controls_count}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Rooms</span>
            <span class="info-value">${s.rooms_count}</span>
          </div>
        </div>
      </div>

      <h3 class="diagnostics-title">Diagnostics</h3>
      <div class="diag-card">
        <div class="diag-item">
          <span class="diag-icon ${s.connection_state === "connected" ? "diag-ok" : "diag-warn"}"
            >${s.connection_state === "connected" ? "✓" : "⚠"}</span
          >
          <div>
            <div class="diag-label">Miniserver connection</div>
            <div class="diag-detail">${s.connection_state}</div>
          </div>
        </div>

        <div class="diag-item">
          <span class="diag-icon ${orphanCount === 0 ? "diag-ok" : "diag-warn"}"
            >${orphanCount === 0 ? "✓" : "⚠"}</span
          >
          <div>
            <div class="diag-label">Entities without state</div>
            <div class="diag-detail">
              ${orphanCount === 0
                ? `All ${s.entities_enabled} enabled entities have state`
                : html`${orphanCount} of ${s.entities_enabled} enabled
                    entities missing state:
                    <br />
                    ${s.entities_without_state
                      .slice(0, 10)
                      .join(", ")}${orphanCount > 10
                      ? ` … and ${orphanCount - 10} more`
                      : ""}`}
            </div>
          </div>
        </div>

        ${s.entities_disabled > 0
          ? html`
              <div class="diag-item">
                <span class="diag-icon diag-ok">ℹ</span>
                <div>
                  <div class="diag-label">Disabled entities</div>
                  <div class="diag-detail">
                    ${s.entities_disabled} entities disabled (bridged or
                    manually hidden)
                  </div>
                </div>
              </div>
            `
          : ""}

        <div class="diag-item">
          <span class="diag-icon diag-ok">✓</span>
          <div>
            <div class="diag-label">Device bridges</div>
            <div class="diag-detail">
              ${s.bridge_count} bridge${s.bridge_count !== 1 ? "s" : ""}
              configured
            </div>
          </div>
        </div>

        <div class="diag-item">
          <span class="diag-icon diag-ok">ℹ</span>
          <div>
            <div class="diag-label">Integration summary</div>
            <div class="diag-detail">
              ${s.controls_count} controls across ${s.rooms_count} rooms,
              ${s.entities_total} HA entities (${s.entities_enabled}
              enabled, ${s.entities_disabled} disabled)
            </div>
          </div>
        </div>
      </div>

      ${this._renderStructureDiff()}
      <button class="download-btn" @click=${this._downloadDiagnostics}>⬇ Download Diagnostics</button>
    `;
  }

  private _downloadDiagnostics(): void {
    try {
      const data = { status: this._status, structureDiff: this._diff, exported: new Date().toISOString() };
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `loxone-diagnostics-${new Date().toISOString().slice(0,10)}.json`;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast(this, "Diagnostics downloaded");
    } catch { showToast(this, "Failed to download diagnostics"); }
  }

  private _renderStructureDiff() {
    const d = this._diff;
    if (!d || !d.has_diff) {
      return html`
        <h3 class="diagnostics-title" style="margin-top:24px">Structure Changes</h3>
        <div class="diag-card">
          <div class="diag-item">
            <span class="diag-icon diag-ok">✓</span>
            <div>
              <div class="diag-label">No changes detected</div>
              <div class="diag-detail">
                Structure has not changed since the integration was loaded
              </div>
            </div>
          </div>
        </div>
      `;
    }

    const total = d.added.length + d.removed.length + d.changed.length;
    const ts = d.timestamp
      ? new Date(d.timestamp).toLocaleString(this.hass.language || "en")
      : "Unknown";

    return html`
      <h3 class="diagnostics-title" style="margin-top:24px">
        Structure Changes
        <span style="font-weight:400;font-size:12px;color:var(--secondary-text-color)">
          — ${total} change${total !== 1 ? "s" : ""} at ${ts}
        </span>
      </h3>
      <div class="diag-card">
        ${d.added.length > 0
          ? html`
              <div class="diag-item">
                <span class="diag-icon" style="color:var(--success-color,#4caf50)">+</span>
                <div>
                  <div class="diag-label">Added (${d.added.length})</div>
                  <div class="diag-detail">
                    ${d.added.map(
                      (a) => html`<div>${a.name} <span style="opacity:0.6">(${a.type})</span> — ${a.room || "no room"}</div>`,
                    )}
                  </div>
                </div>
              </div>
            `
          : ""}
        ${d.removed.length > 0
          ? html`
              <div class="diag-item">
                <span class="diag-icon" style="color:var(--error-color,#db4437)">−</span>
                <div>
                  <div class="diag-label">Removed (${d.removed.length})</div>
                  <div class="diag-detail">
                    ${d.removed.map(
                      (r) => html`<div>${r.name} <span style="opacity:0.6">(${r.type})</span> — ${r.room || "no room"}</div>`,
                    )}
                  </div>
                </div>
              </div>
            `
          : ""}
        ${d.changed.length > 0
          ? html`
              <div class="diag-item">
                <span class="diag-icon" style="color:var(--warning-color,#ff9800)">~</span>
                <div>
                  <div class="diag-label">Changed (${d.changed.length})</div>
                  <div class="diag-detail">
                    ${d.changed.map(
                      (c) => html`<div>${c.old.name} → ${c.new.name} <span style="opacity:0.6">(${c.new.type})</span></div>`,
                    )}
                  </div>
                </div>
              </div>
            `
          : ""}
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "status-view": StatusView;
  }
}
