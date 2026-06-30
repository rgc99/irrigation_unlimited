/**
 * Irrigation Unlimited -- Custom Panel
 *
 * --------------------------------------------------------------------------
 * Upstream has no frontend assets at all; all controller/zone/
 * sequence/schedule/adjustment/global-config management that upstream did
 * via the config-entry options flow / subentry flow (config_flow.py) is
 * implemented here as a custom sidebar panel (Web Component), talking to
 * the backend via the WebSocket commands in websocket_api.py.
 * --------------------------------------------------------------------------
 *
 * Main file: class skeleton (Web Component), lifecycle, data/translation
 * loading, base rendering, finders.
 *
 * The rest of the functionality is split into mixins (Object.assign on the
 * prototype):
 *   - render-mixin.js   -> builds the panel's HTML (cards, lists)
 *   - forms-mixin.js    -> builds the modal forms
 *   - actions-mixin.js  -> event handling, save, validation, YAML export
 *
 * Shared static modules (frontend/lib/):
 *   - constants.js      -> DOMAIN, WEEKDAYS, MONTHS
 *   - translations.js   -> translation system (_str, _tr, _fetchLang)
 *   - helpers.js        -> esc, normTime, callWS, fmtWd, fmtAdj
 *   - form-fields.js    -> HTML builders for form fields
 *   - styles.js         -> STYLES (CSS for the Shadow DOM)
 */

import { callWS, esc } from "./lib/helpers.js";
import { _str, _tr, _fetchLang } from "./lib/translations.js";
import { STYLES } from "./lib/styles.js";

import { renderMixin }  from "./render-mixin.js";
import { formsMixin }   from "./forms-mixin.js";
import { actionsMixin } from "./actions-mixin.js";

class IrrigationUnlimitedPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:"open"});
    this._hass = null;
    this._config = null;          // {controllers: [{entry_id, name, zones, sequences, ...}]}
    this._expanded = new Set();
    this._modal = null;
    this._loading = true;
    this._err = null;
  }

  _t(key, vars={}) { return _tr(key, vars); }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    const lang = (hass?.locale?.language || hass?.language || "en")
                   .split(/[-_]/)[0].toLowerCase();
    if (first) {
      this._loadTranslations(lang).then(() => this._load());
    } else if (lang !== this._lang) {
      this._loadTranslations(lang).then(() => this._draw());
    } else {
      // Lightweight update (no rebuild) of the "running" indicators on zones
      this._updateRunning();
    }
  }

  _updateRunning() {
    const sr = this.shadowRoot;
    if (!sr || !this._hass) return;
    sr.querySelectorAll("[data-entity]").forEach(el => {
      const eid = el.dataset.entity;
      if (!eid) return;
      const st = this._hass.states[eid];
      el.classList.toggle("running", !!(st && st.state === "on"));
    });
  }

  async _loadTranslations(lang) {
    this._lang = lang;
    const [en, cur] = await Promise.all([
      _fetchLang("en"),
      lang !== "en" ? _fetchLang(lang) : Promise.resolve(null),
    ]);
    _str.en      = en  || {};
    _str.current = cur || _str.en;
  }

  connectedCallback() {
    if (this._hass && this._loading) this._load();
  }

  async _load() {
    this._loading = true; this._err = null; this._draw();
    for (let i = 0; i < 3; i++) {
      try {
        const r = await callWS(this._hass, "config");
        this._config = r;
        this._globalConfig = r.global_config || {};
        this._err = null; break;
      } catch (e) {
        if (i < 2) await new Promise(r => setTimeout(r, 2500));
        else { this._err = `${this._t("err.load")}${e?.message ?? e}`; this._config = {controllers:[]}; }
      }
    }
    this._loading = false; this._draw();
  }

  _draw() {
    const sr = this.shadowRoot;
    sr.innerHTML = "";
    const style = document.createElement("style");
    style.textContent = STYLES;
    sr.appendChild(style);
    const wrap = document.createElement("div");
    wrap.className = "wrap";
    wrap.innerHTML = this._html();
    sr.appendChild(wrap);
    if (this._modal) {
      const ov = document.createElement("div");
      ov.className = "ov";
      ov.innerHTML = this._modalHtml();
      sr.appendChild(ov);
    }
    this._bind(sr);
    // Initialize select colors: fi-changed when value differs from data-default
    sr.querySelectorAll("select.fi[data-default]").forEach(sel => {
      sel.classList.toggle("fi-changed", sel.value !== sel.dataset.default);
    });
    this._updateRunning();
  }


  // ── Finders ────────────────────────────────────────────────────────────────

  _ctrl(eid)             { return (this._config?.controllers??[]).find(c=>c.entry_id===eid)??{}; }
  _fz(eid, zid)          { return (this._ctrl(eid).zones??[]).find(z=>z.id===zid)??{}; }
  _fs(eid, zid, sid)     { return (this._fz(eid,zid).schedules??[]).find(s=>s.id===sid)??{}; }
  _fa(eid, zid, aid)     { return (this._fz(eid,zid).adjustments??[]).find(a=>a.id===aid)??{}; }
  _fsq(eid, sqid)        { return (this._ctrl(eid).sequences??[]).find(s=>s.id===sqid)??{}; }
  _fsqz(eid, sqid, szid) { return (this._fsq(eid,sqid).zones??[]).find(z=>z.id===szid)??{}; }
  _fsqs(eid, sqid, sid)  { return (this._fsq(eid,sqid).schedules??[]).find(s=>s.id===sid)??{}; }
  _initEntityPickers(root) {
    root.querySelectorAll(".ep-inp").forEach(inp => {
      inp.addEventListener("input",  () => this._showEntities(inp));
      inp.addEventListener("focus",  () => this._showEntities(inp));
      inp.addEventListener("blur", () => {
        setTimeout(() => {
          const dd = inp.nextElementSibling;
          if (dd) dd.style.display = "none";
          const val = inp.value.trim();
          const row = inp.closest(".ep-row");
          const multi = inp.closest(".ep-multi");
          const isFirst = multi && multi.querySelector(".ep-row") === row;
          const invalid = val && this._hass?.states && !this._hass.states[val];
          if (isFirst) {
            // First row: never remove; clear if invalid text
            if (invalid) inp.value = "";
          } else if (row && multi && (!val || invalid)) {
            // Other rows: remove if empty or invalid
            row.remove();
            if (this._updateEpMulti) this._updateEpMulti(multi);
          } else if (!row && invalid) {
            inp.value = ""; // single picker fallback
          }
        }, 200);
      });
    });
  }

  _showEntities(inp) {
    if (!this._hass?.states) return;
    const DOMAINS = ["switch", "light", "valve", "cover"];
    const search = inp.value.trim().toLowerCase();
    const dd = inp.nextElementSibling;
    if (!dd) return;

    const matches = Object.entries(this._hass.states)
      .filter(([eid]) => DOMAINS.includes(eid.split(".")[0]))
      .filter(([eid, s]) => {
        if (!search) return true;
        const name = (s.attributes.friendly_name ?? "").toLowerCase();
        return eid.includes(search) || name.includes(search);
      })
      .sort(([a], [b]) => a.localeCompare(b));

    // No limit when user is searching; cap unfiltered list to avoid huge dropdown
    const shown = search ? matches : matches.slice(0, 50);

    if (!shown.length) { dd.style.display = "none"; return; }

    dd.innerHTML = shown.map(([eid, s]) => {
      const name = s.attributes.friendly_name ?? "";
      return `<div class="ep-item" data-val="${esc(eid)}">
        <span class="ep-id">${esc(eid)}</span>
        ${name ? `<span class="ep-name">${esc(name)}</span>` : ""}
      </div>`;
    }).join("");
    dd.style.display = "block";

    dd.querySelectorAll(".ep-item").forEach(item => {
      item.addEventListener("mousedown", e => {
        e.preventDefault();
        inp.value = item.dataset.val;
        dd.style.display = "none";
        // Update ＋ button directly (dispatching 'input' would reopen the dropdown)
        const multi = inp.closest(".ep-multi");
        if (multi && this._updateEpMulti) this._updateEpMulti(multi);
      });
    });
  }
}

// ── Mixins: render / forms / actions ────────────────────────────────────────────
Object.assign(
  IrrigationUnlimitedPanel.prototype,
  renderMixin,
  formsMixin,
  actionsMixin,
);

customElements.define("irrigation-unlimited-panel", IrrigationUnlimitedPanel);
