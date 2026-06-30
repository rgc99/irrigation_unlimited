"""
Config flow for Irrigation Unlimited -- instant install, all management in panel.

--------------------------------------------------------------------------------
Modifications vs upstream master
--------------------------------------------------------------------------------
This file completely replaces upstream's config_flow.py (~760 lines), which
implemented a multi-step setup wizard plus an OptionsFlow and a
ConfigSubentryFlow for adding/editing controllers, zones, sequences,
schedules and adjustments entirely through HA's config-entry UI.

That entire wizard/options/subentry flow is removed and replaced by:

- A single-step async_step_user that creates the config entry immediately,
  with no form and empty data ({}).
- No OptionsFlow, no ConfigSubentryFlow, no async_get_supported_subentry_types.
- All controller/zone/sequence/schedule/adjustment/global-config CRUD that
  upstream did via this config flow is now handled by the custom frontend
  panel (frontend/irrigation-unlimited-panel.js) via WebSocket commands
  (websocket_api.py), backed by persistent storage (storage.py / IUStore).

async_set_unique_id + _abort_if_unique_id_configured ensures only one
instance of the integration can be added (panel manages multiple physical
controllers internally, so a second config entry is never needed).
--------------------------------------------------------------------------------
"""
from __future__ import annotations
from homeassistant import config_entries
from .const import DOMAIN


class IrrigationUnlimitedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Install instantly -- controllers are managed from the Irrigation panel."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Irrigation Unlimited", data={})
