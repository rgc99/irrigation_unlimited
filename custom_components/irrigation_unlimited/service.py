from typing import Optional
from homeassistant.core import ServiceCall, callback
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
    SERVICE_CANCEL,
    SERVICE_ENABLE,
    SERVICE_DISABLE,
    SERVICE_TOGGLE,
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
    CONF_SEQUENCE_ID,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_MANUAL_RUN,
    SERVICE_TIME_ADJUST,
)

ENTITY_SCHEMA = {vol.Required(CONF_ENTITY_ID): cv.entity_id}

TIME_ADJUST_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_ENTITY_ID): cv.entity_id,
            vol.Exclusive(CONF_ACTUAL, "adjust_method"): cv.positive_time_period,
            vol.Exclusive(CONF_PERCENTAGE, "adjust_method"): cv.positive_float,
            vol.Exclusive(CONF_INCREASE, "adjust_method"): cv.positive_time_period,
            vol.Exclusive(CONF_DECREASE, "adjust_method"): cv.positive_time_period,
            vol.Exclusive(CONF_RESET, "adjust_method"): None,
            vol.Optional(CONF_MINIMUM): cv.positive_time_period,
            vol.Optional(CONF_MAXIMUM): cv.positive_time_period,
            vol.Optional(CONF_ZONES): cv.ensure_list,
            vol.Optional(CONF_SEQUENCE_ID): cv.positive_int,
        }
    ),
    cv.has_at_least_one_key(
        CONF_ACTUAL, CONF_PERCENTAGE, CONF_INCREASE, CONF_DECREASE, CONF_RESET
    ),
)

MANUAL_RUN_SCHEMA = {
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_TIME): cv.positive_time_period,
    vol.Optional(CONF_ZONES): cv.ensure_list,
    vol.Optional(CONF_SEQUENCE_ID): cv.positive_int,
}

RELOAD_SERVICE_SCHEMA = vol.Schema({})


@callback
async def async_entity_service_handler(entity: IUEntity, call: ServiceCall) -> None:
    entity.dispatch(call.service, call)


def register_platform_services(platform: entity_platform.EntityPlatform) -> None:
    platform.async_register_entity_service(
        SERVICE_ENABLE, ENTITY_SCHEMA, async_entity_service_handler
    )
    platform.async_register_entity_service(
        SERVICE_DISABLE, ENTITY_SCHEMA, async_entity_service_handler
    )
    platform.async_register_entity_service(
        SERVICE_TOGGLE, ENTITY_SCHEMA, async_entity_service_handler
    )
    platform.async_register_entity_service(
        SERVICE_CANCEL, ENTITY_SCHEMA, async_entity_service_handler
    )
    platform.async_register_entity_service(
        SERVICE_TIME_ADJUST, TIME_ADJUST_SCHEMA, async_entity_service_handler
    )
    platform.async_register_entity_service(
        SERVICE_MANUAL_RUN, MANUAL_RUN_SCHEMA, async_entity_service_handler
    )
    return


def register_component_services(
    component: EntityComponent, coordinator: IUCoordinator
) -> None:
    @callback
    async def reload_service_handler(call: ServiceCall) -> None:
        """Reload yaml entities."""
        conf = await component.async_prepare_reload(skip_reset=True)
        if conf is None or conf == {}:
            conf = {DOMAIN: {}}
        coordinator.load(conf[DOMAIN])
        coordinator.start()
        return

    async_register_admin_service(
        component.hass,
        DOMAIN,
        SERVICE_RELOAD,
        reload_service_handler,
        schema=RELOAD_SERVICE_SCHEMA,
    )
    return
