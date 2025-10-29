"""This module handles the HA service call interface"""

from homeassistant.core import ServiceCall, SupportsResponse, ServiceResponse, callback
from homeassistant.util import dt
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.service import async_register_admin_service

from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_RELOAD,
)

from .irrigation_unlimited import IUCoordinator
from .util import convert_data
from .entity import IUEntity
from .schema import (
    CANCEL_SCHEMA,
    ENABLE_DISABLE_SCHEMA,
    ENTITY_SCHEMA,
    GET_STATUS_SCHEMA,
    LOAD_SCHEDULE_SCHEMA,
    MANUAL_RUN_SCHEMA,
    PAUSE_RESUME_SCHEMA,
    RELOAD_SERVICE_SCHEMA,
    SUSPEND_SCHEMA,
    TIME_ADJUST_SCHEMA,
)

from .const import (
    ATTR_CONTROLLERS,
    ATTR_CONTROLLER_ID,
    ATTR_INDEX,
    ATTR_NAME,
    ATTR_SEQUENCES,
    ATTR_VERSION,
    ATTR_ZONES,
    ATTR_ZONE_ID,
    ATTR_ZONE_IDS,
    CONF_EXTENDED,
    DOMAIN,
    SERVICE_CANCEL,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_GET_INFO,
    SERVICE_GET_STATUS,
    SERVICE_LOAD_SCHEDULE,
    SERVICE_MANUAL_RUN,
    SERVICE_PAUSE,
    SERVICE_RESUME,
    SERVICE_SKIP,
    SERVICE_SUSPEND,
    SERVICE_TIME_ADJUST,
    SERVICE_TOGGLE,
)


@callback
async def async_entity_service_handler(
    entity: IUEntity, call: ServiceCall
) -> ServiceResponse:
    """Dispatch the service call"""
    return entity.dispatch(call.service, call)


def register_platform_services(platform: entity_platform.EntityPlatform) -> None:
    """Register all the available service calls for the entities"""
    platform.async_register_entity_service(
        SERVICE_ENABLE, ENABLE_DISABLE_SCHEMA, async_entity_service_handler
    )
    platform.async_register_entity_service(
        SERVICE_DISABLE, ENABLE_DISABLE_SCHEMA, async_entity_service_handler
    )
    platform.async_register_entity_service(
        SERVICE_TOGGLE, ENABLE_DISABLE_SCHEMA, async_entity_service_handler
    )
    platform.async_register_entity_service(
        SERVICE_CANCEL, CANCEL_SCHEMA, async_entity_service_handler
    )
    platform.async_register_entity_service(
        SERVICE_TIME_ADJUST, TIME_ADJUST_SCHEMA, async_entity_service_handler
    )
    platform.async_register_entity_service(
        SERVICE_MANUAL_RUN, MANUAL_RUN_SCHEMA, async_entity_service_handler
    )
    platform.async_register_entity_service(
        SERVICE_SUSPEND, SUSPEND_SCHEMA, async_entity_service_handler
    )
    platform.async_register_entity_service(
        SERVICE_SKIP, ENTITY_SCHEMA, async_entity_service_handler
    )

    platform.async_register_entity_service(
        SERVICE_PAUSE, PAUSE_RESUME_SCHEMA, async_entity_service_handler
    )

    platform.async_register_entity_service(
        SERVICE_RESUME, PAUSE_RESUME_SCHEMA, async_entity_service_handler
    )


def register_component_services(
    component: EntityComponent, coordinator: IUCoordinator
) -> None:
    """Register the component"""

    @callback
    async def reload_service_handler(call: ServiceCall) -> None:
        """Reload yaml entities."""
        # pylint: disable=unused-argument
        # pylint: disable=import-outside-toplevel
        from .binary_sensor import async_reload_platform

        conf = await component.async_prepare_reload(skip_reset=True)
        if conf is None or conf == {}:
            conf = {DOMAIN: {}}
        coordinator.load(conf[DOMAIN])
        await async_reload_platform(component, coordinator)
        coordinator.timer(dt.utcnow())
        coordinator.clock.start()

    async_register_admin_service(
        component.hass,
        DOMAIN,
        SERVICE_RELOAD,
        reload_service_handler,
        schema=RELOAD_SERVICE_SCHEMA,
    )

    @callback
    async def coordinator_service_handler(call: ServiceCall) -> ServiceResponse:
        """Reload schedule."""
        return coordinator.service_call(call.service, None, None, None, call.data)

    component.hass.services.async_register(
        DOMAIN,
        SERVICE_LOAD_SCHEDULE,
        coordinator_service_handler,
        LOAD_SCHEDULE_SCHEMA,
    )

    @callback
    async def get_info_service_handler(call: ServiceCall) -> ServiceResponse:
        """Return configuration"""
        # pylint: disable=unused-argument
        data = {}
        data[ATTR_VERSION] = "1.0.0"
        data[ATTR_CONTROLLERS] = [
            {
                ATTR_INDEX: ctl.index,
                ATTR_CONTROLLER_ID: ctl.controller_id,
                ATTR_NAME: ctl.name,
                ATTR_ENTITY_ID: ctl.entity_id,
                ATTR_ZONES: [
                    {
                        ATTR_INDEX: zone.index,
                        ATTR_ZONE_ID: zone.zone_id,
                        ATTR_NAME: zone.name,
                        ATTR_ENTITY_ID: zone.entity_id,
                    }
                    for zone in ctl.zones
                ],
                ATTR_SEQUENCES: [
                    {
                        ATTR_INDEX: seq.index,
                        ATTR_NAME: seq.name,
                        ATTR_ENTITY_ID: seq.entity_id,
                        ATTR_ZONES: [
                            {ATTR_INDEX: sqz.index, ATTR_ZONE_IDS: sqz.zone_ids}
                            for sqz in seq.zones
                        ],
                    }
                    for seq in ctl.sequences
                ],
            }
            for ctl in coordinator.controllers
        ]
        return data

    component.hass.services.async_register(
        DOMAIN,
        SERVICE_GET_INFO,
        get_info_service_handler,
        {},
        supports_response=SupportsResponse.ONLY,
    )

    @callback
    async def get_status_service_handler(call: ServiceCall) -> ServiceResponse:
        """Return configuration"""
        # pylint: disable=unused-argument

        return convert_data(
            coordinator.as_dict(extended=call.data.get(CONF_EXTENDED, False))
        )

    component.hass.services.async_register(
        DOMAIN,
        SERVICE_GET_STATUS,
        get_status_service_handler,
        GET_STATUS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
