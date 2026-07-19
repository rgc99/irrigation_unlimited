/**
 * General helpers: HTML escaping, time normalization, WebSocket calls,
 * formatting of weekdays/adjustments.
 */
import { DOMAIN } from "./constants.js";

export function esc(s) {
  return String(s ?? "")
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
export function normTime(v) {
  if (!v) return v;
  const p = String(v).trim().split(":");
  try {
    const [h,m,s] = p.length===1?[0,+p[0],0]:p.length===2?[+p[0],+p[1],0]:[+p[0],+p[1],+p[2]];
    const t = h*3600 + m*60 + s;
    return `${String(Math.floor(t/3600)).padStart(2,"0")}:${String(Math.floor((t%3600)/60)).padStart(2,"0")}:${String(t%60).padStart(2,"0")}`;
  } catch { return v; }
}

export function callWS(hass, type, payload = {}) {
  return hass.callWS({ type: `${DOMAIN}/${type}`, ...payload });
}
export function fmtWd(arr) {
  return arr?.length ? arr.map(d => d[0].toUpperCase() + d.slice(1,3)).join(" ") : "";
}
export function fmtAdj(a) {
  if (!a) return "";
  const {method="actual", value} = a;
  if (method==="reset")       return "reset";
  // BUG FIX: _validate() only checks the value's format when one is
  // provided, so an adjustment can be saved with a method but no value
  // (e.g. percentage with an empty field). Without this guard, the
  // template literals below produced literal "undefined%"/"+undefined"/etc.
  if (value == null || value === "") return method;
  if (method==="percentage")  return `${value>=0?"+":""}${value}%`;
  if (method==="increase")    return `+${value}`;
  if (method==="decrease")    return `−${value}`;
  if (method==="load_factor") return `×${value}`;
  return `=${value}`;
}
