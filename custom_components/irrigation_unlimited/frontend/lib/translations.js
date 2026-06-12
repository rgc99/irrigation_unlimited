/**
 * Translation system: loads en.json (fallback) + the current HA language.
 */

export const _str = { en: {}, current: {} };

export async function _fetchLang(lang) {
  try {
    const r = await fetch("/irrigation_unlimited_static/translations/" + lang + ".json");
    if (r.ok) return await r.json();
  } catch (_) {}
  return null;
}

export function _tr(key, vars = {}) {
  let s = (_str.current[key] ?? _str.en[key]) ?? key;
  for (const [k, v] of Object.entries(vars)) s = s.replace("{" + k + "}", v);
  return s;
}
