"""
Custom integration to integrate irrigation_unlimited with Home Assistant.

For more details about this integration, please refer to
https://github.com/rgc99/irrigation_unlimited

--------------------------------------------------------------------------------
Modifications vs upstream master (custom panel branch)
--------------------------------------------------------------------------------
This file replaces the upstream config-entry setup with a "panel-managed
controllers" architecture:

- A SINGLE config entry is created instantly by config_flow.py (no setup
  form). All controller CRUD (add/edit/delete, zones, sequences, schedules,
  adjustments, global config) is done from a custom frontend panel instead
  of the HA config-entry UI / options flow / subentries.
- A new persistent store (storage.py / IUStore) is the source of truth for
  controller configuration. It is loaded once per HA session and shared via
  hass.data[DOMAIN]["store"].
- A new static file route + custom sidebar panel
  ("Irrigation" / irrigation-unlimited-panel.js) is registered.
- New WebSocket commands (websocket_api.py) back the panel's CRUD UI.
- One-shot migration: if an old-style config entry (entry.data) or
  HA-native subentries (entry.subentries) contain controller data, it is
  copied into IUStore on first load, entry.data is cleared, and the entry
  is reloaded to continue from panel storage.
- async_setup (YAML) now also stashes the raw YAML config in
  hass.data[DOMAIN]["yaml_config"] so async_setup_entry can use it for a
  one-time auto-import of zones/sequences into a freshly migrated panel
  controller (matched by controller name).
- async_unload_entry now preserves yaml_config / store / panel_registered /
  static_registered / ws_registered across entry reloads (previously the
  whole hass.data[DOMAIN] dict was discarded on unload), so reloading the
  main entry (e.g. after a panel save) does not need to re-register the
  static path, the sidebar panel or the WebSocket commands.
- New async_remove_entry: full cleanup (remove sidebar panel, drop
  hass.data[DOMAIN]) when the user explicitly deletes the integration.
--------------------------------------------------------------------------------
"""

from __future__ import annotations  # enables PEP 563 postponed evaluation of annotations;
                                    # consistent with all other files in this integration
import logging
from pathlib import Path  # NEW: needed to resolve the bundled frontend/ dir for StaticPathConfig

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
# NEW: built-in panel registration (custom sidebar panel for the IU frontend)
from homeassistant.components.frontend import (
    async_register_built_in_panel,
    async_remove_panel,
)
# NEW: serve the bundled frontend/ directory as static files
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.core import HomeAssistant
from homeassistant.core_config import Config
from homeassistant.helpers.discovery import async_load_platform

from .irrigation_unlimited import IUCoordinator
from .entity import IUComponent
from .service import register_component_services
# NEW: panel-managed controller storage + WebSocket API for the custom panel
from .storage import IUStore
from . import websocket_api as iu_ws_api

from .schema import (
    IRRIGATION_SCHEMA,
)

from .const import (
    BINARY_SENSOR,
    BUTTON,
    NUMBER,
    SWITCH,
    DOMAIN,
    COORDINATOR,
    COMPONENT,
    STARTUP_MESSAGE,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


CONFIG_SCHEMA = vol.Schema({DOMAIN: IRRIGATION_SCHEMA}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML."""

    # NEW: stash the raw YAML config BEFORE any early-return guard, so
    # async_setup_entry can use it later for one-time auto-import of
    # zones/sequences into a matching panel controller (by name).
    if DOMAIN in config:
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["yaml_config"] = config[DOMAIN]

    if DOMAIN not in config:
        return True

    # NEW: with the panel architecture, a config entry always exists once the
    # integration has been added via the UI. If it exists, coordinator setup
    # is handled entirely by async_setup_entry (panel storage), so the legacy
    # full-YAML coordinator/platforms below must not run.
    if hass.config_entries.async_entries(DOMAIN):
        return True

    _LOGGER.info(STARTUP_MESSAGE)

    hass.data[DOMAIN] = {}
    coordinator = IUCoordinator(hass).load(config[DOMAIN])
    hass.data[DOMAIN][COORDINATOR] = coordinator

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    hass.data[DOMAIN][COMPONENT] = component

    await component.async_add_entities([IUComponent(coordinator)])

    await hass.async_create_task(
        async_load_platform(hass, BINARY_SENSOR, DOMAIN, {}, config)
    )
    await hass.async_create_task(
        async_load_platform(hass, BUTTON, DOMAIN, {}, config)
    )
    await hass.async_create_task(
        async_load_platform(hass, NUMBER, DOMAIN, {}, config)
    )
    await hass.async_create_task(
        async_load_platform(hass, SWITCH, DOMAIN, {}, config)
    )

    register_component_services(component, coordinator)

    coordinator.listen()
    coordinator.clock.start()

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration from a config entry (UI)."""

    _LOGGER.info(STARTUP_MESSAGE)

    hass.data.setdefault(DOMAIN, {})

    # ── NEW: shared panel store ──────────────────────────────────────────────
    # IUStore (storage.py) is the persistent, panel-managed source of truth
    # for controllers/zones/sequences/schedules/adjustments/global config.
    # Loaded once and cached in hass.data so reloads reuse the same instance.
    if "store" not in hass.data[DOMAIN]:
        store = IUStore(hass)
        await store.async_load()
        hass.data[DOMAIN]["store"] = store
    else:
        store = hass.data[DOMAIN]["store"]

    # ── NEW: static files, sidebar panel, WS commands — BEFORE the coordinator ─
    # Registered first so the panel still loads even if building the IU
    # coordinator below fails (e.g. invalid stored config).
    if not hass.data[DOMAIN].get("static_registered"):
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                "/irrigation_unlimited_static",
                str(Path(__file__).parent / "frontend"),
                cache_headers=False,
            )
        ])
        hass.data[DOMAIN]["static_registered"] = True

    if not hass.data[DOMAIN].get("panel_registered"):
        async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title="Irrigation",
            sidebar_icon="mdi:water",
            frontend_url_path="irrigation-unlimited",
            config={
                "_panel_custom": {
                    "name": "irrigation-unlimited-panel",
                    "module_url": (
                        "/irrigation_unlimited_static"
                        "/irrigation-unlimited-panel.js"
                    ),
                    "embed_iframe": False,
                    "trust_external": False,
                }
            },
            require_admin=True,
        )
        hass.data[DOMAIN]["panel_registered"] = True

    # NEW: register the panel's WebSocket CRUD commands (websocket_api.py)
    iu_ws_api.async_register_commands(hass)
    hass.data[DOMAIN]["ws_registered"] = True

    # ── NEW: one-shot migration — entry.data / subentries -> panel storage ────
    # Upstream master stores controller config either directly in entry.data
    # (single-controller) or in HA-native subentries (multi-controller). On
    # first run with the panel architecture, copy any such data into IUStore,
    # clear entry.data and reload so the rest of setup runs purely from the
    # panel store.
    migrated = False
    if entry.data.get("name"):
        eid = entry.entry_id
        if not store.get_entry_data(eid).get("name"):
            _LOGGER.info("IU: migrating controller from entry.data to panel storage")
            await store.save_controller(eid, dict(entry.data))
            migrated = True
    for sid, subentry in getattr(entry, "subentries", {}).items():
        if getattr(subentry, "subentry_type", None) == "controller":
            if not store.get_entry_data(sid).get("name"):
                _LOGGER.info("IU: migrating subentry %s to panel storage", sid[:8])
                await store.save_controller(sid, dict(subentry.data))
                migrated = True
    if migrated:
        hass.config_entries.async_update_entry(entry, data={})
        # Reload will re-run this function, this time loading from panel storage.
        return True

    # ── NEW: build the controller list from panel storage ────────────────────
    controller_list = store.get_controller_list()

    # NEW: match YAML config controllers by name for one-time auto-import of
    # zones/sequences into a panel controller that has none yet (see
    # websocket_api.ws_get_config / _auto_import).
    yaml_ctrls = hass.data[DOMAIN].get("yaml_config", {}).get("controllers", [])
    for cid, ctrl_basics in controller_list:
        src = next((c for c in yaml_ctrls if c.get("name") == ctrl_basics.get("name")), {})
        hass.data[DOMAIN][f"coord_src_{cid}"] = src

    # NEW: build the full multi-controller IU config from panel storage
    # (replaces upstream's single `config = dict(entry.options or entry.data)`).
    iu_config = store.to_iu_config_multi(controller_list)
    coordinator = IUCoordinator(hass).load(iu_config)

    hass.data[DOMAIN][COORDINATOR] = coordinator
    hass.data[DOMAIN][entry.entry_id] = {COORDINATOR: coordinator}

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    hass.data[DOMAIN][COMPONENT] = component

    await component.async_add_entities([IUComponent(coordinator)])

    ent_reg = er.async_get(hass)
    if coordinator_entry := ent_reg.async_get(coordinator.entity_id):
        ent_reg.async_update_entity(
            coordinator_entry.entity_id, config_entry_id=entry.entry_id
        )

    await hass.config_entries.async_forward_entry_setups(
        entry, [BINARY_SENSOR, BUTTON, NUMBER, SWITCH]
    )

    register_component_services(component, coordinator)

    # Override the master's reload service with a panel-aware version.
    # The master's handler calls coordinator.load(conf[DOMAIN]) where conf
    # comes from YAML; if the user has no 'controllers:' in YAML (panel-only
    # mode) this raises KeyError: 'controllers'. Our version reloads from store.
    from homeassistant.const import SERVICE_RELOAD  # noqa: PLC0415
    from homeassistant.helpers.service import async_register_admin_service  # noqa: PLC0415
    from .binary_sensor import async_reload_platform as _bs_reload  # noqa: PLC0415

    async def _panel_reload_service(call: ServiceCall) -> None:
        """Reload coordinator from panel store, not from YAML."""
        iu_cfg = store.to_iu_config_multi(store.get_controller_list())
        coordinator.load(iu_cfg)
        await _bs_reload(component, coordinator)

    async_register_admin_service(hass, DOMAIN, SERVICE_RELOAD, _panel_reload_service)

    coordinator.listen()
    coordinator.clock.start()

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry (e.g. when a subentry is added/removed -> reload)."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [BINARY_SENSOR, BUTTON, NUMBER, SWITCH]
    )

    # Remove entity registry entries for unloaded platforms so that deleted
    # controllers/zones don't persist as "unavailable" after reload.
    # On re-setup, async_add_entities re-creates only current entities.
    _er = er.async_get(hass)
    for ent in er.async_entries_for_config_entry(_er, entry.entry_id):
        if ent.domain in (BINARY_SENSOR, BUTTON, NUMBER, SWITCH):
            _er.async_remove(ent.entity_id)

    # Remove devices that belong to this config entry and have no remaining
    # entities (e.g. deleted zones leave an empty device in the registry).
    _dr = dr.async_get(hass)
    for dev in dr.async_entries_for_config_entry(_dr, entry.entry_id):
        if not er.async_entries_for_device(_er, dev.id, include_disabled_entities=True):
            _dr.async_remove_device(dev.id)

    # CHANGED: use a local reference instead of hass.data[DOMAIN] directly,
    # since (unlike upstream) this dict is no longer fully popped below.
    d = hass.data.get(DOMAIN, {})

    coordinator: IUCoordinator = d.get(COORDINATOR)
    if coordinator is not None:
        coordinator.finalise(False)

    component: EntityComponent = d.get(COMPONENT)
    if component is not None:
        for entity in list(component.entities):
            await entity.async_remove()

    # CHANGED: upstream did `hass.data.pop(DOMAIN, None)` here, wiping
    # everything on every unload/reload. With the panel architecture this
    # would force re-registering the static path, sidebar panel and WS
    # commands (and lose yaml_config / store) on every reload triggered by a
    # panel save. Instead, remove only the per-reload keys and keep
    # yaml_config, store, panel_registered, static_registered, ws_registered.
    for key in list(d.keys()):
        if key in (COORDINATOR, COMPONENT) or key.startswith(("coord_src_", "_rl_")):
            d.pop(key, None)
    d.pop(entry.entry_id, None)

    return unload_ok


# NEW: not present upstream. Upstream relied on hass.data.pop(DOMAIN, None)
# inside async_unload_entry for full cleanup; here that pop is intentionally
# removed from async_unload_entry (see above), so full cleanup -- including
# removing the custom sidebar panel -- is performed here instead, only when
# the user explicitly deletes the integration.
async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Full cleanup when the user explicitly deletes the integration."""
    if hass.data.get(DOMAIN, {}).get("panel_registered"):
        async_remove_panel(hass, "irrigation-unlimited")
    hass.data.pop(DOMAIN, None)
