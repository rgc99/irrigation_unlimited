"""
Custom integration to integrate irrigation_unlimited with Home Assistant.

For more details about this integration, please refer to
https://github.com/rgc99/irrigation_unlimited
"""

import logging
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers import entity_registry as er
from homeassistant.core import HomeAssistant
from homeassistant.core_config import Config
from homeassistant.helpers.discovery import async_load_platform

from .irrigation_unlimited import IUCoordinator
from .entity import IUComponent
from .service import register_component_services

from .schema import (
    IRRIGATION_SCHEMA,
)

from .const import (
    BINARY_SENSOR,
    BUTTON,
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

    if DOMAIN not in config:
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

    # Options written by the options flow take precedence over initial data
    config = dict(entry.options) if entry.options else dict(entry.data)

    hass.data.setdefault(DOMAIN, {})
    coordinator = IUCoordinator(hass).load(config)
    hass.data[DOMAIN][COORDINATOR] = coordinator

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    hass.data[DOMAIN][COMPONENT] = component

    await component.async_add_entities([IUComponent(coordinator)])

    # Associate the coordinator entity with this config entry so it is
    # removed automatically when the integration is deleted.
    ent_reg = er.async_get(hass)
    if coordinator_entry := ent_reg.async_get(coordinator.entity_id):
        ent_reg.async_update_entity(
            coordinator_entry.entity_id, config_entry_id=entry.entry_id
        )

    await hass.config_entries.async_forward_entry_setups(entry, [BINARY_SENSOR, BUTTON, SWITCH])

    register_component_services(component, coordinator)

    coordinator.listen()
    coordinator.clock.start()

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, [BINARY_SENSOR, BUTTON, SWITCH])

    coordinator: IUCoordinator = hass.data[DOMAIN].get(COORDINATOR)
    if coordinator is not None:
        coordinator.finalise(False)

    component: EntityComponent = hass.data[DOMAIN].get(COMPONENT)
    if component is not None:
        for entity in list(component.entities):
            await entity.async_remove()

    hass.data.pop(DOMAIN, None)
    return unload_ok
