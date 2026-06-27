/**
 * Render mixin: builds the HTML for the main panel
 * (controllers, zones, sequences, all-zones-config, global config).
 *
 * All methods run with `this` = the IrrigationUnlimitedPanel instance
 * (see Object.assign in irrigation-unlimited-panel.js).
 */
import { esc, fmtWd, fmtAdj } from "./lib/helpers.js";

export const renderMixin = {

_html() {
    if (this._loading) return `<div class="state">${this._t("status.loading")}</div>`;
    if (this._err)     return `<div class="state err">${esc(this._err)}</div>`;
    const ctrls = this._config?.controllers ?? [];
    return `
      <div class="toolbar">
        <span class="brand">💧 Irrigation Unlimited</span>
        <div class="tbr">
          <a class="btn btxt" href="/config/integrations/integration/irrigation_unlimited" target="_top">${this._t("btn.integration")}</a>
        </div>
      </div>
      ${this._globalConfigRow(this._globalConfig)}
      <div class="sh">
        <span class="st">${this._t("sec.controllers")}</span>
        <button class="btn bsm" data-a="add-ctrl">${this._t("btn.add_controller")}</button>
      </div>
      ${ctrls.length ? ctrls.map(c => this._ctrlCard(c)).join("") : `
        <div class="empty">
          <div class="eicon">🌱</div>
          <p>${this._t("status.no_ctrl")}</p>
        </div>`}`;
  },

  _ctrlCard(c) {
    const eid  = c.entry_id;
    const open = this._expanded.has(`c:${eid}`);
    const zn = (c.zones??[]).length, sn = (c.sequences??[]).length;
    return `
      <div class="card">
        <div class="ch" data-tog="c:${eid}">
          <span class="chev${open?" op":""}">›</span>
          <span class="ci">🌐</span>
          <span class="cn">${esc(c.name??"Controller")}</span>
          ${c.entity_id?`<span class="chip">🔌 ${esc(c.entity_id)}</span>`:""}
          ${c.enabled===false?`<span class="bdg off">${this._t("chip.disabled")}</span>`:""}
          <span class="cm">${this._t("cm.count_zones",{n:zn})} · ${this._t("cm.count_seqs",{n:sn})}</span>
          <div class="ia">
            <button class="ib" data-a="edit-ctrl" data-eid="${eid}"
               title="${this._t("title.edit_controller")}">✏️</button>
            <button class="ib rd" data-a="del-ctrl" data-eid="${eid}"
               data-name="${esc(c.name??'Controller')}"
               title="${this._t("title.delete_controller")}">🗑</button>
          </div>
        </div>
        ${open?`
        <div class="cb">
          ${c.queue_manual?`<div class="chips"><span class="chip">queue_manual</span>${c.show_log?`<span class="chip">log</span>`:""}</div>`:""}
          ${this._allZonesRow(eid, c.all_zones_config)}
          <div class="sh"><span class="st">${this._t("sec.zones")}</span>
            <button class="btn bsm" data-a="add-zone" data-eid="${eid}">${this._t("btn.add_zone")}</button>
          </div>
          ${this._zonesHtml(c)}
          <div class="sh"><span class="st">${this._t("sec.sequences")}</span>
            <button class="btn bsm" data-a="add-seq" data-eid="${eid}">${this._t("btn.add_sequence")}</button>
          </div>
          ${this._seqsHtml(c)}
          <div class="ctrl-yaml-row">
            <button class="btn btxt sm-btn" data-a="yaml" data-eid="${eid}">${this._t("btn.yaml")}</button>
          </div>
        </div>`:``}
      </div>`;
  },

  _zonesHtml(c) {
    const zones = c.zones ?? [];
    if (!zones.length) return `<p class="ei">${this._t("status.no_zones")}</p>`;
    return zones.map(z => this._zoneCard(c.entry_id, z)).join("");
  },

  _zoneCard(eid, z) {
    const open = this._expanded.has(`z:${z.id}`);
    const sn = (z.schedules??[]).length, an = (z.adjustments??[]).length;
    return `
      <div class="sc">
        <div class="sch" data-tog="z:${z.id}"${z.entity_id?` data-entity="${esc(z.entity_id)}"`:""}>
          <span class="chev${open?" op":""}">›</span>
          <span class="run-dot" title="${this._t("status.running")}"></span>
          <span class="ci">💧</span>
          <span class="cn">${esc(z.name??"Zone")}</span>
          ${z.enabled===false?`<span class="bdg off">${this._t("chip.disabled")}</span>`:""}
          <span class="cm">${this._t("cm.count_scheds",{n:sn})} · ${this._t("cm.count_adjs",{n:an})}</span>
          <div class="ia">
            <button class="ib" data-a="edit-zone" data-eid="${eid}" data-zid="${z.id}">✏️</button>
            <button class="ib rd" data-a="del-zone" data-eid="${eid}" data-zid="${z.id}">🗑</button>
          </div>
        </div>
        ${open?`
        <div class="scb">
          ${z.entity_id?`<span class="chip">🔌 ${esc(z.entity_id)}</span>`:""}
          ${z.zone_id?`<span class="chip">id: ${esc(z.zone_id)}</span>`:""}
          ${z.entity_states&&z.entity_states!=="all"?`<span class="chip">states: ${esc(z.entity_states)}</span>`:""}
          ${z.allow_manual?`<span class="chip">${this._t("chip.allow_manual")}</span>`:""}
          ${z.minimum?`<span class="chip">min: ${esc(z.minimum)}</span>`:""}
          ${z.maximum?`<span class="chip">max: ${esc(z.maximum)}</span>`:""}
          ${z.threshold?`<span class="chip">thr: ${esc(z.threshold)}</span>`:""}
          ${z.duration?`<span class="chip">rt: ${esc(z.duration)}</span>`:""}
          ${z.future_span!=null&&z.future_span!==3?`<span class="chip">fs: ${z.future_span}</span>`:""}
          ${(z.show&&z.show.timeline)||z.show_timeline?`<span class="chip">timeline</span>`:""}
          ${(z.show&&z.show.config)||z.show_config?`<span class="chip">show config</span>`:""}
          <div class="ssh"><span>${this._t("sec.schedules")}</span>
            <button class="btn bxs" data-a="add-sched" data-eid="${eid}" data-zid="${z.id}">${this._t("btn.add_schedule")}</button>
          </div>
          ${this._schedList(eid, z.id, z.schedules??[], "sched")}
          <div class="ssh"><span>${this._t("sec.adjustments")}</span>
            <button class="btn bxs" data-a="add-adj" data-eid="${eid}" data-zid="${z.id}">${this._t("btn.add_adj")}</button>
          </div>
          ${this._adjList(eid, z.id, z.adjustments??[])}
        </div>`:``}
      </div>`;
  },

  _schedList(eid, zid, schedules, prefix) {
    if (!schedules.length) return `<p class="ei sm">${this._t("status.no_schedules")}</p>`;
    return `<div class="lst">${schedules.map(s=>`
      <div class="li">
        <span class="lico">🕐</span>
        <span class="ln">${esc(s.name??"")}</span>
        <span class="ld">${s.time??"—"}</span><span class="ld">${s.duration??"—"}</span>
        <span class="ld mu">${s.cron?"cron":fmtWd(s.weekday)}</span>
        ${s.enabled===false?`<span class="bdg off">${this._t("chip.disabled")}</span>`:""}
        <div class="la">
          <button class="ib sm" data-a="edit-${prefix}" data-eid="${eid}" data-zid="${zid}" data-sid="${s.id}">✏️</button>
          <button class="ib sm rd" data-a="del-${prefix}" data-eid="${eid}" data-zid="${zid}" data-sid="${s.id}">🗑</button>
        </div>
      </div>`).join("")}</div>`;
  },

  _adjList(eid, zid, adjustments) {
    if (!adjustments.length) return `<p class="ei sm">${this._t("status.no_adjustments")}</p>`;
    return `<div class="lst">${adjustments.map(a=>`
      <div class="li">
        <span class="lico">⚙️</span>
        <span class="ln">${fmtAdj(a)}</span>
        <span class="ld mu">${fmtWd(a.weekday)}</span>
        <div class="la">
          <button class="ib sm" data-a="edit-adj" data-eid="${eid}" data-zid="${zid}" data-aid="${a.id}">✏️</button>
          <button class="ib sm rd" data-a="del-adj" data-eid="${eid}" data-zid="${zid}" data-aid="${a.id}">🗑</button>
        </div>
      </div>`).join("")}</div>`;
  },

  _seqsHtml(c) {
    const seqs = c.sequences ?? [];
    if (!seqs.length) return `<p class="ei">${this._t("status.no_sequences")}</p>`;
    return seqs.map(s => this._seqCard(c.entry_id, s, c.zones??[])).join("");
  },

  _seqCard(eid, s, ctrlZones) {
    const open = this._expanded.has(`s:${s.id}`);
    const zn = (s.zones??[]).length, sn = (s.schedules??[]).length;
    return `
      <div class="sc seq">
        <div class="sch" data-tog="s:${s.id}">
          <span class="chev${open?" op":""}">›</span>
          <span class="ci">🔄</span>
          <span class="cn">${esc(s.name??"Sequence")}</span>
          ${s.enabled===false?`<span class="bdg off">${this._t("chip.disabled")}</span>`:""}
          <span class="cm">${this._t("cm.count_zones",{n:zn})} · ${this._t("cm.count_scheds",{n:sn})}</span>
          <div class="ia">
            <button class="ib" data-a="edit-seq" data-eid="${eid}" data-sqid="${s.id}">✏️</button>
            <button class="ib rd" data-a="del-seq" data-eid="${eid}" data-sqid="${s.id}">🗑</button>
          </div>
        </div>
        ${open?`
        <div class="scb">
          <div class="chips">
            ${s.sequence_id?`<span class="chip">id: ${esc(s.sequence_id)}</span>`:""}
            ${s.delay?`<span class="chip">delay: ${esc(s.delay)}</span>`:""}
            ${s.duration?`<span class="chip">max: ${esc(s.duration)}</span>`:""}
            ${s.repeat!=null&&s.repeat!==1?`<span class="chip">×${s.repeat}</span>`:""}
          </div>
          <div class="ssh"><span>${this._t("sec.seq_zones")}</span>
            <button class="btn bxs" data-a="add-sqz" data-eid="${eid}" data-sqid="${s.id}">${this._t("btn.add_sqz")}</button>
          </div>
          ${this._sqzList(eid, s, ctrlZones)}
          <div class="ssh"><span>${this._t("sec.seq_schedules")}</span>
            <button class="btn bxs" data-a="add-sqsched" data-eid="${eid}" data-sqid="${s.id}">${this._t("btn.add_sqsched")}</button>
          </div>
          ${this._sqSchedList(eid, s.id, s.schedules??[])}
        </div>`:``}
      </div>`;
  },

  _sqzList(eid, s, ctrlZones) {
    const zones = s.zones ?? [];
    if (!zones.length) return `<p class="ei sm">${this._t("status.no_seq_zones")}</p>`;
    return `<div class="lst">${zones.map(sz=>{
      const zname = ctrlZones.find(z=>z.zone_id===sz.zone_id)?.name
        ?? ctrlZones[(parseInt(sz.zone_id,10)||1)-1]?.name
        ?? `Zone ${sz.zone_id}`;
      return `
        <div class="li">
          <span class="lico">💧</span>
          <span class="ln">${esc(zname)}</span>
          <span class="ld">${sz.duration??"—"}</span>
          ${sz.repeat>1?`<span class="ld">×${sz.repeat}</span>`:""}
          ${sz.enabled===false?`<span class="bdg off">${this._t("chip.disabled")}</span>`:""}
          <div class="la">
            <button class="ib sm" data-a="edit-sqz" data-eid="${eid}" data-sqid="${s.id}" data-szid="${sz.id}">✏️</button>
            <button class="ib sm rd" data-a="del-sqz" data-eid="${eid}" data-sqid="${s.id}" data-szid="${sz.id}">🗑</button>
          </div>
        </div>`}).join("")}</div>`;
  },

  _sqSchedList(eid, sqid, schedules) {
    if (!schedules.length) return `<p class="ei sm">${this._t("status.no_schedules")}</p>`;
    return `<div class="lst">${schedules.map(s=>`
      <div class="li">
        <span class="lico">🕐</span>
        <span class="ln">${esc(s.name??"")}</span>
        <span class="ld">${s.time??"—"}</span><span class="ld">${s.duration??"—"}</span>
        <span class="ld mu">${s.cron?"cron":fmtWd(s.weekday)}</span>
        ${s.enabled===false?`<span class="bdg off">${this._t("chip.disabled")}</span>`:""}
        <div class="la">
          <button class="ib sm" data-a="edit-sqsched" data-eid="${eid}" data-sqid="${sqid}" data-sid="${s.id}">✏️</button>
          <button class="ib sm rd" data-a="del-sqsched" data-eid="${eid}" data-sqid="${sqid}" data-sid="${s.id}">🗑</button>
        </div>
      </div>`).join("")}</div>`;
  },

  _allZonesRow(eid, azc) {
    azc = azc || {};
    const open = this._expanded.has(`az:${eid}`);
    const keys = ["minimum","maximum","threshold","duration","delay",
                  "future_span","allow_manual","entity_states"];
    const items = keys
      .filter(k => azc[k] != null && azc[k] !== "")
      .map(k => `<span class="chip">${k}: ${esc(String(azc[k]))}</span>`);
    if (azc.show) {
      if (azc.show.timeline) items.push(`<span class="chip">timeline</span>`);
      if (azc.show.config)   items.push(`<span class="chip">show_config</span>`);
    }
    return `
      <div class="sc">
        <div class="sch" data-tog="az:${eid}">
          <span class="chev${open?" op":""}">›</span>
          <span class="ci">🌿</span>
          <span class="cn">${this._t("sec.all_zones")}</span>
          ${items.length?`<span class="bdg">${this._t("chip.configured")}</span>`:""}
          <div class="ia">
            <button class="ib" data-a="edit-allzones" data-eid="${eid}"
               title="${this._t("title.edit_allzones")}">✏️</button>
          </div>
        </div>
        ${open?`<div class="scb">
          ${items.length
            ? `<div class="chips">${items.join("")}</div>`
            : `<span class="cm">${this._t("status.no_defaults")}</span>`}
        </div>`:""}
      </div>`;
  },

  _globalConfigRow(cfg) {
    cfg = cfg || {};
    const open = this._expanded.has("__global__");
    const items = [];
    if (cfg.granularity      != null) items.push(`<span class="chip">granularity: ${esc(String(cfg.granularity))}</span>`);
    if (cfg.refresh_interval != null) items.push(`<span class="chip">refresh: ${esc(String(cfg.refresh_interval))}</span>`);
    if (cfg.rename_entities)          items.push(`<span class="chip">rename_entities</span>`);
    if (cfg.history) {
      const h = cfg.history;
      if (h.enabled===false)         items.push(`<span class="chip">history off</span>`);
      if (h.span!=null)              items.push(`<span class="chip">history.span: ${esc(String(h.span))}</span>`);
      if (h.refresh_interval!=null)  items.push(`<span class="chip">history.refresh: ${esc(String(h.refresh_interval))}</span>`);
    }
    if (cfg.clock) {
      const c = cfg.clock;
      if (c.mode && c.mode!=="seer") items.push(`<span class="chip">clock: ${esc(c.mode)}</span>`);
      if (c.show_log)                items.push(`<span class="chip">clock log</span>`);
    }
    return `
      <div class="sc">
        <div class="sch" data-tog="__global__">
          <span class="chev${open?" op":""}">›</span>
          <span class="ci">⚙</span>
          <span class="cn">${this._t("sec.configuration")}</span>
          ${items.length?`<span class="bdg">${this._t("chip.configured")}</span>`:""}
          <div class="ia">
            <button class="ib" data-a="edit-global" title="${this._t("title.edit")}">✏️</button>
          </div>
        </div>
        ${open?`<div class="scb">
          ${items.length
            ?`<div class="chips">${items.join("")}</div>`
            :`<span class="cm">${this._t("status.defaults")}</span>`}
        </div>`:""}
      </div>`;
  }

};
