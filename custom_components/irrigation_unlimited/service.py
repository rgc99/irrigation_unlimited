from homeassistant.core import ServiceCall
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service
import voluptuous as vol
from homeassistant.const import (
    CONF_ENTITY_ID,
    SERVICE_RELOAD,
)

from .irrigation_unlimited import IUCoordinator
from .entity import IUEntity
from .const import (
    DOMAIN,
    SERVICE_ENABLE,
    SERVICE_DISABLE,
    SERVICE_TIME_ADJUST,
    SERVICE_MANUAL_RUN,
    CONF_PERCENTAGE,
    CONF_ACTUAL,
    CONF_INCREASE,
    CONF_DECREASE,
    CONF_RESET,
    CONF_TIME,
    CONF_MINIMUM,
    CONF_MAXIMUM,
    CONF_ZONES,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_MANUAL_RUN,
    SERVICE_TIME_ADJUST,
)

ENABLE_SCHEMA = {
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
}

DISABLE_SCHEMA = {vol.Required(CONF_ENTITY_ID): cv.entity_id}

TIME_ADJUST_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_ENTITY_ID): cv.entity_id,
            vol.Exclusive(CONF_ACTUAL, "adjust_method"): cv.positive_time_period,
            vol.Exclusive(CONF_PERCENTAGE, "adjust_method"): cv.positive_float,
            vol.Exclusive(CONF_INCREASE, "adjust_method"): cv.positive_time_period,
            vol.Exclusive(CONF_DECREASE, "adjust_method"): cv.positive_time_period,
            vol.Exclusive(CONF_RESET, "adjust_method"): str,
            vol.Optional(CONF_MINIMUM): cv.positive_time_period,
            vol.Optional(CONF_MAXIMUM): cv.positive_time_period,
            vol.Optional(CONF_ZONES): cv.ensure_list,
        }
    ),
    cv.has_at_least_one_key(CONF_ACTUAL, CONF_PERCENTAGE, CONF_INCREASE, CONF_DECREASE),
)

MANUAL_RUN_SCHEMA = {
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_TIME): cv.positive_time_period,
    vol.Optional(CONF_ZONES): cv.ensure_list,
}

RELOAD_SERVICE_SCHEMA = vol.Schema({})


async def async_enable(entity: IUEntity, call: ServiceCall) -> None:
    entity.dispatch(SERVICE_ENABLE, call)
    return


async def async_disable(entity: IUEntity, call: ServiceCall) -> None:
    entity.dispatch(SERVICE_DISABLE, call)
    return


async def async_time_adjust(entity: IUEntity, call: ServiceCall) -> None:
    entity.dispatch(SERVICE_TIME_ADJUST, call)
    return


async def async_manual_run(entity: IUEntity, call: ServiceCall) -> None:
    entity.dispatch(SERVICE_MANUAL_RUN, call)
    return


def register_platform_services(platform: entity_platform.EntityPlatform) -> None:
    platform.async_register_entity_service(SERVICE_ENABLE, ENABLE_SCHEMA, async_enable)
    platform.async_register_entity_service(
        SERVICE_DISABLE, DISABLE_SCHEMA, async_disable
    )
    platform.async_register_entity_service(
        SERVICE_TIME_ADJUST, TIME_ADJUST_SCHEMA, async_time_adjust
    )
    platform.async_register_entity_service(
        SERVICE_MANUAL_RUN, MANUAL_RUN_SCHEMA, async_manual_run
    )
    return


def register_component_services(
    component: EntityComponent, coordinator: IUCoordinator
) -> None:
    async def reload_service_handler(call: ServiceCall) -> None:
        """Reload yaml entities."""
        conf = await component.async_prepare_reload(skip_reset=True)
        if conf is None:
            conf = {DOMAIN: {}}
        coordinator.load(conf[DOMAIN])
        return

    async_register_admin_service(
        component.hass,
        DOMAIN,
        SERVICE_RELOAD,
        reload_service_handler,
        schema=RELOAD_SERVICE_SCHEMA,
    )
    return
