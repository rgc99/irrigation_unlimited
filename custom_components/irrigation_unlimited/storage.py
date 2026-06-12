"""Irrigation Unlimited panel storage.

This module is the persistent, panel-managed source of truth for controller
configuration, replacing upstream's config-entry-driven setup (single
controller in entry.data, or multiple controllers via HA-native subentries).

IUStore wraps a single Store(STORAGE_VERSION, STORAGE_KEY) file and provides:
  - Controller CRUD (save_controller / delete_controller / get_controller_list)
  - Zone / Sequence / Schedule / Adjustment / Sequence-Zone /
    Sequence-Schedule CRUD, used by the WebSocket API (websocket_api.py) on
    behalf of the custom frontend panel
  - All-Zones-Config and global IU config (section 5: granularity,
    refresh_interval, rename_entities, history, clock) CRUD
  - Conversion helpers (to_iu_config_multi / generate_yaml) that build the
    full multi-controller IU configuration dict (and equivalent YAML) from
    panel storage, applying:
      * IU-schema defaults dropping (so untouched fields are omitted, e.g.
        enabled=true, allow_manual=false, future_span=3, anchor="start", ...)
      * HH:MM / HH:MM:SS time normalization (_norm_time)
      * future_span as int (not float) in the generated config
      * entity_id wrapped as a list (IU iterates entity_id as a list)
      * weekday/month/zone_id rendered as YAML flow-style lists (_FL)

Schema (per-entry, keyed by panel controller ID "ctrl_xxxxxxxxxxxxx"):
  {
    "<ctrl_id>": {
      "name": ..., "entity_id": ..., "controller_id": ..., ... (CTRL_KEYS)
      "zones":     [ { id, name, entity_id, ... } ],
      "sequences": [ { id, name, ..., zones, schedules } ],
      "all_zones_config": { ... }
    },
    "__global__": { granularity, refresh_interval, rename_entities,
                     history: {...}, clock: {...} },
    ...
  }

Migration from old flat format {"zones": [...], "sequences": [...]} is handled
automatically in async_load when it detects the old layout.
--------------------------------------------------------------------------------
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)
STORAGE_KEY = "irrigation_unlimited_panel"
STORAGE_VERSION = 1


class _FL(list):
    """YAML flow-style list: [mon, wed, sat]"""


class IUStore:

    def __init__(self, hass: HomeAssistant) -> None:
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = {}   # keyed by entry_id

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def async_load(self) -> None:
        raw = await self._store.async_load()
        if not raw:
            return
        # Migration: old flat format {"zones": [...]} or {"controllers": [...]}
        if "zones" in raw or "sequences" in raw or "controllers" in raw:
            _LOGGER.warning("IU panel: migrating storage to multi-controller format")
            if "controllers" in raw:
                first = raw["controllers"][0] if raw["controllers"] else {}
                zones = first.get("zones", [])
                seqs  = first.get("sequences", [])
            else:
                zones = raw.get("zones", [])
                seqs  = raw.get("sequences", [])
            # We don't know the entry_id here; store under a placeholder.
            # async_setup_entry will re-key it when it knows its entry_id.
            self._data = {"__migrated__": {"zones": zones, "sequences": seqs}}
            await self._save()
            return
        self._data = raw

    async def _save(self) -> None:
        await self._store.async_save(self._data)

    # ── Per-entry access ──────────────────────────────────────────────────────

    def ensure_entry(self, entry_id: str) -> None:
        """Create empty slot for entry if not present (including migration)."""
        if "__migrated__" in self._data and entry_id not in self._data:
            # Re-key the migrated data under the real entry_id
            self._data[entry_id] = self._data.pop("__migrated__")
        self._data.setdefault(entry_id, {"zones": [], "sequences": [], "all_zones_config": {}})
        self._data[entry_id].setdefault("all_zones_config", {})

    def get_entry_data(self, entry_id: str) -> dict:
        return self._data.get(entry_id, {"zones": [], "sequences": []})

    def get_all_config(self) -> dict:
        """Return full storage (all entries)."""
        return dict(self._data)

    async def delete_entry(self, entry_id: str) -> None:
        """Remove all zones/sequences for a deleted config entry."""
        self._data.pop(entry_id, None)
        self._data.pop("__migrated__", None)
        await self._save()

    # ── IU config builder ─────────────────────────────────────────────────────

    def to_iu_config(self, entry_id: str, ctrl_basics: dict) -> dict:
        """Build full IU config dict for one controller."""
        ed = self.get_entry_data(entry_id)
        ctrl = {k: v for k, v in ctrl_basics.items() if v not in (None, "")}
        ctrl["zones"]     = self._build_zones(ed.get("zones", []))
        ctrl["sequences"] = self._build_sequences(ed.get("sequences", []))
        return {"controllers": [ctrl]}

    def to_iu_config_multi(self, subentries: list[tuple[str, dict]]) -> dict:
        """Build IU config with multiple controllers from subentries list."""
        controllers = []
        for sid, ctrl_basics in subentries:
            ctrl = {k: v for k, v in ctrl_basics.items() if v not in (None, "")}
            if "entity_id" in ctrl:
                ctrl["entity_id"] = [ctrl["entity_id"]]
            for k in ("preamble","postamble"):
                if ctrl.get(k) not in (None, ""):
                    ctrl[k] = IUStore._norm_time(ctrl[k])
            IUStore._drop_defaults(ctrl, IUStore.CTRL_DEFAULTS)
            ed = self.get_entry_data(sid)
            ctrl["zones"]     = self._build_zones(ed.get("zones", []))
            ctrl["sequences"] = self._build_sequences(ed.get("sequences", []))
            azc = IUStore._build_all_zones_config(ed.get("all_zones_config", {}))
            if azc:
                ctrl["all_zones_config"] = azc
            controllers.append(ctrl)
        # Add global settings (granularity, refresh_interval, rename_entities)
        result: dict = {"controllers": controllers}
        gcfg = dict(self.get_global_config())
        if "history" in gcfg and isinstance(gcfg["history"], dict):
            hist = {k: v for k, v in gcfg["history"].items() if v not in (None, "")}
            IUStore._drop_defaults(hist, IUStore.HISTORY_DEFAULTS)
            if hist: gcfg["history"] = hist
            else: del gcfg["history"]
        if "clock" in gcfg and isinstance(gcfg["clock"], dict):
            clk = {k: v for k, v in gcfg["clock"].items() if v not in (None, "")}
            IUStore._drop_defaults(clk, IUStore.CLOCK_DEFAULTS)
            if clk: gcfg["clock"] = clk
            else: del gcfg["clock"]
        IUStore._drop_defaults(gcfg, IUStore.GLOBAL_DEFAULTS)
        for k, v in gcfg.items():
            if v not in (None, ""):
                result[k] = v
        return result

    def generate_yaml(self) -> str:
        """Generate full IU YAML: global config + all controllers."""
        import yaml  # pylint: disable=import-outside-toplevel

        def _fl_repr(dumper, data):
            return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)

        yaml.add_representer(_FL, _fl_repr)

        iu_config = self.to_iu_config_multi(self.get_controller_list())
        return yaml.dump(
            {"irrigation_unlimited": iu_config},
            default_flow_style=False, allow_unicode=True, sort_keys=False,
        )

    # ── Zone builders ─────────────────────────────────────────────────────────

    @staticmethod
    def _build_all_zones_config(azc: dict) -> dict | None:
        """Build all_zones_config dict for IU coordinator (5.2 All Zone Objects)."""
        if not azc:
            return None
        obj: dict = {}
        TIME_KEYS_AZC = {"minimum","maximum","threshold","duration"}  # ALL_ZONES_SCHEMA nu are "delay"
        for k in ("minimum","maximum","threshold","duration","entity_states"):
            v = azc.get(k)
            if v in (None, ""): continue
            obj[k] = IUStore._norm_time(v) if k in TIME_KEYS_AZC else v
        fs = azc.get("future_span")
        if fs not in (None, ""):
            obj["future_span"] = int(float(fs))
        if azc.get("allow_manual"):
            obj["allow_manual"] = True
        # show e stocat ca {"show": {"timeline": true, "config": true}}
        show_obj = azc.get("show") or {}
        show: dict = {}
        if show_obj.get("timeline"):
            show["timeline"] = True
        if show_obj.get("config"):
            show["config"] = True
        if show:
            obj["show"] = show
        # entity_states "all" = default, future_span 3 = default
        IUStore._drop_defaults(obj, {"entity_states": "all", "future_span": 3})
        return obj if obj else None

    @staticmethod
    def _norm_time(v) -> str | None:
        """Normalize any valid time period to HH:MM:SS."""
        if v is None or str(v).strip() == "":
            return None
        parts = str(v).strip().split(":")
        try:
            if len(parts) == 1:
                h, m, s = 0, int(parts[0]), 0
            elif len(parts) == 2:
                h, m, s = int(parts[0]), int(parts[1]), 0
            elif len(parts) == 3:
                h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
            else:
                return None
            total = h * 3600 + m * 60 + s
            return f"{total//3600:02d}:{(total%3600)//60:02d}:{total%60:02d}"
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _normalize_schedule_times(data: dict) -> None:
        """Normalize 'time' and 'duration' to HH:MM:SS directly on save
        (defensive -- regardless of whether JS already normalized them)."""
        for k in ("time", "duration"):
            v = data.get(k)
            if v not in (None, ""):
                normalized = IUStore._norm_time(v)
                if normalized is not None:
                    data[k] = normalized

    @staticmethod
    def _drop_defaults(obj: dict, defaults: dict) -> dict:
        """Remove from obj the fields that have the IU default value."""
        for k, dv in defaults.items():
            if k in obj and obj[k] == dv:
                del obj[k]
        return obj

    @staticmethod
    def _build_zones(zones: list) -> list:
        result = []
        for z in zones:
            obj: dict = {}
            TIME_KEYS_Z = {"minimum","maximum","threshold","duration"}
            for k in ("name","zone_id","enabled","allow_manual",
                      "minimum","maximum","threshold","duration"):
                v = z.get(k)
                if v in (None, ""): continue
                obj[k] = IUStore._norm_time(v) if k in TIME_KEYS_Z else v
            # entity_id: IU does `for e in entity_ids` -> must be a list
            if z.get("entity_id") not in (None, ""):
                obj["entity_id"] = [z["entity_id"]]
            # entity_states: skip if "all" (IU default) for a clean YAML
            if z.get("entity_states") and z["entity_states"] != "all":
                obj["entity_states"] = z["entity_states"]
            # future_span must be a float (IU does max(float, str) -> TypeError)
            fs = z.get("future_span")
            if fs not in (None, ""):
                try:
                    obj["future_span"] = int(float(fs))
                except (ValueError, TypeError):
                    pass
            # show: stored as flat keys -> nested in the IU config
            show: dict = {}
            if z.get("show_timeline"): show["timeline"] = True
            if z.get("show_config"):   show["config"]   = True
            if show: obj["show"] = show
            scheds = IUStore._schedules_to_iu(z.get("schedules", []))
            if scheds: obj["schedules"] = scheds
            adjs = IUStore._adjustments_to_iu(z.get("adjustments", []))
            if adjs: obj["adjustments"] = adjs
            IUStore._drop_defaults(obj, IUStore.ZONE_DEFAULTS)
            result.append(obj)
        return result

    @staticmethod
    def _build_sequences(seqs: list) -> list:
        result = []
        for s in seqs:
            obj: dict = {}
            for k in ("name","sequence_id","enabled"):
                if s.get(k) not in (None, ""): obj[k] = s[k]
            for k in ("delay","duration"):
                v = s.get(k)
                if v not in (None, ""): obj[k] = IUStore._norm_time(v)
            if s.get("repeat") and int(s["repeat"]) != 1: obj["repeat"] = s["repeat"]
            sz_list = []
            for sz in s.get("zones", []):
                sz_obj: dict = {}
                TIME_KEYS_SQZ = {"delay","duration"}
                for k in ("enabled","delay","duration"):
                    v = sz.get(k)
                    if v in (None, ""): continue
                    sz_obj[k] = IUStore._norm_time(v) if k in TIME_KEYS_SQZ else v
                # zone_id: IU does `for zone_id in _zone_ids` -> must be a list of str
                raw_zid = sz.get("zone_id")
                if raw_zid not in (None, ""):
                    if isinstance(raw_zid, list):
                        sz_obj["zone_id"] = _FL([str(z) for z in raw_zid])
                    else:
                        sz_obj["zone_id"] = _FL([str(raw_zid)])
                # entity_states: skip if "all" (IU default)
                if sz.get("entity_states") and sz["entity_states"] != "all":
                    sz_obj["entity_states"] = sz["entity_states"]
                if sz.get("repeat") and int(sz["repeat"]) != 1: sz_obj["repeat"] = sz["repeat"]
                if sz_obj: sz_list.append(sz_obj)
            if sz_list: obj["zones"] = sz_list
            scheds = IUStore._schedules_to_iu(s.get("schedules", []))
            if scheds: obj["schedules"] = scheds
            IUStore._drop_defaults(obj, IUStore.SEQ_DEFAULTS)
            if obj: result.append(obj)
        return result

    @staticmethod
    def _schedules_to_iu(schedules: list) -> list:
        result = []
        for s in schedules:
            obj: dict = {}
            TIME_KEYS_SCH = {"duration","time"}  # "time" normalizat defensiv la HH:MM:SS
            # "delay" is not a valid field in SCHEDULE_SCHEMA -- not included
            for k in ("name","schedule_id","enabled","time","duration","anchor","from","until","cron"):
                v = s.get(k)
                if v in (None, ""): continue
                obj[k] = IUStore._norm_time(v) if k in TIME_KEYS_SCH else v
            if s.get("weekday"): obj["weekday"] = _FL(s["weekday"]) if isinstance(s.get("weekday"), list) else s["weekday"]
            if s.get("month"):   obj["month"]   = _FL(s["month"])   if isinstance(s.get("month"), list)   else s["month"]
            if s.get("day") not in (None, ""):
                raw = s["day"]
                if isinstance(raw, str) and raw in ("odd","even"):
                    obj["day"] = raw
                else:
                    try:
                        parts = [int(p.strip()) for p in str(raw).split(",") if p.strip()]
                        obj["day"] = parts if len(parts) > 1 else parts[0]
                    except ValueError:
                        obj["day"] = raw
            # Defaults IU: anchor="start", enabled=true
            IUStore._drop_defaults(obj, {"anchor": "start", "enabled": True})
            if obj: result.append(obj)
        return result

    @staticmethod
    def _adjustments_to_iu(adjs: list) -> list:
        result = []
        for a in adjs:
            obj: dict = {}
            method = a.get("method","actual")
            value  = a.get("value")
            if method == "reset": obj["reset"] = None
            elif value not in (None, ""): obj[method] = value
            for k in ("minimum","maximum"):
                if a.get(k) not in (None, ""): obj[k] = a[k]
            if a.get("load_factor") not in (None, ""): obj["load_factor"] = a["load_factor"]
            if a.get("weekday"): obj["weekday"] = _FL(a["weekday"]) if isinstance(a.get("weekday"), list) else a["weekday"]
            if a.get("month"):   obj["month"]   = _FL(a["month"])   if isinstance(a.get("month"), list)   else a["month"]
            for k in ("day","from","until"):
                if a.get(k) not in (None, ""): obj[k] = a[k]
            if obj: result.append(obj)
        return result

    # ── Generic list helpers ──────────────────────────────────────────────────

    @staticmethod
    def _new_id() -> str:
        return uuid.uuid4().hex[:8]

    def _entry_zones(self, eid: str) -> list:
        return self._data.setdefault(eid, {"zones":[],"sequences":[]}).setdefault("zones",[])

    def _entry_seqs(self, eid: str) -> list:
        return self._data.setdefault(eid, {"zones":[],"sequences":[]}).setdefault("sequences",[])

    def _find_zone(self, eid: str, zid: str) -> dict | None:
        return next((z for z in self._entry_zones(eid) if z["id"] == zid), None)

    def _find_seq(self, eid: str, sid: str) -> dict | None:
        return next((s for s in self._entry_seqs(eid) if s["id"] == sid), None)

    async def _save_to(self, lst: list, data: dict) -> dict:
        if not data.get("id"):
            data["id"] = self._new_id()
            lst.append(data)
        else:
            idx = next((i for i,x in enumerate(lst) if x["id"] == data["id"]), None)
            if idx is not None:
                lst[idx] = data
            else:
                # BUG FIX: previously fell through without appending,
                # silently discarding the edit (data was never persisted).
                lst.append(data)
        await self._save(); return data

    async def _del_from(self, parent: dict, key: str, iid: str) -> bool:
        lst = parent.get(key,[])
        before = len(lst)
        parent[key] = [x for x in lst if x["id"] != iid]
        if len(parent[key]) != before:
            await self._save(); return True
        return False

    # ── Zones ─────────────────────────────────────────────────────────────────

    async def save_all_zones_config(self, eid: str, data: dict) -> dict:
        """Persist all_zones_config for a controller."""
        entry = self._data.setdefault(eid, {"zones": [], "sequences": [], "all_zones_config": {}})
        entry["all_zones_config"] = data
        await self._store.async_save(self._data)
        return data

    # -- Global config (section 5, top-level) -----------------------------

    GLOBAL_KEY = "__global__"

    def get_global_config(self) -> dict:
        """Return the top-level IU configuration (granularity, refresh_interval, etc.)."""
        return dict(self._data.get(self.GLOBAL_KEY, {}))

    async def save_global_config(self, data: dict) -> dict:
        """Persist global IU configuration."""
        self._data[self.GLOBAL_KEY] = data
        await self._store.async_save(self._data)
        return data

    # ── Controller CRUD ──────────────────────────────────────────────────────

    CTRL_KEYS = ("name","controller_id","entity_id","entity_states","enabled","queue_manual","show_sequence_status","preamble","postamble")

    # IU default values -- fields with these values are omitted from the YAML
    CTRL_DEFAULTS:  dict = {"enabled": True,  "queue_manual": False,
                            "show_sequence_status": False, "entity_states": "all",
                            # BUG FIX: preamble/postamble are run through
                            # _norm_time() -> "00:00:00" BEFORE _drop_defaults
                            # is applied (see to_iu_config_multi), so the
                            # default here must match that normalized form,
                            # not the raw "00:00" the user might type.
                            "preamble": "00:00:00", "postamble": "00:00:00"}
    ZONE_DEFAULTS:  dict = {"enabled": True,  "allow_manual": False,
                            "entity_states": "all", "future_span": 3}
    SEQ_DEFAULTS:   dict = {"enabled": True,  "repeat": 1}
    AZC_DEFAULTS:   dict = {"allow_manual": False, "entity_states": "all", "future_span": 3}
    GLOBAL_DEFAULTS:dict = {"granularity": 60, "refresh_interval": 30,
                            "rename_entities": False}
    HISTORY_DEFAULTS:dict = {"enabled": True}
    CLOCK_DEFAULTS: dict = {"mode": "seer", "show_log": False}

    async def save_controller(self, ctrl_id: str | None, data: dict) -> tuple[str, dict]:
        """Create (ctrl_id=None) or update a controller. Returns (ctrl_id, basics)."""
        if not ctrl_id:
            import time
            ctrl_id = f"ctrl_{int(time.time()*1000):013x}"
        entry = self._data.setdefault(
            ctrl_id, {"zones": [], "sequences": [], "all_zones_config": {}}
        )
        entry.setdefault("all_zones_config", {})
        for k in self.CTRL_KEYS:
            v = data.get(k)
            if v not in (None, ""):
                entry[k] = v
            else:
                entry.pop(k, None)
        await self._store.async_save(self._data)
        basics = {k: entry[k] for k in self.CTRL_KEYS if k in entry}
        return ctrl_id, basics

    async def delete_controller(self, ctrl_id: str) -> None:
        """Remove a controller and all its data."""
        self._data.pop(ctrl_id, None)
        await self._store.async_save(self._data)

    def get_controller_list(self) -> list[tuple[str, dict]]:
        """Return [(ctrl_id, basics)] for all entries that have a controller name."""
        result = []
        for ctrl_id, ed in self._data.items():
            if ctrl_id == "__migrated__":
                continue
            if ed.get("name"):
                basics = {k: ed[k] for k in self.CTRL_KEYS if k in ed}
                result.append((ctrl_id, basics))
        return result

    async def save_zone(self, eid: str, data: dict) -> dict:
        zones = self._entry_zones(eid)
        data.setdefault("schedules", []); data.setdefault("adjustments", [])
        if data.get("id"):
            idx = next((i for i,z in enumerate(zones) if z["id"]==data["id"]), None)
            if idx is not None:
                data["schedules"]    = zones[idx].get("schedules", data["schedules"])
                data["adjustments"]  = zones[idx].get("adjustments", data["adjustments"])
                zones[idx] = data; await self._save(); return data
        data["id"] = self._new_id(); zones.append(data); await self._save(); return data

    async def delete_zone(self, eid: str, zid: str) -> bool:
        zones = self._entry_zones(eid); before = len(zones)
        self._data[eid]["zones"] = [z for z in zones if z["id"] != zid]
        if len(self._data[eid]["zones"]) != before: await self._save(); return True
        return False

    async def save_schedule(self, eid: str, zid: str, data: dict) -> dict | None:
        IUStore._normalize_schedule_times(data)
        z = self._find_zone(eid, zid)
        return await self._save_to(z.setdefault("schedules",[]), data) if z else None

    async def delete_schedule(self, eid: str, zid: str, sid: str) -> bool:
        z = self._find_zone(eid, zid)
        return await self._del_from(z, "schedules", sid) if z else False

    async def save_adjustment(self, eid: str, zid: str, data: dict) -> dict | None:
        z = self._find_zone(eid, zid)
        return await self._save_to(z.setdefault("adjustments",[]), data) if z else None

    async def delete_adjustment(self, eid: str, zid: str, aid: str) -> bool:
        z = self._find_zone(eid, zid)
        return await self._del_from(z, "adjustments", aid) if z else False

    # ── Sequences ─────────────────────────────────────────────────────────────

    async def save_sequence(self, eid: str, data: dict) -> dict:
        seqs = self._entry_seqs(eid)
        data.setdefault("zones",[]); data.setdefault("schedules",[])
        if data.get("id"):
            idx = next((i for i,s in enumerate(seqs) if s["id"]==data["id"]), None)
            if idx is not None:
                data["zones"]     = seqs[idx].get("zones", data["zones"])
                data["schedules"] = seqs[idx].get("schedules", data["schedules"])
                seqs[idx] = data; await self._save(); return data
        data["id"] = self._new_id(); seqs.append(data); await self._save(); return data

    async def delete_sequence(self, eid: str, sid: str) -> bool:
        seqs = self._entry_seqs(eid); before = len(seqs)
        self._data[eid]["sequences"] = [s for s in seqs if s["id"] != sid]
        if len(self._data[eid]["sequences"]) != before: await self._save(); return True
        return False

    async def save_sequence_zone(self, eid: str, sid: str, data: dict) -> dict | None:
        s = self._find_seq(eid, sid)
        return await self._save_to(s.setdefault("zones",[]), data) if s else None

    async def delete_sequence_zone(self, eid: str, sid: str, zid: str) -> bool:
        s = self._find_seq(eid, sid)
        return await self._del_from(s, "zones", zid) if s else False

    async def save_sequence_schedule(self, eid: str, sid: str, data: dict) -> dict | None:
        IUStore._normalize_schedule_times(data)
        s = self._find_seq(eid, sid)
        return await self._save_to(s.setdefault("schedules",[]), data) if s else None

    async def delete_sequence_schedule(self, eid: str, sid: str, schid: str) -> bool:
        s = self._find_seq(eid, sid)
        return await self._del_from(s, "schedules", schid) if s else False
