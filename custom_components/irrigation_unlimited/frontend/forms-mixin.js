/**
 * Upstream implemented equivalent forms as a multi-step
 * config-entry options flow / subentry flow (config_flow.py); here they are
 * rendered as HTML inside the panel's modal instead.
 *
 * Forms mixin: builds the HTML for the modal forms
 * (controller, all-zones, zone, schedule, adjustment, sequence, sequence-zone,
 * global config) + the general modal structure (_modalHtml).
 */
import { esc } from "./lib/helpers.js";
import { fText, fToggle, fSelect, fPills, fSec, fEntityPicker } from "./lib/form-fields.js";
import { WEEKDAYS, MONTHS } from "./lib/constants.js";

export const formsMixin = {

_fGlobalConfig(d = {}) {
    const h = d.history || {};
    const c = d.clock   || {};
    return `<div class="form">
      <div class="fg-title">${this._t("sec.general")}</div>
      ${fText("granularity",      this._t("fld.granularity"),      d.granularity!=null?String(d.granularity):"", "60")}
      ${fText("refresh_interval", this._t("fld.refresh_interval"), d.refresh_interval!=null?String(d.refresh_interval):"", "30")}
      ${fToggle("rename_entities",this._t("fld.rename_entities"),!!d.rename_entities)}
      <div class="fg-title">${this._t("sec.history")}</div>
      ${fToggle("history_enabled",          this._t("fld.enabled"),              h.enabled!==false)}
      ${fText("history_span",               this._t("fld.hist_span"),          h.span!=null?String(h.span):"", "7")}
      ${fText("history_refresh_interval",   this._t("fld.refresh_interval"), h.refresh_interval!=null?String(h.refresh_interval):"", "120")}
      ${fText("history_read_delay",         this._t("fld.hist_read_delay"),       h.read_delay!=null?String(h.read_delay):"")}
      <div class="fg-title">${this._t("sec.clock")}</div>
      ${fSelect("clock_mode",this._t("fld.clock_mode"),[
        {value:"seer", label:this._t("opt.clock_seer")},
        {value:"fixed",label:this._t("opt.clock_fixed")},
      ], c.mode??"seer")}
      ${fToggle("clock_show_log",       this._t("fld.clock_show_log"),        !!c.show_log)}
      ${fText("clock_max_log_entries",  this._t("fld.clock_max_log"), c.max_log_entries!=null?String(c.max_log_entries):"", "50")}
    </div>`;
  },

  _fCtrl(d = {}) {
    return `<div class="form">
      ${fText("name",this._t("fld.ctrl_name"),d.name??"")}
      ${fText("controller_id",this._t("fld.ctrl_id"),d.controller_id??"")}
      ${fEntityPicker("entity_id",this._t("fld.entity_id_ctrl"),d.entity_id??"",this._hass)}
      ${fSelect("entity_states",this._t("fld.entity_states"),[
        {value:"all", label:this._t("opt.states_all")},
        {value:"on",  label:this._t("opt.states_on")},
        {value:"off", label:this._t("opt.states_off")},
        {value:"none",label:this._t("opt.states_none")},
      ], d.entity_states??"all")}
      ${fToggle("enabled",this._t("fld.enabled"),d.enabled!==false)}
      ${fToggle("queue_manual",this._t("fld.queue_manual"),!!d.queue_manual)}
      ${fToggle("show_sequence_status",this._t("fld.show_seq_status"),!!d.show_sequence_status)}
      ${fToggle("pause_next",this._t("fld.pause_next"),!!d.pause_next)}
      ${fText("preamble",this._t("fld.preamble"),d.preamble??"")}
      ${fText("postamble",this._t("fld.postamble"),d.postamble??"")}
    </div>`;
  },

  _fAllZones(d = {}) {
    d = d || {};
    const show = d.show || {};
    return `<div class="form">
      <div class="fg-title">${this._t("sec.run_time")}</div>
      ${fText("duration",  this._t("fld.duration"),      d.duration??"")}
      ${fText("minimum",   this._t("fld.minimum"), d.minimum??"")}
      ${fText("maximum",   this._t("fld.maximum"), d.maximum??"")}
      ${fText("threshold", this._t("fld.threshold"),      d.threshold??"")}
      ${fText("future_span",this._t("fld.future_span"),
        d.future_span!=null?String(d.future_span):"", "3")}
      <div class="fg-title">${this._t("sec.behaviour")}</div>
      ${fToggle("allow_manual",this._t("fld.allow_manual"),
        d.allow_manual===true)}
      ${fSelect("entity_states",this._t("fld.entity_states"),[
        {value:"all",  label:this._t("opt.states_all")},
        {value:"on",   label:this._t("opt.states_on")},
        {value:"off",  label:this._t("opt.states_off")},
        {value:"none", label:this._t("opt.states_none")},
      ], d.entity_states??"all")}
      <div class="fg-title">${this._t("sec.show_attr")}</div>
      ${fToggle("show_timeline",this._t("fld.show_timeline"),
        show.timeline===true)}
      ${fToggle("show_config",this._t("fld.show_config"),
        show.config===true)}
    </div>`;
  },

  _modalHtml() {
    const m = this._modal;
    const titles = {
      zone:this._t("modal.zone"), sched:this._t("modal.sched"), adj:this._t("modal.adj"),
      seq:this._t("modal.seq"), sqz:this._t("modal.sqz"), yaml:this._t("modal.yaml"),
      allzones:this._t("modal.allzones"), ctrl:this._t("modal.ctrl"),
      global:this._t("modal.global"),
    };
    const forms = {
      zone:     () => this._fZone(m.data??{}),
      sched:    () => this._fSched(m.data??{}),
      adj:      () => this._fAdj(m.data??{}),
      seq:      () => this._fSeq(m.data??{}),
      sqz:      () => this._fSqz(m.data??{}, m.eid),
      yaml:     () => `<pre class="yp">${esc(m.data??"")}</pre>`,
      allzones: () => this._fAllZones(m.data??{}),
      ctrl:     () => this._fCtrl(m.data??{}),
      global:   () => this._fGlobalConfig(m.data??{}),
    };
    const isEdit = m.type === "ctrl" ? !!m.ctrlId : !!m.data?.id;
    const prefix = isEdit ? this._t("modal.edit") : this._t("modal.add");
    // global and allzones are singleton forms (no add/edit) -- no prefix
    const noPrefix = new Set(["yaml","global","allzones"]);
    const title = noPrefix.has(m.type)
      ? (titles[m.type] ?? m.type)
      : `${prefix} ${titles[m.type]??m.type}`;
    return `
      <div class="modal">
        <div class="mh"><span class="mt">${title}</span>
          <button class="mc" data-a="close">✕</button></div>
        <div class="mb">${(forms[m.type]??(()=>""))()}</div>
        <div class="mf">
          <div class="val-err"  id="modal-err"></div>
          <div class="val-warn" id="modal-warn"></div>
          ${m.type!=="yaml"
            ? `<button class="btn btxt" data-a="close">${this._t("btn.cancel")}</button>
               <button class="btn bpri" data-a="save">${this._t("btn.save")}</button>`
            : `<button class="btn btxt" data-a="close">${this._t("btn.close")}</button>`}
        </div>
      </div>`;
  },

  _fZone(d) {
    const show = d.show || {};
    return `<div class="form">
      ${fText("name",this._t("fld.zone_name"),d.name??"")}
      ${fText("zone_id",this._t("fld.zone_id"),d.zone_id??"")}
      ${fEntityPicker("entity_id",this._t("fld.entity_id_zone"),d.entity_id??"",this._hass)}
      ${fSelect("entity_states",this._t("fld.entity_states"),[
        {value:"all", label:this._t("opt.states_all")},
        {value:"on",  label:this._t("opt.states_on")},
        {value:"off", label:this._t("opt.states_off")},
        {value:"none",label:this._t("opt.states_none")},
      ], d.entity_states??"all")}
      ${fToggle("enabled",this._t("fld.enabled"),d.enabled!==false)}
      ${fToggle("allow_manual",this._t("fld.allow_manual"),!!d.allow_manual)}
      ${fText("minimum",  this._t("fld.minimum"), d.minimum??"", "00:01")}
      ${fText("maximum",  this._t("fld.maximum"), d.maximum??"")}
      ${fText("threshold",this._t("fld.threshold"),         d.threshold??"")}
      ${fText("duration", this._t("fld.duration"),           d.duration??"")}
      ${fText("future_span",this._t("fld.future_span"),       d.future_span!=null?String(d.future_span):"", "3")}
      <div class="fg-title">${this._t("sec.show_attr")}</div>
      ${fToggle("show_timeline",this._t("fld.show_timeline"),
        !!(show.timeline || d.show_timeline))}
      ${fToggle("show_config",this._t("fld.show_config"),
        !!(show.config || d.show_config))}
    </div>`;
  },

  // Helper: date picker for from/until fields.
  // Initially shows only a month dropdown (—, Jan…Dec).
  // When a month is selected, a day dropdown (1…N) appears dynamically.
  // IU expects "dd Mon" format e.g. "01 Jan", "15 Jun".
  _fDate(prefix, label, val) {
    const MONS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    const MDAYS = {Jan:31,Feb:29,Mar:31,Apr:30,May:31,Jun:30,Jul:31,Aug:31,Sep:30,Oct:31,Nov:30,Dec:31};
    const parts = (val||"").trim().split(" ");
    const d = parts[0]||"", m = parts[1]||"";
    const maxDay = m ? (MDAYS[m]||31) : 0;
    const dayOpts = Array.from({length:maxDay},(_,i)=>{
      const v=String(i+1).padStart(2,"0");
      return `<option value="${v}"${d===v?" selected":""}>${i+1}</option>`;
    }).join("");
    return `<div class="fg">
      <label class="fl">${label}</label>
      <div class="iu-date-wrap" style="display:flex;gap:4px">
        <select class="fi" name="${prefix}_month">
          <option value="">—</option>
          ${MONS.map(mo=>`<option value="${mo}"${m===mo?" selected":""}>${mo}</option>`).join("")}
        </select>
        ${m ? `<select class="fi" name="${prefix}_day" style="flex:0 0 70px">${dayOpts}</select>` : ""}
      </div>
    </div>`;
  },

  _fSched(d) {
    return `<div class="form">
      ${fText("name",this._t("fld.seq_name"),d.name)}
      ${fText("schedule_id",this._t("fld.schedule_id"),d.schedule_id??"")}
      ${fToggle("enabled",this._t("fld.enabled"),d.enabled!==false)}
      ${fText("time",this._t("fld.sched_time"),d.time??"","")}
      ${fText("cron",this._t("fld.cron"),d.cron??"","0 6 * * 1,3,5")}
      ${fText("duration",this._t("fld.sched_duration"),d.duration??"","")}
      ${fSelect("anchor",this._t("fld.anchor"),[{value:"start",label:this._t("opt.anchor_start")},{value:"finish",label:this._t("opt.anchor_finish")}],d.anchor??"start")}
      ${fPills("weekday",this._t("fld.weekdays"),WEEKDAYS,d.weekday??[])}
      <div class="fg"><label class="fl">${this._t("fld.days")}</label><select class="fi" name="day"><option value="">${this._t("opt.day_all")}</option><option value="odd" ${(typeof d.day==="string"&&(d.day==="odd"||d.day==="even")?d.day:"")==="odd"?"selected":""}>${this._t("opt.day_odd")}</option><option value="even" ${(typeof d.day==="string"&&(d.day==="odd"||d.day==="even")?d.day:"")==="even"?"selected":""}>${this._t("opt.day_even")}</option></select></div>
      <div class="fg"><label class="fl">${this._t("fld.day_specific")}</label><input class="fi" type="text" name="day_num" value="${Array.isArray(d.day)?d.day.join(", "):(d.day!=null&&d.day!=="odd"&&d.day!=="even"?String(d.day):"")}"></div>
      ${fPills("month",this._t("fld.months"),MONTHS,d.month??[])}
      ${this._fDate("from",this._t("fld.from"),d.from??"")}
      ${this._fDate("until",this._t("fld.until"),d.until??"")}
    </div>`;
  },

  _fAdj(d) {
    const method = d.method ?? "percentage";
    const isTime = ["actual","increase","decrease"].includes(method);
    return `<div class="form">
      ${fSelect("method",this._t("fld.adj_method"),[
        {value:"actual",label:this._t("opt.adj_actual")},
        {value:"percentage",label:this._t("opt.adj_percentage")},
        {value:"increase",label:this._t("opt.adj_increase")},
        {value:"decrease",label:this._t("opt.adj_decrease")},
        {value:"reset",label:this._t("opt.adj_reset")},
        {value:"load_factor",label:this._t("opt.adj_load_factor")},
      ],method)}
      ${method!=="reset"?fText("value",isTime?this._t("fld.adj_value_duration"):method==="percentage"?this._t("fld.adj_value_percent"):this._t("fld.adj_value_factor"),d.value!=null?String(d.value):isTime?"":"",""):""}
      ${fText("minimum",this._t("fld.adj_minimum"),d.minimum??"","")}
      ${fText("maximum",this._t("fld.adj_maximum"),d.maximum??"","")}
      ${fPills("adj_weekday",this._t("fld.adj_weekday"),WEEKDAYS,d.weekday??[])}
      <div class="fg"><label class="fl">${this._t("fld.days")}</label><select class="fi" name="day"><option value="">${this._t("opt.day_all")}</option><option value="odd" ${(typeof d.day==="string"&&(d.day==="odd"||d.day==="even")?d.day:"")==="odd"?"selected":""}>${this._t("opt.day_odd")}</option><option value="even" ${(typeof d.day==="string"&&(d.day==="odd"||d.day==="even")?d.day:"")==="even"?"selected":""}>${this._t("opt.day_even")}</option></select></div>
      <div class="fg"><label class="fl">${this._t("fld.day_specific")}</label><input class="fi" type="text" name="day_num" value="${Array.isArray(d.day)?d.day.join(", "):(d.day!=null&&d.day!=="odd"&&d.day!=="even"?String(d.day):"")}"></div>
      ${fPills("adj_month",this._t("fld.adj_month"),MONTHS,d.month??[])}
      ${this._fDate("from",this._t("fld.from"),d.from??"")}
      ${this._fDate("until",this._t("fld.until"),d.until??"")}
      ${fText("load_factor",this._t("fld.load_factor"),d.load_factor!=null?String(d.load_factor):"","1")}
    </div>`;
  },

  _fSeq(d) {
    return `<div class="form">
      ${fText("name",this._t("fld.seq_name"),d.name)}
      ${fText("sequence_id",this._t("fld.seq_id"),d.sequence_id??"")}
      ${fToggle("enabled",this._t("fld.enabled"),d.enabled!==false)}
      ${fText("delay",this._t("fld.delay"),d.delay??"","")}
      ${fText("duration",this._t("fld.seq_duration"),d.duration??"","")}
      ${fText("repeat",this._t("fld.repeat"),d.repeat!=null?String(d.repeat):"","1")}
    </div>`;
  },

  _fSqz(d, eid) {
    const ctrlZones = (this._config?.controllers??[]).find(c=>c.entry_id===eid)?.zones??[];
    // zone_id must match the zone's real zone_id (or index+1 if unset -- IU default)
    const zoneOpts = ctrlZones.length
      ? ctrlZones.map((z,i)=>({value: z.zone_id || String(i+1), label:`${i+1}. ${z.name??"Zone "+(i+1)}`}))
      : [{value:"1",label:"Zone 1"}];
    const curZid = Array.isArray(d.zone_id) ? (d.zone_id[0]??"1") : (d.zone_id ?? "1");
    return `<div class="form">
      ${fSelect("zone_id",this._t("fld.sqz_zone"),zoneOpts,String(curZid))}
      ${fToggle("enabled",this._t("fld.enabled"),d.enabled!==false)}
      ${fText("duration",this._t("fld.sqz_duration"),d.duration??"","")}
      ${fText("delay",this._t("fld.sqz_delay"),d.delay??"","")}
      ${fText("repeat",this._t("fld.repeat"),d.repeat!=null?String(d.repeat):"","1")}
    </div>`;
  }

};
