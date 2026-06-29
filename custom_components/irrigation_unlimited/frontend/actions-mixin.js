/**
 * Actions mixin: event delegation (_bind/_act), CRUD (_save/_del),
 * form collection (_collect), validation (_validate), YAML export (_genYaml).
 * All CRUD calls go through callWS(...) to the WebSocket commands in
 * websocket_api.py.
 */
import { normTime, callWS } from "./lib/helpers.js";

export const actionsMixin = {

_bind(root) {
    if (this._clickH) root.removeEventListener("click", this._clickH);
    if (this._changeH) root.removeEventListener("change", this._changeH);

    this._clickH = e => {
      const pill = e.target.closest(".pill");
      if (pill) {
        const cb = pill.querySelector("input[type=checkbox]");
        if (cb) {
          cb.checked = !cb.checked;
          pill.classList.toggle("on", cb.checked);
          // Dispatch change so onchange handlers (e.g. mutual exclusion) fire
          cb.dispatchEvent(new Event("change", {bubbles: true}));
        }
        return;
      }
      const tog = e.target.closest("[data-tog]");
      if (tog && !e.target.closest("[data-a]")) {
        const id = tog.dataset.tog;
        this._expanded.has(id) ? this._expanded.delete(id) : this._expanded.add(id);
        this._draw(); return;
      }
      const btn = e.target.closest("[data-a]");
      if (btn) this._act(btn, root);
    };

    this._changeH = e => {
      if (e.target.matches("select[name=method]") && this._modal?.type==="adj") {
        const fd = this._collect(root);
        fd.method = e.target.value;
        this._modal.data = {...this._modal.data, ...fd};
        const ov = root.querySelector(".ov");
        if (ov) ov.innerHTML = this._modalHtml();
      }
    };

    root.addEventListener("click", this._clickH);
    root.addEventListener("change", this._changeH);

    // Mutual exclusion: weekday/adj_weekday pills - day select - day_num text
    // Note: month pills and from/until are mutually INCLUSIVE (they can coexist).
    // Uses event delegation so it works inside Shadow DOM and modal re-renders.
    root.addEventListener("change", e => {
      const form = e.target.closest(".form");
      if (!form) return;
      const name = e.target.getAttribute("name");
      // start_n_days: treat year/month/day as a group — any change makes all three primary
      const _snNames = ["start_n_days_year","start_n_days_month","start_n_days_day"];
      const _snDateChanged = frm => {
        const els = _snNames.map(n => frm.querySelector(`[name=${n}]`)).filter(Boolean);
        const changed = els.some(el => el.value !== (el.dataset.default??""));
        els.forEach(el => el.classList.toggle("fi-changed", changed));
      };
      if (_snNames.includes(name) && form) {
        // Explicit day change: clear clamp record
        if (name === "start_n_days_day") {
          const ds = form.querySelector("[name=start_n_days_day]");
          if (ds) delete ds.dataset.clamped;
        }
        _snDateChanged(form);
      }
      // Select color: grey at default, primary when changed (skip start_n_days handled above)
      else if (e.target.tagName === "SELECT" && e.target.dataset.default !== undefined)
        e.target.classList.toggle("fi-changed", e.target.value !== e.target.dataset.default);
      const clearPills = n => form.querySelectorAll(`[name=${n}]`).forEach(cb => {
        cb.checked = false; cb.closest(".pill")?.classList.remove("on");
      });
      if (name === "weekday" || name === "adj_weekday") {
        if ([...form.querySelectorAll(`[name=${name}]`)].some(c => c.checked)) {
          const ds = form.querySelector("[name=day]");
          if (ds) { ds.value = ""; ds.classList.toggle("fi-changed", ds.value !== (ds.dataset.default??""));  }
          const dn = form.querySelector("[name=day_num]"); if (dn) dn.value = "";
          const eo = form.querySelector(".every-n-days-opts"); if (eo) eo.innerHTML = "";
        }
      } else if (name === "day" && e.target.value) {
        clearPills("weekday"); clearPills("adj_weekday");
        const dn = form.querySelector("[name=day_num]"); if (dn) dn.value = "";
      }
      // sun select → clear time/cron; show/hide before+after offsets
      if (name === "sun" && form) {
        if (e.target.value) {
          const time = form.querySelector("[name=time]"); if (time) time.value = "";
          const cron = form.querySelector("[name=cron]"); if (cron) cron.value = "";
        }
        const offsets = form.querySelector(".sun-offsets");
        if (offsets) {
          if (e.target.value) {
            if (!offsets.querySelector("[name=before]")) {
              offsets.innerHTML =
                `<div class="fg"><label class="fl">${this._t("fld.before")}</label>` +
                `<input class="fi" type="text" name="before" value="" placeholder=""></div>` +
                `<div class="fg"><label class="fl">${this._t("fld.after")}</label>` +
                `<input class="fi" type="text" name="after"  value="" placeholder=""></div>`;
            }
          } else {
            offsets.innerHTML = "";
          }
        }
      }

      // start_n_days_year → rebuild Feb days if month is February
      if (name === "start_n_days_year" && form) {
        const moEl = form.querySelector("[name=start_n_days_month]");
        const ds   = form.querySelector("[name=start_n_days_day]");
        if (moEl && moEl.value === "02" && ds) {
          const yrN    = parseInt(e.target.value, 10);
          const isLeap = yrN ? ((yrN%4===0 && yrN%100!==0) || yrN%400===0) : true;
          const maxDay = isLeap ? 29 : 28;
          const cur    = ds.value;
          ds.innerHTML = Array.from({length:maxDay},(_,i)=>{
            const v=String(i+1).padStart(2,"0");
            return `<option value="${v}"${cur===v?" selected":""}>${i+1}</option>`;
          }).join("");
          if (!isLeap && parseInt(ds.value,10) > 28) {
            ds.dataset.clamped = ds.value; // remember pre-clamp for restoration
            ds.value = "28";
          }
        }
        _snDateChanged(form);
      }

      // start_n_days_month → rebuild start_n_days_day options (day always visible)
      if (name === "start_n_days_month" && form) {
        const SMONS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
        const ds = form.querySelector("[name=start_n_days_day]");
        if (ds && e.target.value) {
          const moName = SMONS[parseInt(e.target.value,10)-1];
          const yrEl = form.querySelector("[name=start_n_days_year]");
          const yrN  = parseInt(yrEl ? yrEl.value : 0, 10);
          const isLeap = yrN ? ((yrN%4===0 && yrN%100!==0) || yrN%400===0) : true;
          const MDAYS = {Jan:31,Feb:isLeap?29:28,Mar:31,Apr:30,May:31,Jun:30,Jul:31,Aug:31,Sep:30,Oct:31,Nov:30,Dec:31};
          const maxDay = MDAYS[moName]||31;
          // Restore pre-clamp value if valid in new month, else clamp/keep
          const clamped = ds.dataset.clamped;
          const preferred = (clamped && parseInt(clamped,10) <= maxDay) ? clamped : ds.value;
          const safeDay = parseInt(preferred,10) <= maxDay
            ? preferred : String(maxDay).padStart(2,"0");
          ds.innerHTML = Array.from({length:maxDay},(_,i)=>{
            const v=String(i+1).padStart(2,"0");
            return `<option value="${v}"${safeDay===v?" selected":""}>${i+1}</option>`;
          }).join("");
          ds.value = safeDay;
          // Clear clamp record if restored; set new one if we had to clamp
          if (clamped && parseInt(clamped,10) <= maxDay) delete ds.dataset.clamped;
          else if (parseInt(ds.value,10) >= maxDay && parseInt(preferred,10) > maxDay)
            ds.dataset.clamped = preferred;
          _snDateChanged(form);
        }
      }

      // day select → "every_n_days" → show/hide .every-n-days-opts container
      if ((name === "day" || name === "adj_day") && form) {
        const opts = form.querySelector(".every-n-days-opts");
        if (opts) {
          if (e.target.value === "every_n_days") {
            if (!opts.querySelector("[name=every_n_days]")) {
              opts.innerHTML =
                `<div class="fg"><label class="fl">${this._t("fld.every_n_days")}</label>` +
                `<input class="fi" type="text" name="every_n_days" value="" placeholder="3"></div>` +
                this._fStartDate("");
            }
          } else {
            opts.innerHTML = "";
          }
        }
      }

      // _fDate pickers: month select controls visibility of day select
      // Month -> value: add/rebuild day select (1..N, default 1, no —)
      // Month -> —   : remove day select
      if ((name === "from_month" || name === "until_month") && form) {
        const MDAYS = {Jan:31,Feb:29,Mar:31,Apr:30,May:31,Jun:30,Jul:31,Aug:31,Sep:30,Oct:31,Nov:30,Dec:31};
        const dayName = name.replace("_month", "_day");
        const wrap = e.target.parentElement;          // .iu-date-wrap
        let daySelect = form.querySelector(`[name="${dayName}"]`);
        if (!e.target.value) {
          if (daySelect) daySelect.remove();          // hide day select
        } else {
          const maxDay = MDAYS[e.target.value] || 31;
          if (!daySelect) {
            // Create day select with days 1..maxDay, default to "01"
            daySelect = document.createElement("select");
            daySelect.className = "fi"; daySelect.name = dayName;
            daySelect.style.cssText = "flex:0 0 70px";
            daySelect.dataset.default = "";  // day has no default (month must be selected first)
            daySelect.innerHTML = Array.from({length:maxDay},(_,i)=>{
              const v=String(i+1).padStart(2,"0");
              return `<option value="${v}">${i+1}</option>`;
            }).join("");
            wrap.appendChild(daySelect);
            if (daySelect && daySelect.dataset.default !== undefined) daySelect.classList.toggle("fi-changed", daySelect.value !== daySelect.dataset.default);
          } else {
            // Rebuild options for new month, preserve current day if valid
            const cur = daySelect.value;
            daySelect.innerHTML = Array.from({length:maxDay},(_,i)=>{
              const v=String(i+1).padStart(2,"0");
              return `<option value="${v}"${cur===v?" selected":""}>${i+1}</option>`;
            }).join("");
            if (daySelect && daySelect.dataset.default !== undefined) daySelect.classList.toggle("fi-changed", daySelect.value !== daySelect.dataset.default);
          }
        }
      }
    });
    root.addEventListener("input", e => {
      const name = e.target.getAttribute("name");
      const form = e.target.closest(".form");
      if (!form) return;
      if (name === "day_num") {
        if (!e.target.value.trim()) return;
        ["weekday","adj_weekday"].forEach(n =>
          form.querySelectorAll(`[name=${n}]`).forEach(cb => {
            cb.checked = false; cb.closest(".pill")?.classList.remove("on");
          })
        );
        const ds = form.querySelector("[name=day]");
        if (ds) { ds.value = ""; ds.classList.toggle("fi-changed", ds.value !== (ds.dataset.default??"")); }
        const eo = form.querySelector(".every-n-days-opts"); if (eo) eo.innerHTML = "";
      }
      // time / cron / sun mutual exclusion
      if (name === "time" && e.target.value.trim()) {
        const cron = form.querySelector("[name=cron]"); if (cron) cron.value = "";
        const sun = form.querySelector("[name=sun]");
        if (sun) { sun.value = ""; sun.classList.toggle("fi-changed", sun.value !== (sun.dataset.default??""));
          const so = form.querySelector(".sun-offsets"); if (so) so.innerHTML = ""; }
      }
      if (name === "cron" && e.target.value.trim()) {
        const time = form.querySelector("[name=time]"); if (time) time.value = "";
        const sun = form.querySelector("[name=sun]");
        if (sun) { sun.value = ""; sun.classList.toggle("fi-changed", sun.value !== (sun.dataset.default??""));
          const so = form.querySelector(".sun-offsets"); if (so) so.innerHTML = ""; }
      }
    });

    this._initEntityPickers(root);
  },

  _act(el, root) {
    const a = el.dataset.a;
    const { eid, zid, sid, aid, sqid, szid } = el.dataset;

    switch (a) {
      case "close": this._modal = null; this._draw(); break;
      case "save":  this._save(root); break;
      case "yaml":  this._genYaml(); break;

      // Global Configuration
      case "edit-global":
        this._open("global", {...(this._globalConfig||{})}, {}); break;

      // Controller CRUD
      case "add-ctrl":
        this._open("ctrl", {}, {}); break;

      case "edit-ctrl": {
        const cc = (this._config.controllers||[]).find(c=>c.entry_id===eid)||{};
        this._modal = {type:"ctrl", data:{...cc}, eid, ctrlId:eid};
        this._draw(); break;
      }

      case "del-ctrl": {
        const cname = el.dataset.name || "this controller";
        if (!confirm(this._t("confirm.del_ctrl",{name:cname}))) break;
        (async () => {
          try {
            await callWS(this._hass,"delete_controller",{ctrl_id:eid});
            await this._load();
          } catch(e) { alert(this._t("err.del")+(e.message||e)); }
        })();
        break;
      }

      // All Zones Config
      case "edit-allzones": {
        const ctrl = (this._config.controllers||[]).find(c=>c.entry_id===eid)||{};
        this._open("allzones", ctrl.all_zones_config||{}, {eid});
        break;
      }

      // Zones
      case "add-zone":
        this._open("zone",{},{eid}); break;
      case "edit-zone":
        this._open("zone",{...this._fz(eid,zid)},{eid,zoneId:zid}); break;
      case "del-zone":
        if (confirm(this._t("confirm.del_zone"))) this._del(()=>
          callWS(this._hass,"delete_zone",{entry_id:eid,zone_id:zid}),`z:${zid}`); break;

      // Zone schedules
      case "add-sched":
        this._open("sched",{},{eid,zoneId:zid}); break;
      case "edit-sched":
        this._open("sched",{...this._fs(eid,zid,sid)},{eid,zoneId:zid,schedId:sid}); break;
      case "del-sched":
        if (confirm(this._t("confirm.del_sched"))) this._del(()=>
          callWS(this._hass,"delete_schedule",{entry_id:eid,zone_id:zid,schedule_id:sid})); break;

      // Adjustments
      case "add-adj":
        this._open("adj",{},{eid,zoneId:zid}); break;
      case "edit-adj":
        this._open("adj",{...this._fa(eid,zid,aid)},{eid,zoneId:zid,adjId:aid}); break;
      case "del-adj":
        if (confirm(this._t("confirm.del_adj"))) this._del(()=>
          callWS(this._hass,"delete_adjustment",{entry_id:eid,zone_id:zid,adjustment_id:aid})); break;

      // Sequences
      case "add-seq":
        this._open("seq",{},{eid}); break;
      case "edit-seq":
        this._open("seq",{...this._fsq(eid,sqid)},{eid,seqId:sqid}); break;
      case "del-seq":
        if (confirm(this._t("confirm.del_seq"))) this._del(()=>
          callWS(this._hass,"delete_sequence",{entry_id:eid,sequence_id:sqid}),`s:${sqid}`); break;

      // Sequence zones
      case "add-sqz":
        this._open("sqz",{},{eid,seqId:sqid}); break;
      case "edit-sqz":
        this._open("sqz",{...this._fsqz(eid,sqid,szid)},{eid,seqId:sqid,szId:szid}); break;
      case "del-sqz":
        if (confirm(this._t("confirm.del_sqz"))) this._del(()=>
          callWS(this._hass,"delete_sequence_zone",{entry_id:eid,sequence_id:sqid,zone_id:szid})); break;

      // Sequence schedules
      case "add-sqsched":
        this._open("sched",{},{eid,seqId:sqid}); break;
      case "edit-sqsched":
        this._open("sched",{...this._fsqs(eid,sqid,sid)},{eid,seqId:sqid,schedId:sid}); break;
      case "del-sqsched":
        if (confirm(this._t("confirm.del_sched"))) this._del(()=>
          callWS(this._hass,"delete_sequence_schedule",{entry_id:eid,sequence_id:sqid,schedule_id:sid})); break;
    }
  },

  _open(type, data, ctx) { this._modal = {type, data, ...ctx}; this._draw(); },

  async _del(fn, expandKey) {
    try { await fn(); if (expandKey) this._expanded.delete(expandKey); await this._load(); }
    catch (e) { alert(this._t("err.del") + (e?.message ?? e)); }
  },

  _collect(root) {
    const form = root.querySelector(".form");
    if (!form) return {};
    const d = {};
    form.querySelectorAll("input[type=text]").forEach(inp => {
      if (!inp.name) return;
      const v = inp.value.trim();
      d[inp.name] = v || null;
    });
    form.querySelectorAll("input.ti[type=checkbox]").forEach(cb => {
      if (cb.name) d[cb.name] = cb.checked;
    });
    form.querySelectorAll("select").forEach(sel => {
      if (sel.name) d[sel.name] = sel.value;
    });
    // BUG FIX: previously, if the pill group existed in the form but had
    // zero checked pills (user cleared all weekdays/months), no key was
    // emitted here -- so in _save, `payload = {...m.data, ...fd}` kept the
    // OLD weekday/month array from m.data, silently undoing the user's
    // attempt to clear the filter. Now the key is always set (to [] if
    // nothing is checked) whenever the pill group is present in the form,
    // so it always overrides m.data.
    for (const [pn, key] of [["weekday","weekday"],["month","month"],
                               ["adj_weekday","weekday"],["adj_month","month"]]) {
      const group = form.querySelectorAll(`input[name="${pn}"]`);
      if (!group.length) continue;
      d[key] = [...group].filter(c=>c.checked).map(c=>c.value);
    }
    return d;
  },

  _validate(fd) {
    // fd = obiect simplu din _collect (valori string sau null)
    // Returns {errors: [...], warnings: [...]}
    // Errors block save; warnings are shown but allow save.
    const g = k => (fd[k] != null ? String(fd[k]) : "").trim();

    const rTime     = /^\d+:\d{1,2}(:\d{1,2})?$/;       // HH:MM sau HH:MM:SS
    const rNum      = /^\d+(\.\d*)?$/;                   // positive number (float ok)
    const rInt      = /^\d+$/;                             // positive integer only
    const rIuId     = /^[a-z0-9]+(_[a-z0-9]+)*$/;          // IU snake_case ID
    const rDate     = /^\d{1,2}\s+[a-zA-Z]{3}$|^\d{4}-\d{2}-\d{2}$/;
    const rDayNums  = /^\d+(,\s*\d+)*$/;                 // comma-separated integers

    const errs = [], warns = [];

    const chkTime = (k, label) => {
      const v = g(k);
      if (v && !rTime.test(v))
        errs.push(`${label}: "${v}" — expected HH:MM or HH:MM:SS`);
    };
    const chkNum = (k, label) => {
      const v = g(k);
      if (v && !rNum.test(v))
        errs.push(`${label}: "${v}" — expected a number`);
    };
    // cv.positive_int: integer >= 1
    const chkPosInt = (k, label) => {
      const v = g(k);
      if (v && (!rInt.test(v.trim()) || parseInt(v, 10) < 1))
        errs.push(`${label}: "${v}" — expected a positive integer`);
    };
    // cv.positive_float: number > 0
    const chkPosFloat = (k, label) => {
      const v = g(k);
      if (v && (!rNum.test(v) || parseFloat(v) <= 0))
        errs.push(`${label}: "${v}" — expected a positive number`);
    };
    // IU ID: optional snake_case (validated only if non-empty)
    const chkIuId = (k, label) => {
      const v = g(k);
      if (v && !rIuId.test(v))
        errs.push(this._t("err.id_format").replace("{field}", label));
    };

    for (const [k,l] of [
      ["minimum",  "Minimum"],   ["maximum",  "Maximum"],
      ["threshold","Threshold"], ["delay",    "Delay"],
      ["preamble", "Preamble"],  ["postamble","Postamble"],
      ["before",   "Before"],    ["after",    "After"],
      ["duration", "Duration"],
    ]) chkTime(k, l);

    // time (schedule): strict HH:MM:SS check
    const t = g("time");
    if (t && /^[\d:]/.test(t) && !/^([01]\d|2[0-3]):[0-5]\d:[0-5]\d$/.test(t))
      errs.push(`Time: "${t}" — expected HH:MM or HH:MM:SS`);

    // future_span: docs "Number of days to look ahead" -> positive integer
    chkNum("future_span", "Future span");
    { const v = g("future_span");
      if (v && (!rInt.test(v.trim()) || parseInt(v, 10) < 1))
        errs.push(this._t("err.future_span_int")); }

    // cv.positive_int fields
    chkPosInt("repeat",                   "Repeat");
    chkPosInt("granularity",              "Granularity");
    chkPosInt("refresh_interval",         "Refresh interval");
    chkPosInt("history_span",             "History span");
    chkPosInt("history_refresh_interval", "History refresh interval");
    chkPosInt("history_read_delay",       "History read delay");
    chkPosInt("clock_max_log_entries",    "Clock max log entries");

    // cv.positive_float fields
    chkPosFloat("load_factor", "Load factor");

    // IU ID fields: optional, snake_case if provided
    chkIuId("controller_id", "Controller ID");
    chkIuId("zone_id",       "Zone ID");
    chkIuId("schedule_id",   "Schedule ID");
    chkIuId("sequence_id",   "Sequence ID");

    // every_n_days + start_n_days: both Required in EVERY_N_DAYS_SCHEMA
    chkPosInt("every_n_days", "Every N days");
    { const en = g("every_n_days"), sny = g("start_n_days_year"), snm = g("start_n_days_month");
      if (en && (!sny || !snm)) errs.push(this._t("err.start_n_days_required")); }
    // Specific days (day_num): comma-separated integers 1-31
    { const v = g("day_num");
      if (v) {
        const parts = v.split(",").map(s => s.trim()).filter(Boolean);
        const ok = parts.length > 0 &&
                   parts.every(p => rInt.test(p) && +p >= 1 && +p <= 31);
        if (!ok) errs.push(this._t("err.day_num_format"));
      }
    }

    // Adjustment value
    const method = g("method");
    if (method) {
      const isTime = ["actual","increase","decrease"].includes(method);
      const v = g("value");
      if (v) {
        if (isTime && !rTime.test(v))
          errs.push(`Value: "${v}" — expected HH:MM or HH:MM:SS`);
        if (!isTime && method !== "reset") {
          if (!rNum.test(v) || parseFloat(v) <= 0)
            errs.push(`Value: "${v}" — expected a positive number`);
        }
      }
    }

    // from/until: vol.Inclusive — both must be set or both empty
    const fromDay = g("from_day"), fromMon = g("from_month");
    const untilDay = g("until_day"), untilMon = g("until_month");
    const fromSet = !!(fromDay && fromMon);
    const untilSet = !!(untilDay && untilMon);
    if (fromSet !== untilSet)
      errs.push(this._t("err.from_until_inclusive"));

    // Cron syntax validation (5 fields: min hour dom month dow)
    const cron = g("cron");
    if (cron) {
      const RANGES = [[0,59],[0,23],[1,31],[1,12],[0,7]];
      const parts = cron.trim().split(/\s+/);
      let cronOk = parts.length === 5;
      if (cronOk) {
        cronOk = parts.every((p, i) => {
          const [lo, hi] = RANGES[i];
          return p.split(",").every(tok => {
            if (tok === "*") return true;
            if (/^\*\/\d+$/.test(tok)) return parseInt(tok.slice(2)) > 0;
            const rs = tok.match(/^(\d+)-(\d+)(\/\d+)?$/);
            if (rs) { const a=+rs[1],b=+rs[2]; return a>=lo&&b<=hi&&a<=b; }
            const n = +tok;
            return Number.isInteger(n) && n >= lo && n <= hi;
          });
        });
      }
      if (!cronOk) {
        errs.push(this._t("err.cron_invalid"));
      } else {
        // Semantic: impossible dom+month combinations
        const MAX_DAYS = [0,31,29,31,30,31,30,31,31,30,31,30,31];
        const expand = field => {
          if (field === "*" || field.includes("/")) return null;
          const vals = [];
          for (const tok of field.split(",")) {
            const r = tok.match(/^(\d+)-(\d+)$/);
            if (r) { for (let v=+r[1]; v<=+r[2]; v++) vals.push(v); }
            else vals.push(+tok);
          }
          return vals;
        };
        const domVals = expand(parts[2]), monthVals = expand(parts[3]);
        if (domVals && monthVals) {
          if (!monthVals.some(m => domVals.some(d => d <= MAX_DAYS[m])))
            errs.push(this._t("err.cron_impossible"));
        }
        // Warning: dom + dow both non-wildcard -> OR logic
        const domIsWild = parts[2]==="*" || parts[2].startsWith("*/");
        const dowIsWild = parts[4]==="*" || parts[4].startsWith("*/");
        if (!domIsWild && !dowIsWild) warns.push(this._t("warn.cron_dom_dow_or"));
      }
    }

    return {errors: errs, warnings: warns};
  },

  async _save(root) {
    const m = this._modal;
    if (!m) return;
    const fd = this._collect(root);
    // Normalize time fields in fd BEFORE building the payload
    const _TF = new Set(["minimum","maximum","threshold","duration","delay","preamble","postamble","before","after","time"]);
    for (const _k of _TF) { if (fd[_k]) fd[_k] = normTime(fd[_k]); }

    let payload = {...m.data, ...fd};
    if (!m.data?.id) delete payload.id;

    if (payload.repeat) payload.repeat = parseInt(payload.repeat) || 1;
    // NOTE: zone_id is kept as-is (string) -- it may be a real zone_id
    // (snake_case) or the IU default index "1","2",... as a string.
    // storage.py wraps it with str()/_FL(); parseInt() here would turn
    // a custom zone_id into NaN, which the cleanup loop below would then
    // delete entirely, silently breaking the sequence-zone reference.
    if (m.type === "adj") {
      const meth = payload.method ?? "percentage";
      if (["percentage","load_factor"].includes(meth) && payload.value != null)
        payload.value = parseFloat(payload.value);
    }
    const keep = new Set(["name","entity_id","enabled","id","method"]);
    Object.keys(payload).forEach(k => {
      if (!keep.has(k) && (payload[k]===null||payload[k]==="")) delete payload[k];
    });
    // snake_case IDs: if empty, remove them explicitly (must not overwrite with null)
    ["zone_id","sequence_id","controller_id","schedule_id"].forEach(k => {
      if (!payload[k]) delete payload[k];
    });
    // Conversii de tip necesare pentru IU
    if (payload.future_span != null) payload.future_span = parseFloat(payload.future_span);
    if (payload.repeat      != null) payload.repeat      = parseInt(payload.repeat,10);
    if (payload.load_factor != null) payload.load_factor = parseFloat(payload.load_factor);

    try {
      const eid = m.eid;

      // -- Field validation ----------------------------------------------
      const {errors: valErrs, warnings: valWarns} = this._validate(fd);
      const errEl = root.getElementById("modal-err");
      const warnEl = root.getElementById("modal-warn");
      if (errEl)  errEl.textContent  = valErrs.join("\n");
      if (warnEl) warnEl.textContent = valWarns.join("\n");
      if (valErrs.length) return;

      if (m.type === "global") {
        const gcfg = {};
        const iv = k => { const v = payload[k]; return (v!=null && v!=="")?parseInt(v,10):null; };

        // General
        const gn = iv("granularity");      if (gn!=null && !isNaN(gn) && gn>0)  gcfg.granularity = gn;
        const ri = iv("refresh_interval"); if (ri!=null && !isNaN(ri) && ri>0)  gcfg.refresh_interval = ri;
        if (payload["rename_entities"] === true) gcfg.rename_entities = true;

        // History (5.8)
        const hist = {};
        if (payload["history_enabled"] === false) hist.enabled = false;
        const hs  = iv("history_span");             if (hs!=null  && !isNaN(hs)  && hs>0)  hist.span = hs;
        const hri = iv("history_refresh_interval"); if (hri!=null && !isNaN(hri) && hri>0) hist.refresh_interval = hri;
        const hrd = iv("history_read_delay");       if (hrd!=null && !isNaN(hrd) && hrd>=0) hist.read_delay = hrd;
        if (Object.keys(hist).length) gcfg.history = hist;

        // Clock (5.9)
        const clk = {};
        const cm = payload["clock_mode"]; if (cm && cm !== "seer") clk.mode = cm;
        if (payload["clock_show_log"] === true) clk.show_log = true;
        const cml = iv("clock_max_log_entries"); if (cml!=null && !isNaN(cml) && cml>0) clk.max_log_entries = cml;
        if (Object.keys(clk).length) gcfg.clock = clk;

        await callWS(this._hass,"save_global_config",{data:gcfg});
        this._modal = null; await this._load(); return;
      }

      if (m.type === "ctrl") {
        const ctrlPayload = {};
        const TIME_CTRL = new Set(["preamble","postamble"]);
        const keys = ["name","controller_id","entity_id","entity_states",
                      "enabled","queue_manual","show_sequence_status",
                      "preamble","postamble"];
        for (const k of keys) {
          if (payload[k] !== null && payload[k] !== undefined) {
            ctrlPayload[k] = TIME_CTRL.has(k) ? normTime(payload[k]) : payload[k];
          }
        }
        if (!ctrlPayload.name) {
          const errEl = root.getElementById("modal-err");
          if (errEl) errEl.textContent = this._t("err.name_req");
          return;
        }
        await callWS(this._hass,"save_controller",{
          ...(m.ctrlId ? {ctrl_id:m.ctrlId} : {}),
          data: ctrlPayload,
        });
        this._modal = null; await this._load(); return;
      }

      if (m.type === "allzones") {
        // Build all_zones_config from the form fields
        const azc = {};
        const g = k => (fd[k] != null ? String(fd[k]) : "").trim();
        const TIME_AZ = new Set(["duration","minimum","maximum","threshold"]);
        const setV = (k) => { const v=g(k); if (v) azc[k] = TIME_AZ.has(k)?normTime(v):v; };
        setV("duration"); setV("minimum"); setV("maximum"); setV("threshold");
        const fs = parseFloat(g("future_span"));
        if (!isNaN(fs)) azc.future_span = fs;
        azc.allow_manual = fd["allow_manual"] === true;
        const es = g("entity_states");
        if (es && es !== "all") azc.entity_states = es;
        const show = {};
        if (fd["show_timeline"] === true) show.timeline = true;
        if (fd["show_config"]   === true) show.config   = true;
        if (Object.keys(show).length) azc.show = show;
        await callWS(this._hass,"save_all_zones_config",{entry_id:eid,data:azc});
        this._modal = null; await this._load(); return;
      }

      switch (m.type) {
        case "zone": {
          // Build explicitly -- not using the generic payload, collect field-by-field from fd
          const g  = k => (fd[k] != null ? String(fd[k]) : "").trim();
          const gb = k => fd[k] === true;
          const zone = {};
          // Keep the id and schedules/adjustments from m.data
          if (m.data?.id) zone.id = m.data.id;
          if (m.data?.schedules)    zone.schedules    = m.data.schedules;
          if (m.data?.adjustments)  zone.adjustments  = m.data.adjustments;
          // Text fields -- include only if filled in
          const TIME_ZONE = new Set(["minimum","maximum","threshold","duration"]);
          const strKeys = ["name","zone_id","entity_id","minimum","maximum",
                           "threshold","duration"];
          for (const k of strKeys) {
            const v=g(k); if (v) zone[k] = TIME_ZONE.has(k) ? normTime(v) : v;
          }
          // entity_states -- include only if not default "all"
          const es = g("entity_states");
          if (es && es !== "all") zone.entity_states = es;
          // future_span -- number, include if filled in
          const fs = g("future_span");
          if (fs) { const n=parseFloat(fs); if (!isNaN(n)) zone.future_span=n; }
          // Booleans -- always include
          zone.enabled      = fd["enabled"]      !== false;
          zone.allow_manual = gb("allow_manual");
          // show — obiect nested
          const show = {};
          if (gb("show_timeline")) show.timeline = true;
          if (gb("show_config"))   show.config   = true;
          if (Object.keys(show).length) zone.show = show;
          await callWS(this._hass,"save_zone",{entry_id:eid,zone});
          break;
        }
        case "sched": {
          // Normalize time fields before saving
          for (const k of ["duration","delay","minimum"]) {
            if (payload[k]) payload[k] = normTime(payload[k]);
          }
          // Combine day select (odd/even) + day_num text (specific numbers)
          { const dn=(payload.day_num||"").trim(), dp=(payload.day||"").trim();
            delete payload.day_num; delete payload.day;
            if (dn) {
              const nums=dn.split(",").map(s=>parseInt(s.trim())).filter(n=>!isNaN(n)&&n>=1&&n<=31);
              if (nums.length===1) payload.day=nums[0];
              else if (nums.length>1) payload.day=nums;
            } else if (dp) { payload.day=dp; }
          }
          // Sun event: combine sun + before + after into payload.time object
          { const sun=(payload.sun||"").trim(), bef=(payload.before||"").trim(), aft=(payload.after||"").trim();
            delete payload.sun; delete payload.before; delete payload.after;
            if (sun) {
              const sunObj = {sun};
              if (bef) sunObj.before = bef;
              if (aft) sunObj.after  = aft;
              payload.time = sunObj;
            }
          }
          // Combine from_day + from_month -> "dd Mon", same for until
          { const fd=payload.from_day||"", fm=payload.from_month||"";
            delete payload.from_day; delete payload.from_month;
            if (fd && fm) payload.from = `${fd} ${fm}`; else delete payload.from;
          }
          { const ud=payload.until_day||"", um=payload.until_month||"";
            delete payload.until_day; delete payload.until_month;
            if (ud && um) payload.until = `${ud} ${um}`; else delete payload.until;
          }
          if (m.seqId)
            await callWS(this._hass,"save_sequence_schedule",{entry_id:eid,sequence_id:m.seqId,schedule:payload});
          else
            await callWS(this._hass,"save_schedule",{entry_id:eid,zone_id:m.zoneId,schedule:payload});
          break;
        }
        case "adj": {
          // Combine day select (odd/even/every_n_days) + day_num + every_n_days fields
          { const dn=(payload.day_num||"").trim(), dp=(payload.day||"").trim();
            const en=(payload.every_n_days||"").trim();
            const sny=(payload.start_n_days_year||"").trim();
            const snm=(payload.start_n_days_month||"").trim();
            const snd=(payload.start_n_days_day||"01").trim();
            delete payload.day_num; delete payload.day;
            delete payload.every_n_days;
            delete payload.start_n_days_year; delete payload.start_n_days_month; delete payload.start_n_days_day;
            if (dp === "every_n_days" && en) {
              const obj = {every_n_days: parseInt(en, 10)};
              if (sny && snm) obj.start_n_days = `${sny}-${snm}-${snd}`;
              payload.day = obj;
            } else if (dn) {
              const nums=dn.split(",").map(s=>parseInt(s.trim())).filter(n=>!isNaN(n)&&n>=1&&n<=31);
              if (nums.length===1) payload.day=nums[0];
              else if (nums.length>1) payload.day=nums;
            } else if (dp && dp !== "every_n_days") { payload.day=dp; }
          }
          // Combine from_day + from_month -> "dd Mon", same for until
          { const fd=payload.from_day||"", fm=payload.from_month||"";
            delete payload.from_day; delete payload.from_month;
            if (fd && fm) payload.from = `${fd} ${fm}`; else delete payload.from;
          }
          { const ud=payload.until_day||"", um=payload.until_month||"";
            delete payload.until_day; delete payload.until_month;
            if (ud && um) payload.until = `${ud} ${um}`; else delete payload.until;
          }
          await callWS(this._hass,"save_adjustment",{entry_id:eid,zone_id:m.zoneId,adjustment:payload}); break;
        }
        case "seq": {
          const g  = k => (fd[k] != null ? String(fd[k]) : "").trim();
          const seq = {};
          if (m.data?.id) seq.id = m.data.id;
          if (m.data?.zones)     seq.zones     = m.data.zones;
          if (m.data?.schedules) seq.schedules = m.data.schedules;
          const TIME_SEQ = new Set(["delay","duration"]);
          const seqStrKeys = ["name","sequence_id","delay","duration"];
          for (const k of seqStrKeys) {
            const v=g(k); if (v) seq[k] = TIME_SEQ.has(k) ? normTime(v) : v;
          }
          seq.enabled = fd["enabled"] !== false;
          const rpt = g("repeat");
          if (rpt) { const n=parseInt(rpt,10); if (!isNaN(n)&&n>0) seq.repeat=n; }
          await callWS(this._hass,"save_sequence",{entry_id:eid,sequence:seq});
          break;
        }
        case "sqz": {
          for (const k of ["duration","delay"]) {
            if (payload[k]) payload[k] = normTime(payload[k]);
          }
          await callWS(this._hass,"save_sequence_zone",{entry_id:eid,sequence_id:m.seqId,zone:payload});
          break;
        }
      }
      this._modal = null;
      await this._load();
    } catch (e) { alert(this._t("err.save") + (e?.message ?? e)); }
  },

  async _genYaml() {
    try {
      const r = await callWS(this._hass,"generate_yaml",{});
      this._open("yaml", r.yaml, {});
    } catch (e) { alert(this._t("err.yaml") + (e?.message ?? e)); }
  }

};
