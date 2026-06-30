"""WebSocket API for the Irrigation Unlimited panel.

Provides the WebSocket commands consumed by the custom frontend panel
(frontend/irrigation-unlimited-panel.js) for all CRUD operations that
upstream master performed via the config-entry options flow / subentry flow:

  - {DOMAIN}/config                 -> ws_get_config
        Returns all controllers (+ global config) from IUStore. On first
        load for a freshly migrated controller (no zones/sequences yet),
        auto-imports them from hass.data[DOMAIN]["coord_src_<ctrl_id>"]
        (the matching YAML controller, see __init__.async_setup_entry).
  - {DOMAIN}/save_global_config      -> section 5 top-level config
  - {DOMAIN}/save_controller,
    {DOMAIN}/delete_controller       -> controller CRUD (5.1)
  - {DOMAIN}/save_all_zones_config   -> all-zones defaults (5.2)
  - {DOMAIN}/save_zone, delete_zone  -> zone CRUD (5.3)
  - {DOMAIN}/save_schedule, delete_schedule       -> zone schedules (5.5)
  - {DOMAIN}/save_adjustment, delete_adjustment   -> zone adjustments
  - {DOMAIN}/save_sequence, delete_sequence       -> sequence CRUD (5.6)
  - {DOMAIN}/save_sequence_zone, delete_sequence_zone           -> 5.7
  - {DOMAIN}/save_sequence_schedule, delete_sequence_schedule
  - {DOMAIN}/generate_yaml           -> full IU YAML (IUStore.generate_yaml)

Every save/delete command schedules a debounced (4s) reload of the main
config entry via _schedule_reload, so the IU coordinator picks up the new
configuration without restarting Home Assistant.
--------------------------------------------------------------------------------
"""
from __future__ import annotations

import asyncio
import datetime as _dt
import logging

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .storage import IUStore

_LOGGER = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _store(hass: HomeAssistant) -> IUStore:
    s = hass.data.get(DOMAIN, {}).get("store")
    if s is None:
        raise RuntimeError("IU panel store unavailable (integration reloading)")
    return s


# ── Debounced per-entry reload ─────────────────────────────────────────────────

@callback
def _schedule_reload(hass: HomeAssistant, entry_id: str) -> None:
    key = f"_rl_{entry_id}"
    d = hass.data.setdefault(DOMAIN, {})
    old: asyncio.Task | None = d.get(key)
    if old and not old.done():
        old.cancel()

    async def _run() -> None:
        try:
            await asyncio.sleep(4)
            dd = hass.data.get(DOMAIN)
            if dd is None or dd.get("_rl_busy"):
                return
            # Reload the MAIN config entry (which rebuilds all subentry coordinators)
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                return
            store = dd.get("store")
            if store is None:
                return
            dd["_rl_busy"] = True
            _LOGGER.debug("IU panel: auto-reload after change to subentry %s", entry_id[:8])
            await hass.config_entries.async_reload(entries[0].entry_id)
        except asyncio.CancelledError:
            pass
        except Exception:
            _LOGGER.exception("IU panel auto-reload failed")
        finally:
            dd2 = hass.data.get(DOMAIN)
            if dd2:
                dd2.pop("_rl_busy", None)
                dd2.pop(key, None)

    d[key] = hass.async_create_task(_run(), name=f"iu_reload_{entry_id[:8]}")


# ── Import helpers ─────────────────────────────────────────────────────────────

def _td(v):
    if v is None: return None
    if isinstance(v, str): return v
    if isinstance(v, _dt.timedelta):
        t = int(abs(v.total_seconds())); h,r = divmod(t,3600)
        return f"{h:02d}:{r//60:02d}"
    return str(v)

def _tm(v):
    if v is None: return None
    if isinstance(v, str): return v
    if isinstance(v, _dt.time): return v.strftime("%H:%M")
    return str(v)

def _dts(v):
    if v is None: return None
    if isinstance(v, str): return v
    if isinstance(v, (_dt.date,_dt.datetime)): return v.strftime("%Y-%m-%d")
    return str(v)

def _wd(v):
    if not v: return None
    days=["mon","tue","wed","thu","fri","sat","sun"]
    r=[]
    for d in (v if isinstance(v,list) else [v]):
        if isinstance(d,int) and 0<=d<=6: r.append(days[d])
        elif isinstance(d,str): r.append(d.lower()[:3])
    return r or None

def _mo(v):
    if not v: return None
    return list(v) if isinstance(v,(list,tuple)) else [str(v)]

def _isched(s, sid):
    o={"id":sid}
    for k in ("name","enabled","anchor","cron"):
        if s.get(k) is not None: o[k]=s[k]
    for k,fn in (("time",_tm),("duration",_td),("delay",_td)):
        if r:=fn(s.get(k)): o[k]=r
    for k,fn in (("from",_dts),("until",_dts)):
        if r:=fn(s.get(k)): o[k]=r
    if w:=_wd(s.get("weekday")): o["weekday"]=w
    if m:=_mo(s.get("month")): o["month"]=m
    if s.get("day") is not None: o["day"]=str(s["day"])
    return o

def _iadj(a, aid):
    methods=["actual","percentage","increase","decrease","reset","load_factor"]
    method=next((m for m in methods if m in a),"actual")
    o={"id":aid,"method":method}
    if method!="reset":
        raw=a.get(method); o["value"]=_td(raw) if isinstance(raw,_dt.timedelta) else raw
    for k in ("minimum","maximum"):
        if a.get(k) is not None: o[k]=_td(a[k])
    if a.get("load_factor") is not None: o["load_factor"]=a["load_factor"]
    if w:=_wd(a.get("weekday")): o["weekday"]=w
    if m:=_mo(a.get("month")): o["month"]=m
    for k in ("from","until"):
        if a.get(k): o[k]=_dts(a[k])
    if a.get("day") is not None: o["day"]=str(a["day"])
    return o

async def _auto_import(store: IUStore, eid: str, ctrl_src: dict) -> None:
    uid = store._new_id
    zones = [
        { "id":uid(),"name":z.get("name",""),"enabled":z.get("enabled",True),
          "entity_id":z.get("entity_id"),"allow_manual":z.get("allow_manual",True),
          "show_log":z.get("show_log",False),"minimum":_td(z.get("minimum")),
          "maximum":_td(z.get("maximum")),"future_span":z.get("future_span"),
          "schedules":[_isched(s,uid()) for s in z.get("schedules",[])],
          "adjustments":[_iadj(a,uid()) for a in z.get("adjustments",[])],
        } for z in ctrl_src.get("zones",[])
    ]
    seqs = []
    for sq in ctrl_src.get("sequences",[]):
        s={"id":uid(),"name":sq.get("name",""),"enabled":sq.get("enabled",True),
           "delay":_td(sq.get("delay")),"duration":_td(sq.get("duration")),
           "repeat":sq.get("repeat",1),"show_log":sq.get("show_log",False),
           "schedules":[_isched(sc,uid()) for sc in sq.get("schedules",[])],
           "zones":[
               {"id":uid(),"zone_id":sz.get("zone_id",1),"enabled":sz.get("enabled",True),
                "duration":_td(sz.get("duration")),"delay":_td(sz.get("delay")),
                "repeat":sz.get("repeat",1)}
               for sz in sq.get("zones",[])
           ]}
        seqs.append(s)
    store._data[eid] = {"zones": zones, "sequences": seqs}
    await store._save()


# ── Config read ────────────────────────────────────────────────────────────────

@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/config"})
@websocket_api.async_response
async def ws_get_config(hass, connection, msg):
    store = _store(hass)
    dd = hass.data.get(DOMAIN, {})

    controllers = []
    for cid, basics in store.get_controller_list():
        ed = store.get_entry_data(cid)
        if not ed.get("zones") and not ed.get("sequences"):
            src = dd.get(f"coord_src_{cid}", {})
            if src.get("zones") or src.get("sequences"):
                _LOGGER.info("IU panel: auto-import for %s", cid[:8])
                await _auto_import(store, cid, src)
                ed = store.get_entry_data(cid)
        controllers.append({
            "entry_id": cid,
            **{k: v for k, v in basics.items() if v not in (None, "")},
            "zones":            ed.get("zones", []),
            "sequences":        ed.get("sequences", []),
            "all_zones_config": ed.get("all_zones_config", {}),
        })
    global_config = store.get_global_config()
    connection.send_result(msg["id"], {"controllers": controllers, "global_config": global_config})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_zone",
    vol.Required("entry_id"): str,
    vol.Required("zone"): dict,
})
@websocket_api.async_response
async def ws_save_zone(hass, connection, msg):
    r = await _store(hass).save_zone(msg["entry_id"], msg["zone"])
    _schedule_reload(hass, msg["entry_id"])
    connection.send_result(msg["id"], {"zone": r})

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_zone",
    vol.Required("entry_id"): str,
    vol.Required("zone_id"): str,
})
@websocket_api.async_response
async def ws_delete_zone(hass, connection, msg):
    ok = await _store(hass).delete_zone(msg["entry_id"], msg["zone_id"])
    _schedule_reload(hass, msg["entry_id"])
    connection.send_result(msg["id"], {"success": ok})


# ── Zone Schedules ─────────────────────────────────────────────────────────────

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_schedule",
    vol.Required("entry_id"): str, vol.Required("zone_id"): str, vol.Required("schedule"): dict,
})
@websocket_api.async_response
async def ws_save_schedule(hass, connection, msg):
    r = await _store(hass).save_schedule(msg["entry_id"], msg["zone_id"], msg["schedule"])
    _schedule_reload(hass, msg["entry_id"])
    connection.send_result(msg["id"], {"schedule": r})

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_schedule",
    vol.Required("entry_id"): str, vol.Required("zone_id"): str, vol.Required("schedule_id"): str,
})
@websocket_api.async_response
async def ws_delete_schedule(hass, connection, msg):
    ok = await _store(hass).delete_schedule(msg["entry_id"], msg["zone_id"], msg["schedule_id"])
    _schedule_reload(hass, msg["entry_id"])
    connection.send_result(msg["id"], {"success": ok})


# ── Adjustments ────────────────────────────────────────────────────────────────

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_adjustment",
    vol.Required("entry_id"): str, vol.Required("zone_id"): str, vol.Required("adjustment"): dict,
})
@websocket_api.async_response
async def ws_save_adjustment(hass, connection, msg):
    r = await _store(hass).save_adjustment(msg["entry_id"], msg["zone_id"], msg["adjustment"])
    _schedule_reload(hass, msg["entry_id"])
    connection.send_result(msg["id"], {"adjustment": r})

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_adjustment",
    vol.Required("entry_id"): str, vol.Required("zone_id"): str, vol.Required("adjustment_id"): str,
})
@websocket_api.async_response
async def ws_delete_adjustment(hass, connection, msg):
    ok = await _store(hass).delete_adjustment(msg["entry_id"], msg["zone_id"], msg["adjustment_id"])
    _schedule_reload(hass, msg["entry_id"])
    connection.send_result(msg["id"], {"success": ok})


# ── Sequences ──────────────────────────────────────────────────────────────────

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_sequence",
    vol.Required("entry_id"): str, vol.Required("sequence"): dict,
})
@websocket_api.async_response
async def ws_save_sequence(hass, connection, msg):
    r = await _store(hass).save_sequence(msg["entry_id"], msg["sequence"])
    _schedule_reload(hass, msg["entry_id"])
    connection.send_result(msg["id"], {"sequence": r})

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_sequence",
    vol.Required("entry_id"): str, vol.Required("sequence_id"): str,
})
@websocket_api.async_response
async def ws_delete_sequence(hass, connection, msg):
    ok = await _store(hass).delete_sequence(msg["entry_id"], msg["sequence_id"])
    _schedule_reload(hass, msg["entry_id"])
    connection.send_result(msg["id"], {"success": ok})


# ── Sequence Zones ─────────────────────────────────────────────────────────────

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_sequence_zone",
    vol.Required("entry_id"): str, vol.Required("sequence_id"): str, vol.Required("zone"): dict,
})
@websocket_api.async_response
async def ws_save_sequence_zone(hass, connection, msg):
    r = await _store(hass).save_sequence_zone(msg["entry_id"], msg["sequence_id"], msg["zone"])
    _schedule_reload(hass, msg["entry_id"])
    connection.send_result(msg["id"], {"zone": r})

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_sequence_zone",
    vol.Required("entry_id"): str, vol.Required("sequence_id"): str, vol.Required("zone_id"): str,
})
@websocket_api.async_response
async def ws_delete_sequence_zone(hass, connection, msg):
    ok = await _store(hass).delete_sequence_zone(msg["entry_id"], msg["sequence_id"], msg["zone_id"])
    _schedule_reload(hass, msg["entry_id"])
    connection.send_result(msg["id"], {"success": ok})


# ── Sequence Schedules ─────────────────────────────────────────────────────────

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_sequence_schedule",
    vol.Required("entry_id"): str, vol.Required("sequence_id"): str, vol.Required("schedule"): dict,
})
@websocket_api.async_response
async def ws_save_sequence_schedule(hass, connection, msg):
    r = await _store(hass).save_sequence_schedule(msg["entry_id"], msg["sequence_id"], msg["schedule"])
    _schedule_reload(hass, msg["entry_id"])
    connection.send_result(msg["id"], {"schedule": r})

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_sequence_schedule",
    vol.Required("entry_id"): str, vol.Required("sequence_id"): str, vol.Required("schedule_id"): str,
})
@websocket_api.async_response
async def ws_delete_sequence_schedule(hass, connection, msg):
    ok = await _store(hass).delete_sequence_schedule(msg["entry_id"], msg["sequence_id"], msg["schedule_id"])
    _schedule_reload(hass, msg["entry_id"])
    connection.send_result(msg["id"], {"success": ok})


# ── YAML ───────────────────────────────────────────────────────────────────────

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/generate_yaml",
})
@websocket_api.async_response
async def ws_generate_yaml(hass, connection, msg):
    """Generate full IU YAML: global config + all controllers."""
    yaml_str = _store(hass).generate_yaml()
    connection.send_result(msg["id"], {"yaml": yaml_str})


# ── Registration ───────────────────────────────────────────────────────────────

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_all_zones_config",
    vol.Required("entry_id"): str,
    vol.Required("data"): dict,
})
@websocket_api.async_response
async def ws_save_all_zones_config(hass, connection, msg):
    """Save all_zones_config (5.2 All Zone Objects) for a controller."""
    store = _store(hass)
    eid = msg["entry_id"]
    result = await store.save_all_zones_config(eid, msg["data"])
    _schedule_reload(hass, eid)
    connection.send_result(msg["id"], {"all_zones_config": result})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_global_config",
    vol.Required("data"): dict,
})
@websocket_api.async_response
async def ws_save_global_config(hass, connection, msg):
    """Save top-level IU configuration (section 5)."""
    store = _store(hass)
    result = await store.save_global_config(msg["data"])
    _schedule_reload(hass, "global")
    connection.send_result(msg["id"], {"global_config": result})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_controller",
    vol.Optional("ctrl_id"): str,
    vol.Required("data"): dict,
})
@websocket_api.async_response
async def ws_save_controller(hass, connection, msg):
    """Create (no ctrl_id) or update (with ctrl_id) a controller from the panel."""
    store = _store(hass)
    ctrl_id, basics = await store.save_controller(msg.get("ctrl_id"), msg["data"])
    _schedule_reload(hass, ctrl_id)
    connection.send_result(msg["id"], {"ctrl_id": ctrl_id, "data": basics})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_controller",
    vol.Required("ctrl_id"): str,
})
@websocket_api.async_response
async def ws_delete_controller(hass, connection, msg):
    """Delete a controller and all its panel data."""
    store = _store(hass)
    await store.delete_controller(msg["ctrl_id"])
    _schedule_reload(hass, msg["ctrl_id"])
    connection.send_result(msg["id"], {"deleted": True})


def async_register_commands(hass: HomeAssistant) -> None:
    for h in [
        ws_get_config,
        ws_save_global_config,
        ws_save_controller,    ws_delete_controller,
        ws_save_all_zones_config,
        ws_save_zone,       ws_delete_zone,
        ws_save_schedule,   ws_delete_schedule,
        ws_save_adjustment, ws_delete_adjustment,
        ws_save_sequence,   ws_delete_sequence,
        ws_save_sequence_zone,     ws_delete_sequence_zone,
        ws_save_sequence_schedule, ws_delete_sequence_schedule,
        ws_generate_yaml,
    ]:
        websocket_api.async_register_command(hass, h)
