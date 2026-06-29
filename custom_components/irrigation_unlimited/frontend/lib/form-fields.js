/**
 * HTML builders for form fields (text, toggle, select, pills, entity picker).
 */
import { esc } from "./helpers.js";
import { _tr } from "./translations.js";

export function fText(name, label, value="", hint="") {
  return `<div class="fg">
    <label class="fl">${label}</label>
    <input class="fi" type="text" name="${name}" value="${esc(value)}"${hint?` placeholder="${esc(hint)}"`:""}>
  </div>`;
}
export function fToggle(name, label, checked=true) {
  return `<div class="fg"><div class="tw">
    <span class="tl">${label}</span>
    <label class="tg"><input class="ti" type="checkbox" name="${name}" data-default="${checked}"${checked?" checked":""}><span class="ts"></span></label>
  </div></div>`;
}
export function fSelect(name, label, options, value) {
  return `<div class="fg">
    <label class="fl">${label}</label>
    <select class="fi" name="${name}" data-default="${esc(String(value??""))}">
      ${options.map(o=>`<option value="${esc(o.value)}"${o.value===String(value??"")?` selected`:""}>${esc(o.label)}</option>`).join("")}
    </select>
  </div>`;
}
export function fPills(name, label, options, selected=[], onchange="") {
  const oc = onchange ? ` onchange="${onchange}"` : "";
  return `<div class="fg">
    <label class="fl">${label}</label>
    <div class="pg">${options.map(o=>`
      <label class="pill${selected.includes(o.key)?" on":""}">
        <input type="checkbox" name="${name}" value="${o.key}"${selected.includes(o.key)?" checked":""}${oc} hidden>
        ${o.label}</label>`).join("")}
    </div>
  </div>`;
}
export function fSec(t) { return `<div class="fsec">${t}</div>`; }

export function fEntityPicker(name, label, value="") {
  return `<div class="fg">
    <label class="fl">${label}</label>
    <div class="epw">
      <input class="fi ep-inp" type="text" name="${name}"
             value="${esc(value)}" placeholder="${esc(_tr("fld.entity_picker_placeholder"))}" autocomplete="off">
      <div class="ep-dd" style="display:none"></div>
    </div>
  </div>`;
}

