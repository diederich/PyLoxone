import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, GetStructureResult, StructureControl } from "./types";
import { fetchStructure } from "./api";

type GroupBy = "room" | "category" | "type";

@customElement("structure-view")
export class StructureView extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property({ type: Number }) refreshKey = 0;
  @property({ type: String }) miniserverId?: string;
  @state() private _data: GetStructureResult | null = null;
  @state() private _loading = true;
  @state() private _error = "";
  @state() private _filter = "";
  @state() private _groupBy: GroupBy = "room";
  @state() private _expanded = new Set<string>();

  static styles = css`
    :host { display: block; }
    .page-intro {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 20px;
      line-height: 1.6;
      max-width: 800px;
    }
    .toolbar {
      display: flex; align-items: center; gap: 12px;
      margin-bottom: 16px; flex-wrap: wrap;
    }
    .toolbar input {
      padding: 8px 12px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 14px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      flex: 1; min-width: 200px;
    }
    .toolbar select {
      padding: 8px 10px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 13px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      cursor: pointer;
    }
    .summary {
      font-size: 13px; color: var(--secondary-text-color);
      margin-bottom: 12px;
    }
    .count { font-weight: 500; color: var(--primary-color, #03a9f4); }
    .group-card {
      background: var(--card-background-color, #fff);
      border-radius: 12px; margin-bottom: 12px;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,0.1));
      overflow: hidden;
    }
    .group-header {
      padding: 12px 16px; cursor: pointer; display: flex;
      justify-content: space-between; align-items: center;
      font-size: 14px; font-weight: 500;
      background: var(--table-header-background-color, var(--card-background-color, #fff));
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      user-select: none;
    }
    .group-header:hover { background: var(--table-row-alternative-background-color, #fafafa); }
    .group-count {
      font-size: 12px; font-weight: 400;
      color: var(--secondary-text-color);
    }
    .arrow { font-size: 10px; margin-right: 8px; }
    .ctrl-row {
      padding: 8px 16px; font-size: 13px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      display: flex; justify-content: space-between; align-items: center;
    }
    .ctrl-row:last-child { border-bottom: none; }
    .ctrl-name { font-weight: 500; }
    .ctrl-meta {
      display: flex; gap: 8px; align-items: center;
      color: var(--secondary-text-color); font-size: 12px;
    }
    .badge {
      display: inline-block; padding: 2px 8px; border-radius: 8px;
      font-size: 11px; font-weight: 500;
      background: var(--divider-color, #e0e0e0);
      color: var(--secondary-text-color);
    }
    .sub-row {
      padding: 4px 16px 4px 32px; font-size: 12px;
      color: var(--secondary-text-color);
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    .sub-row:last-child { border-bottom: none; }
    .states-chips {
      display: flex; gap: 4px; flex-wrap: wrap; margin-top: 2px;
    }
    .state-chip {
      padding: 1px 6px; border-radius: 8px; font-size: 10px;
      background: var(--secondary-background-color, #e8e8e8);
      color: var(--primary-text-color);
    }
    .status { color: var(--secondary-text-color); font-size: 14px; padding: 16px; }
    .error { color: var(--error-color, #db4437); }
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
      this._data = await fetchStructure(this.hass, this.miniserverId);
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    } finally {
      this._loading = false;
    }
  }

  private _toggle(key: string): void {
    const next = new Set(this._expanded);
    if (next.has(key)) next.delete(key); else next.add(key);
    this._expanded = next;
  }

  private _groupControls(controls: StructureControl[]): Map<string, StructureControl[]> {
    const groups = new Map<string, StructureControl[]>();
    for (const c of controls) {
      const key = this._groupBy === "room" ? (c.room || "No room")
        : this._groupBy === "category" ? (c.category || "No category")
        : c.type;
      const list = groups.get(key) || [];
      list.push(c);
      groups.set(key, list);
    }
    return new Map([...groups.entries()].sort((a, b) => a[0].localeCompare(b[0])));
  }

  protected render() {
    if (this._loading) return html`<p class="status">Loading structure…</p>`;
    if (this._error) return html`<p class="status error">Error: ${this._error}</p>`;
    if (!this._data) return html`<p class="status">No data.</p>`;

    let controls = this._data.controls;
    if (this._filter) {
      const lower = this._filter.toLowerCase();
      controls = controls.filter(
        (c) => c.name.toLowerCase().includes(lower) ||
               c.type.toLowerCase().includes(lower) ||
               c.room.toLowerCase().includes(lower) ||
               c.uuid.toLowerCase().includes(lower),
      );
    }

    const grouped = this._groupControls(controls);
    const totalSub = controls.reduce((n, c) => n + c.sub_controls.length, 0);

    return html`
      <p class="page-intro">
        The full control hierarchy from <code>LoxAPP3.json</code> — rooms, categories, controls,
        and their sub-controls with state key names. Use this to find a control's UUID before
        adding a bridge or sending a console command, or to verify what the Miniserver exposes
        after a structure change.
      </p>
      <div class="toolbar">
        <input type="search" placeholder="Search controls…" .value=${this._filter}
          @input=${(e: Event) => { this._filter = (e.target as HTMLInputElement).value; }} />
        <select .value=${this._groupBy}
          @change=${(e: Event) => { this._groupBy = (e.target as HTMLSelectElement).value as GroupBy; }}>
          <option value="room">Group by room</option>
          <option value="category">Group by category</option>
          <option value="type">Group by type</option>
        </select>
      </div>
      <p class="summary">
        <span class="count">${controls.length}</span> controls,
        <span class="count">${totalSub}</span> sub-controls,
        <span class="count">${this._data.rooms.length}</span> rooms,
        <span class="count">${this._data.categories.length}</span> categories
      </p>
      ${[...grouped.entries()].map(([group, ctrls]) => {
        const key = `g_${group}`;
        const open = this._expanded.has(key);
        return html`
          <div class="group-card">
            <div class="group-header" @click=${() => this._toggle(key)}>
              <div><span class="arrow">${open ? "▼" : "▶"}</span>${group}</div>
              <span class="group-count">${ctrls.length}</span>
            </div>
            ${open ? ctrls.map((c) => html`
              <div class="ctrl-row">
                <div>
                  <span class="ctrl-name">${c.name}</span>
                  ${c.states.length > 0 ? html`
                    <div class="states-chips">
                      ${c.states.map((s) => html`<span class="state-chip">${s}</span>`)}
                    </div>
                  ` : nothing}
                </div>
                <div class="ctrl-meta">
                  <span class="badge">${c.type}</span>
                  <span style="font-family:var(--ha-font-family-code,monospace);font-size:10px;opacity:0.6"
                        title=${c.uuid}>${c.uuid.slice(0, 8)}…</span>
                </div>
              </div>
              ${c.sub_controls.map((sc) => html`
                <div class="sub-row">
                  ${sc.name} <span class="badge">${sc.type}</span>
                  ${sc.states.length > 0 ? html`
                    <div class="states-chips">
                      ${sc.states.map((s) => html`<span class="state-chip">${s}</span>`)}
                    </div>
                  ` : nothing}
                </div>
              `)}
            `) : nothing}
          </div>
        `;
      })}
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "structure-view": StructureView;
  }
}
