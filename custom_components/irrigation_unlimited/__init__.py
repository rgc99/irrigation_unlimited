"""
Custom integration to integrate irrigation_unlimited with Home Assistant.

For more details about this integration, please refer to
https://github.com/rgc99/irrigation_unlimited
"""
import logging
import voluptuous as vol
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.core import Config, HomeAssistant
from homeassistant.helpers.discovery import async_load_platform

from .irrigation_unlimited import IUCoordinator
from .entity import IUComponent
from .service import register_component_services

from .schema import (
    IRRIGATION_SCHEMA,
)

from .const import (
    BINARY_SENSOR,
    DOMAIN,
    COORDINATOR,
    COMPONENT,
    STARTUP_MESSAGE,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


CONFIG_SCHEMA = vol.Schema({DOMAIN: IRRIGATION_SCHEMA}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML."""

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

    register_component_services(component, coordinator)

    coordinator.listen()
    coordinator.clock.start()

    return True
