"""
Custom integration to integrate irrigation_unlimited with Home Assistant.

For more details about this integration, please refer to
https://github.com/rgc99/irrigation_unlimited
"""
import logging
import voluptuous as vol
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.core import Config, HomeAssistant
from homeassistant.const import (
    CONF_AFTER,
    CONF_BEFORE,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_WEEKDAY,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform

from .irrigation_unlimited import IUCoordinator
from .entity import IUComponent
from .service import register_component_services

from .const import (
    BINARY_SENSOR,
    CONF_ENABLED,
    CONF_MAXIMUM,
    CONF_MINIMUM,
    CONF_MONTH,
    CONF_DAY,
    CONF_ODD,
    CONF_EVEN,
    DOMAIN,
    COORDINATOR,
    COMPONENT,
    STARTUP_MESSAGE,
    CONF_CONTROLLERS,
    CONF_SCHEDULES,
    CONF_ZONES,
    CONF_DURATION,
    CONF_SUN,
    CONF_TIME,
    CONF_PREAMBLE,
    CONF_POSTAMBLE,
    CONF_GRANULARITY,
    CONF_TESTING,
    CONF_SPEED,
    CONF_TIMES,
    CONF_START,
    CONF_END,
    MONTHS,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


def _list_is_not_empty(value):
    if value is None or len(value) < 1:
        raise vol.Invalid("Must have at least one entry")
    return value


SUN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SUN): cv.sun_event,
        vol.Optional(CONF_BEFORE): cv.positive_time_period,
        vol.Optional(CONF_AFTER): cv.positive_time_period,
    }
)

time_event = vol.Any(cv.time, SUN_SCHEMA)
month_event = vol.All(cv.ensure_list, [vol.In(MONTHS)])

day_number = vol.All(vol.Coerce(int), vol.Range(min=0, max=31))
day_event = vol.Any(CONF_ODD, CONF_EVEN, cv.ensure_list(day_number))

SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TIME): time_event,
        vol.Required(CONF_DURATION): cv.positive_time_period,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_WEEKDAY): cv.weekdays,
        vol.Optional(CONF_MONTH): month_event,
        vol.Optional(CONF_DAY): day_event,
    }
)

ZONE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SCHEDULES, default={}): vol.All(
            cv.ensure_list, [SCHEDULE_SCHEMA], _list_is_not_empty
        ),
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_ENTITY_ID): cv.entity_id,
        vol.Optional(CONF_ENABLED): cv.boolean,
        vol.Optional(CONF_MINIMUM): cv.positive_time_period,
        vol.Optional(CONF_MAXIMUM): cv.positive_time_period,
    }
)

CONTROLLER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ZONES): vol.All(
            cv.ensure_list, [ZONE_SCHEMA], _list_is_not_empty
        ),
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_ENTITY_ID): cv.entity_id,
        vol.Optional(CONF_PREAMBLE): cv.positive_time_period,
        vol.Optional(CONF_POSTAMBLE): cv.positive_time_period,
        vol.Optional(CONF_ENABLED): cv.boolean,
    }
)

TEST_TIME_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_START): cv.datetime,
        vol.Required(CONF_END): cv.datetime,
        vol.Optional(CONF_NAME): cv.string,
    }
)

TEST_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ENABLED): cv.boolean,
        vol.Optional(CONF_SPEED): cv.positive_float,
        vol.Optional(CONF_TIMES): [TEST_TIME_SCHEMA],
    }
)

IRRIGATION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CONTROLLERS, default={}): vol.All(
            cv.ensure_list, [CONTROLLER_SCHEMA], _list_is_not_empty
        ),
        vol.Optional(CONF_GRANULARITY): cv.positive_int,
        vol.Optional(CONF_TESTING): TEST_SCHEMA,
    }
)

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

    register_component_services(component)

    coordinator.start()

    return True
