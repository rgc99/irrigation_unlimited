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

  _fCtrl(d = {}, ctrlId) {
    const ctrls = this._config?.controllers ?? [];
    const ctrlIdx = ctrlId
      ? ctrls.findIndex(c => c.entry_id === ctrlId)
      : ctrls.length;
    const ctrlPlaceholder = `Controller ${ctrlIdx + 1}`;
    return `<div class="form">
      <div class="fg-title">${this._t("sec.identity")}</div>
      ${fText("name",this._t("fld.ctrl_name"),d.name??"",ctrlPlaceholder)}
      ${fText("controller_id",this._t("fld.ctrl_id"),d.controller_id??"",String(ctrlIdx+1))}
      ${fEntityPicker("entity_id",this._t("fld.entity_id_ctrl"),d.entity_id??"")}
      ${fSelect("entity_states",this._t("fld.entity_states"),[
        {value:"all", label:this._t("opt.states_all")},
        {value:"on",  label:this._t("opt.states_on")},
        {value:"off", label:this._t("opt.states_off")},
        {value:"none",label:this._t("opt.states_none")},
      ], d.entity_states??"all")}
      <div class="fg-title">${this._t("sec.behaviour")}</div>
      ${fToggle("enabled",this._t("fld.enabled"),d.enabled!==false)}
      ${fToggle("queue_manual",this._t("fld.queue_manual"),!!d.queue_manual)}
      ${fToggle("show_sequence_status",this._t("fld.show_seq_status"),!!d.show_sequence_status)}
      ${fToggle("pause_next",this._t("fld.pause_next"),!!d.pause_next)}
      <div class="fg-title">${this._t("sec.timing")}</div>
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
      zone:     () => this._fZone(m.data??{}, m.eid),
      sched:    () => this._fSched(m.data??{}, m.eid, m.zoneId, !!m.seqId),
      adj:      () => this._fAdj(m.data??{}),
      seq:      () => this._fSeq(m.data??{}, m.eid),
      sqz:      () => this._fSqz(m.data??{}, m.eid),
      yaml:     () => `<pre class="yp">${esc(m.data??"")}</pre>`,
      allzones: () => this._fAllZones(m.data??{}),
      ctrl:     () => this._fCtrl(m.data??{}, m.ctrlId),
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
            : `<button class="btn btxt" data-a="close">${this._t("btn.close")}</button>
               <button class="btn btxt" data-a="copy-yaml">${this._t("btn.copy")}</button>
               <button class="btn bpri" data-a="download-yaml">${this._t("btn.download")}</button>`}
        </div>
      </div>`;
  },

  _fZone(d, eid) {
    const ctrl = this._config?.controllers?.find(c => c.entry_id === eid);
    const zones = ctrl?.zones ?? [];
    const zoneIdx = d.id ? zones.findIndex(z => z.id === d.id) : zones.length;
    const zonePlaceholder = `Zone ${zoneIdx + 1}`;
    const show = d.show || {};
    return `<div class="form">
      <div class="fg-title">${this._t("sec.identity")}</div>
      ${fText("name",this._t("fld.zone_name"),d.name??"",zonePlaceholder)}
      ${fText("zone_id",this._t("fld.zone_id"),d.zone_id??"",String(zoneIdx+1))}
      <div class="fg">
        <div class="ep-header">
          <label class="fl">${this._t("fld.entity_id_zone")}</label>
          ${(() => {
            const eids = Array.isArray(d.entity_id) ? d.entity_id.filter(Boolean)
                         : d.entity_id ? [d.entity_id] : [];
            // ＋ disabled when last row is empty (incl. initial empty row)
            const lastEmpty = eids.length === 0 || !eids[eids.length - 1];
            return `<button class="btn bxs ep-add" data-a="add-ep-row" type="button"
                            ${lastEmpty ? "disabled" : ""}>＋</button>`;
          })()}
        </div>
        <div class="ep-multi">${(() => {
          const eids = Array.isArray(d.entity_id) ? d.entity_id.filter(Boolean)
                       : d.entity_id ? [d.entity_id] : [];
          return eids.map((eid, i) =>
            `<div class="ep-row">
              <div class="epw">
                <input class="fi ep-inp" type="text" value="${esc(eid)}"
                       placeholder="${esc(this._t("fld.entity_picker_placeholder"))}" autocomplete="off">
                <div class="ep-dd" style="display:none"></div>
              </div>
              <button class="ib rd ep-del" data-a="del-ep-row" type="button"
        >×</button>
            </div>`).join("");
        })()}</div>
      </div>
      ${fSelect("entity_states",this._t("fld.entity_states"),[
        {value:"all", label:this._t("opt.states_all")},
        {value:"on",  label:this._t("opt.states_on")},
        {value:"off", label:this._t("opt.states_off")},
        {value:"none",label:this._t("opt.states_none")},
      ], d.entity_states??"all")}
      <div class="fg-title">${this._t("sec.behaviour")}</div>
      ${fToggle("enabled",this._t("fld.enabled"),d.enabled!==false)}
      ${fToggle("allow_manual",this._t("fld.allow_manual"),!!d.allow_manual)}
      <div class="fg-title">${this._t("sec.run_time")}</div>
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

  // Helper: year+month+day picker for start_n_days (EVERY_N_DAYS_SCHEMA).
  // Generates: <year-select> <month-select> <day-select (dynamic)>
  // Saves as "YYYY-MM-DD" for cv.date compatibility.
  _fStartDate(val) {
    const MONS  = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    // Default to today when no saved value
    const today = new Date();
    const defY  = String(today.getFullYear());
    const defM  = String(today.getMonth()+1).padStart(2,"0");
    const defD  = String(today.getDate()).padStart(2,"0");
    const parts = (val||"").split("-");
    const yr    = parts.length===3 ? parts[0] : defY;
    const mo    = parts.length===3 ? parts[1] : defM;
    const dy    = parts.length===3 ? parts[2] : defD;
    const moName = MONS[parseInt(mo,10)-1] || MONS[parseInt(defM,10)-1];
    // Leap year check for February
    const yrN = parseInt(yr,10);
    const isLeap = yrN ? ((yrN%4===0 && yrN%100!==0) || yrN%400===0) : true;
    const MDAYS = {Jan:31,Feb:isLeap?29:28,Mar:31,Apr:30,May:31,Jun:30,Jul:31,Aug:31,Sep:30,Oct:31,Nov:30,Dec:31};
    const maxDay = MDAYS[moName]||31;
    const curY   = today.getFullYear();
    const yearOpts = Array.from({length:11},(_,i)=>{
      const y=curY+i; return `<option value="${y}"${yr===String(y)?" selected":""}>${y}</option>`;
    }).join("");
    const monthOpts = MONS.map((m,i)=>{
      const v=String(i+1).padStart(2,"0");
      return `<option value="${v}"${mo===v?" selected":""}>${m}</option>`;
    }).join("");
    const dayOpts = Array.from({length:maxDay},(_,i)=>{
      const v=String(i+1).padStart(2,"0");
      return `<option value="${v}"${dy===v?" selected":""}>${i+1}</option>`;
    }).join("");
    return `<div class="fg">
      <label class="fl">${this._t("fld.start_n_days")}</label>
      <div style="display:flex;gap:4px">
        <select class="fi" name="start_n_days_year" style="flex:0 0 90px" data-default="${yr}">${yearOpts}</select>
        <select class="fi" name="start_n_days_month" data-default="${mo}">${monthOpts}</select>
        <select class="fi" name="start_n_days_day" style="flex:0 0 70px" data-default="${dy}">${dayOpts}</select>
      </div>
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
        <select class="fi" name="${prefix}_month" data-default="${m}">
          <option value="">—</option>
          ${MONS.map(mo=>`<option value="${mo}"${m===mo?" selected":""}>${mo}</option>`).join("")}
        </select>
        ${m ? `<select class="fi" name="${prefix}_day" style="flex:0 0 70px" data-default="01">${dayOpts}</select>` : ""}
      </div>
    </div>`;
  },

  _fSched(d, eid, zoneId, isSeqSched=false) {
    const ctrl = this._config?.controllers?.find(c => c.entry_id === eid);
    const zone = ctrl?.zones?.find(z => z.id === zoneId);
    const scheds = zone?.schedules ?? [];
    const schedIdx = d.id ? scheds.findIndex(s => s.id === d.id) : scheds.length;
    const schedPlaceholder = `Schedule ${schedIdx + 1}`;
    // time can be a string (HH:MM) or a sun-event object {sun, before?, after?}
    const isSun    = d.time && typeof d.time === "object" && d.time.sun;
    const timeStr  = isSun ? "" : (d.time ?? "");
    const sunVal   = isSun ? d.time.sun : "";
    const beforeVal= isSun ? (d.time.before ?? "") : "";
    const afterVal = isSun ? (d.time.after  ?? "") : "";
    // day can be "odd"/"even", array/int, or {every_n_days, start_n_days}
    const isEvery  = !!(d.day && typeof d.day === "object" && d.day.every_n_days);
    const dayDp    = !isEvery && typeof d.day === "string" && (d.day==="odd"||d.day==="even") ? d.day : "";
    const dayDn    = !isEvery && !dayDp ? (Array.isArray(d.day)?d.day.join(", "):(d.day!=null?String(d.day):"")) : "";
    const everyN   = isEvery ? String(d.day.every_n_days) : "";
    const startN   = isEvery ? (d.day.start_n_days ?? "") : "";
    return `<div class="form">
      <div class="fg-title">${this._t("sec.identity")}</div>
      ${fText("name",this._t("fld.seq_name"),d.name,schedPlaceholder)}
      ${fText("schedule_id",this._t("fld.schedule_id"),d.schedule_id??"")}
      ${fToggle("enabled",this._t("fld.enabled"),d.enabled!==false)}
      <div class="fg-title">${this._t("sec.timing_sched")}<span class="req">*</span></div>
      ${fText("time",this._t("fld.sched_time"),timeStr,"")}
      <div class="fg">
        <label class="fl">${this._t("fld.sun")}</label>
        <select class="fi" name="sun" data-default="${sunVal}">
          <option value="">—</option>
          <option value="sunrise" ${sunVal==="sunrise"?"selected":""}>${this._t("opt.sun_rise")}</option>
          <option value="sunset"  ${sunVal==="sunset" ?"selected":""}>${this._t("opt.sun_set")}</option>
        </select>
        <div class="sun-offsets">${sunVal ? `
          <div class="fg"><label class="fl">${this._t("fld.before")}</label>
            <input class="fi" type="text" name="before" value="${beforeVal}" placeholder=""></div>
          <div class="fg"><label class="fl">${this._t("fld.after")}</label>
            <input class="fi" type="text" name="after" value="${afterVal}" placeholder=""></div>` : ""}
        </div>
      </div>
      ${fText("cron",this._t("fld.cron"),d.cron??"","0 6 * * 1,3,5")}
      ${fText("duration",this._t("fld.sched_duration"),d.duration??"","",!isSeqSched)}
      ${fSelect("anchor",this._t("fld.anchor"),[{value:"start",label:this._t("opt.anchor_start")},{value:"finish",label:this._t("opt.anchor_finish")}],d.anchor??"start")}
      <div class="fg-title">${this._t("sec.day_filter")}</div>
      ${fPills("weekday",this._t("fld.weekdays"),WEEKDAYS,d.weekday??[])}
      <div class="fg"><label class="fl">${this._t("fld.days")}</label><select class="fi" name="day" data-default=""><option value="">${this._t("opt.day_all")}</option><option value="odd" ${dayDp==="odd"?"selected":""}>${this._t("opt.day_odd")}</option><option value="even" ${dayDp==="even"?"selected":""}>${this._t("opt.day_even")}</option><option value="every_n_days" ${isEvery?"selected":""}>${this._t("opt.day_every_n")}</option></select>
        <div class="every-n-days-opts">${isEvery?`
          <div class="fg"><label class="fl">${this._t("fld.every_n_days")}</label><input class="fi" type="text" name="every_n_days" value="${everyN}" placeholder="3"></div>
          ${this._fStartDate(startN)}`
        :""}</div>
      </div>
      <div class="fg"><label class="fl">${this._t("fld.day_specific")}</label><input class="fi" type="text" name="day_num" value="${!isEvery?dayDn:""}"></div>
      <div class="fg-title">${this._t("sec.month_filter")}</div>
      ${fPills("month",this._t("fld.months"),MONTHS,d.month??[])}
      ${this._fDate("from",this._t("fld.from"),d.from??"")}
      ${this._fDate("until",this._t("fld.until"),d.until??"")}
    </div>`;
  },

  _fAdj(d) {
    const method = d.method ?? "percentage";
    const isTime = ["actual","increase","decrease"].includes(method);
    const isEvery= !!(d.day && typeof d.day === "object" && d.day.every_n_days);
    const dayDp  = !isEvery && typeof d.day === "string" && (d.day==="odd"||d.day==="even") ? d.day : "";
    const dayDn  = !isEvery && !dayDp ? (Array.isArray(d.day)?d.day.join(", "):(d.day!=null?String(d.day):"")) : "";
    const everyN = isEvery ? String(d.day.every_n_days) : "";
    const startN = isEvery ? (d.day.start_n_days ?? "") : "";
    return `<div class="form">
      <div class="fg-title">${this._t("sec.adj_params")}</div>
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
      ${fText("load_factor",this._t("fld.load_factor"),d.load_factor!=null?String(d.load_factor):"","1")}
      <div class="fg-title">${this._t("sec.day_filter")}</div>
      ${fPills("adj_weekday",this._t("fld.adj_weekday"),WEEKDAYS,d.weekday??[])}
      <div class="fg"><label class="fl">${this._t("fld.days")}</label><select class="fi" name="day" data-default=""><option value="">${this._t("opt.day_all")}</option><option value="odd" ${dayDp==="odd"?"selected":""}>${this._t("opt.day_odd")}</option><option value="even" ${dayDp==="even"?"selected":""}>${this._t("opt.day_even")}</option><option value="every_n_days" ${isEvery?"selected":""}>${this._t("opt.day_every_n")}</option></select>
        <div class="every-n-days-opts">${isEvery?`
          <div class="fg"><label class="fl">${this._t("fld.every_n_days")}</label><input class="fi" type="text" name="every_n_days" value="${everyN}" placeholder="3"></div>
          ${this._fStartDate(startN)}`
        :""}</div>
      </div>
      <div class="fg"><label class="fl">${this._t("fld.day_specific")}</label><input class="fi" type="text" name="day_num" value="${!isEvery?dayDn:""}"></div>
      <div class="fg-title">${this._t("sec.month_filter")}</div>
      ${fPills("adj_month",this._t("fld.adj_month"),MONTHS,d.month??[])}
      ${this._fDate("from",this._t("fld.from"),d.from??"")}
      ${this._fDate("until",this._t("fld.until"),d.until??"")}
    </div>`;
  },

  _fSeq(d, eid) {
    const seqs = this._config?.controllers?.find(c => c.entry_id === eid)?.sequences ?? [];
    const seqIdx = d.id ? seqs.findIndex(s => s.id === d.id) : seqs.length;
    const seqPlaceholder = `Run ${seqIdx + 1}`;
    return `<div class="form">
      <div class="fg-title">${this._t("sec.identity")}</div>
      ${fText("name",this._t("fld.seq_name"),d.name,seqPlaceholder)}
      ${fText("sequence_id",this._t("fld.seq_id"),d.sequence_id??"",String(seqIdx+1))}
      ${fToggle("enabled",this._t("fld.enabled"),d.enabled!==false)}
      <div class="fg-title">${this._t("sec.timing")}</div>
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
      <div class="fg-title">${this._t("sec.zone")}</div>
      ${fSelect("zone_id",this._t("fld.sqz_zone"),zoneOpts,String(curZid))}
      ${fToggle("enabled",this._t("fld.enabled"),d.enabled!==false)}
      <div class="fg-title">${this._t("sec.timing")}</div>
      ${fText("duration",this._t("fld.sqz_duration"),d.duration??"","")}
      ${fText("delay",this._t("fld.sqz_delay"),d.delay??"","")}
      ${fText("repeat",this._t("fld.repeat"),d.repeat!=null?String(d.repeat):"","1")}
    </div>`;
  }

};
