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
    CONF_REPEAT,
    CONF_WEEKDAY,
    CONF_DELAY,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform

from .irrigation_unlimited import IUCoordinator
from .entity import IUComponent
from .service import register_component_services

from .const import (
    BINARY_SENSOR,
    CONF_ENABLED,
    CONF_FINISH,
    CONF_FUTURE_SPAN,
    CONF_HISTORY_REFRESH,
    CONF_HISTORY_SPAN,
    CONF_MAXIMUM,
    CONF_MINIMUM,
    CONF_MONTH,
    CONF_DAY,
    CONF_ODD,
    CONF_EVEN,
    CONF_RESULTS,
    CONF_SHOW_LOG,
    CONF_AUTOPLAY,
    CONF_ANCHOR,
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
    CONF_SHOW,
    CONF_CONFIG,
    CONF_TIMELINE,
    CONF_ZONE_ID,
    CONF_SEQUENCES,
    CONF_ALL_ZONES_CONFIG,
    CONF_REFRESH_INTERVAL,
    CONF_OUTPUT_EVENTS,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


def _list_is_not_empty(value):
    if value is None or len(value) < 1:
        raise vol.Invalid("Must have at least one entry")
    return value


SHOW_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CONFIG, False): cv.boolean,
        vol.Optional(CONF_TIMELINE, False): cv.boolean,
    }
)

SUN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SUN): cv.sun_event,
        vol.Optional(CONF_BEFORE): cv.positive_time_period,
        vol.Optional(CONF_AFTER): cv.positive_time_period,
    }
)

time_event = vol.Any(cv.time, SUN_SCHEMA)
anchor_event = vol.Any(CONF_START, CONF_FINISH)
month_event = vol.All(cv.ensure_list, [vol.In(MONTHS)])

day_number = vol.All(vol.Coerce(int), vol.Range(min=0, max=31))
day_event = vol.Any(CONF_ODD, CONF_EVEN, cv.ensure_list(day_number))

SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TIME): time_event,
        vol.Required(CONF_ANCHOR, default=CONF_START): anchor_event,
        vol.Required(CONF_DURATION): cv.positive_time_period,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_WEEKDAY): cv.weekdays,
        vol.Optional(CONF_MONTH): month_event,
        vol.Optional(CONF_DAY): day_event,
    }
)

ZONE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SCHEDULES): vol.All(cv.ensure_list, [SCHEDULE_SCHEMA]),
        vol.Optional(CONF_ZONE_ID): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_ENTITY_ID): cv.entity_ids,
        vol.Optional(CONF_ENABLED): cv.boolean,
        vol.Optional(CONF_MINIMUM): cv.positive_time_period,
        vol.Optional(CONF_MAXIMUM): cv.positive_time_period,
        vol.Optional(CONF_FUTURE_SPAN): cv.positive_int,
        vol.Optional(CONF_SHOW): vol.All(SHOW_SCHEMA),
    }
)

ALL_ZONES_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SHOW): vol.All(SHOW_SCHEMA),
        vol.Optional(CONF_MINIMUM): cv.positive_time_period,
        vol.Optional(CONF_MAXIMUM): cv.positive_time_period,
        vol.Optional(CONF_FUTURE_SPAN): cv.positive_int,
    }
)

SEQUENCE_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TIME): time_event,
        vol.Required(CONF_ANCHOR, default=CONF_START): anchor_event,
        vol.Optional(CONF_DURATION): cv.positive_time_period,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_WEEKDAY): cv.weekdays,
        vol.Optional(CONF_MONTH): month_event,
        vol.Optional(CONF_DAY): day_event,
    }
)

SEQUENCE_ZONE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ZONE_ID): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_DELAY): cv.positive_time_period,
        vol.Optional(CONF_DURATION): cv.positive_time_period,
        vol.Optional(CONF_REPEAT): cv.positive_int,
        vol.Optional(CONF_ENABLED): cv.boolean,
    }
)

SEQUENCE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SCHEDULES, default={}): vol.All(
            cv.ensure_list, [SEQUENCE_SCHEDULE_SCHEMA], _list_is_not_empty
        ),
        vol.Required(CONF_ZONES, default={}): vol.All(
            cv.ensure_list, [SEQUENCE_ZONE_SCHEMA], _list_is_not_empty
        ),
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_DELAY): cv.positive_time_period,
        vol.Optional(CONF_DURATION): cv.positive_time_period,
        vol.Optional(CONF_REPEAT): cv.positive_int,
        vol.Optional(CONF_ENABLED): cv.boolean,
    }
)

CONTROLLER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ZONES): vol.All(
            cv.ensure_list, [ZONE_SCHEMA], _list_is_not_empty
        ),
        vol.Optional(CONF_SEQUENCES): vol.All(
            cv.ensure_list, [SEQUENCE_SCHEMA], _list_is_not_empty
        ),
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_ENTITY_ID): cv.entity_ids,
        vol.Optional(CONF_PREAMBLE): cv.positive_time_period,
        vol.Optional(CONF_POSTAMBLE): cv.positive_time_period,
        vol.Optional(CONF_ENABLED): cv.boolean,
        vol.Optional(CONF_ALL_ZONES_CONFIG): vol.All(ALL_ZONES_SCHEMA),
    }
)

TEST_RESULT_SCHEMA = vol.Schema(
    {
        vol.Required("t"): cv.datetime,
        vol.Required("c"): cv.positive_int,
        vol.Required("z"): cv.positive_int,
        vol.Required("s"): cv.boolean,
    }
)

TEST_TIME_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_START): cv.datetime,
        vol.Required(CONF_END): cv.datetime,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_RESULTS): [TEST_RESULT_SCHEMA],
    }
)

TEST_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ENABLED): cv.boolean,
        vol.Optional(CONF_SPEED): cv.positive_float,
        vol.Optional(CONF_TIMES): [TEST_TIME_SCHEMA],
        vol.Optional(CONF_OUTPUT_EVENTS): cv.boolean,
        vol.Optional(CONF_SHOW_LOG): cv.boolean,
        vol.Optional(CONF_AUTOPLAY): cv.boolean,
    }
)

IRRIGATION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CONTROLLERS, default={}): vol.All(
            cv.ensure_list, [CONTROLLER_SCHEMA], _list_is_not_empty
        ),
        vol.Optional(CONF_GRANULARITY): cv.positive_int,
        vol.Optional(CONF_REFRESH_INTERVAL): cv.positive_int,
        vol.Optional(CONF_HISTORY_SPAN): cv.positive_int,
        vol.Optional(CONF_HISTORY_REFRESH): cv.positive_int,
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

    register_component_services(component, coordinator)

    coordinator.listen()
    coordinator.start()

    return True
