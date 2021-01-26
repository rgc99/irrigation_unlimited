"""Binary sensor platform for irrigation_unlimited."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import Entity
from homeassistant.helpers import entity_platform
from homeassistant.helpers import config_validation as cv
from homeassistant.core import ServiceCall
import voluptuous as vol

from .irrigation_unlimited import (
    IUCoordinator,
    IUController,
    IUZone,
)

from homeassistant.const import (
    CONF_ENTITY_ID,
)

from .const import (
    BINARY_SENSOR,
    DOMAIN,
    COORDINATOR,
    NAME,
    ICON,
    CONF_PERCENTAGE,
    CONF_ACTUAL,
    CONF_INCREASE,
    CONF_DECREASE,
    CONF_RESET,
    CONF_TIME,
    CONF_MINIMUM,
    CONF_MAXIMUM,
    CONF_ZONES,
)

SERVICE_ENABLE = "enable"
SERVICE_DISABLE = "disable"
SERVICE_TIME_ADJUST = "adjust_time"
SERVICE_MANUAL_RUN = "manual_run"

RES_MANUAL = "Manual"
RES_NOT_RUNNING = "not running"
RES_NONE = "none"
RES_CONTROLLER = "Controller"
RES_ZONE = "Zone"
RES_MASTER = "Master"

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


async def async_enable(entity: Entity, call: ServiceCall):
    if entity.zone is not None:
        entity.zone.enabled = True
    else:
        entity.controller.enabled = True
    return


async def async_disable(entity: Entity, call: ServiceCall):
    if entity.zone is not None:
        entity.zone.enabled = False
    else:
        entity.controller.enabled = False
    return


async def async_time_adjust(entity: Entity, call: ServiceCall):
    if entity.zone is not None:
        entity.zone.service_adjust_time(call.data)
    else:
        entity.controller.service_adjust_time(call.data)
    return


async def async_manual_run(entity: Entity, call: ServiceCall):
    if entity.zone is not None:
        entity.zone.service_manual_run(call.data)
    return


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup binary_sensor platform."""

    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]
    entities = []
    for controller in coordinator._controllers:
        ctl: IUController = controller
        ctl.master_sensor = IUMasterEntity(coordinator, ctl)
        entities.append(ctl.master_sensor)
        for zone in ctl.zones:
            zn: IUZone = zone
            zn.zone_sensor = IUZoneEntity(coordinator, ctl, zn)
            entities.append(zn.zone_sensor)

    async_add_entities(entities)

    platform = entity_platform.current_platform.get()
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


class IUMasterEntity(BinarySensorEntity):
    """irrigation_unlimited controller binary_sensor class."""

    def __init__(
        self,
        coordinator: IUCoordinator,
        controller: IUController,
    ):
        self._coordinator = coordinator
        self._controller = controller
        self._zone: IUZone = None  # Flag we are a master entity
        self.entity_id = (
            f"{BINARY_SENSOR}.{DOMAIN}_c{controller.controller_index + 1}_m"
        )
        return

    @property
    def controller(self) -> IUController:
        return self._controller

    @property
    def zone(self) -> IUZone:
        return self._zone

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"c{self._controller.controller_index + 1}_m"

    @property
    def name(self):
        """Return the name of the binary_sensor."""
        return f"{NAME} {RES_CONTROLLER} {self._controller.controller_index + 1} {RES_MASTER}"

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self._controller.is_on

    @property
    def should_poll(self):
        """Indicate that we nee to poll data"""
        return False

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}
        attr["enabled"] = self._controller.enabled
        attr["zones"] = len(self._controller._zones)
        current = self._controller.runs.current_run
        if current is not None:
            attr["current_zone"] = current.index + 1
            attr["current_name"] = current.zone.name
            attr["current_start"] = current.start_time
            attr["current_duration"] = str(current.duration)
            attr["time_remaining"] = str(current.time_remaining)
        else:
            attr["current_schedule"] = RES_NOT_RUNNING

        next = self._controller.runs.next_run
        if next is not None:
            attr["next_zone"] = next.index + 1
            attr["next_name"] = next.zone.name
            attr["next_start"] = next.start_time
            attr["next_duration"] = str(next.duration)
        else:
            attr["next_schedule"] = RES_NONE

        return attr

    async def async_added_to_hass(self):
        self._controller.master_sensor_issetup = True
        return


class IUZoneEntity(BinarySensorEntity):
    """irrigation_unlimited zone binary_sensor class."""

    def __init__(
        self,
        coordinator: IUCoordinator,
        controller: IUController,
        zone: IUZone,
    ):
        self._coordinator = coordinator
        self._controller = controller
        self._zone = zone
        self.entity_id = f"{BINARY_SENSOR}.{DOMAIN}_c{zone.controller_index + 1}_z{zone.zone_index + 1}"
        return

    @property
    def controller(self) -> IUController:
        return self._controller

    @property
    def zone(self) -> IUZone:
        return self._zone

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"c{self._zone.controller_index + 1}_z{self._zone.zone_index + 1}"

    @property
    def name(self):
        """Return the name of the binary_sensor."""
        return f"{NAME} {RES_CONTROLLER} {self._zone.controller_index + 1} {RES_ZONE} {self._zone.zone_index + 1}"

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self._zone.is_on

    @property
    def should_poll(self):
        """Indicate that we nee to poll data"""
        return False

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}
        attr["enabled"] = self._zone.enabled
        attr["schedules"] = len(self._zone.schedules)
        attr["adjustment"] = self._zone.adjustment.as_string
        current = self._zone.runs.current_run
        if current is not None:
            if current.schedule is not None:
                attr["current_schedule"] = current.schedule.schedule_index + 1
                attr["current_name"] = current.schedule.name
            else:
                attr["current_schedule"] = RES_MANUAL
                attr["current_name"] = RES_MANUAL
            attr["current_start"] = current.start_time
            attr["current_duration"] = str(current.duration)
            attr["time_remaining"] = str(current.time_remaining)
        else:
            attr["current_schedule"] = RES_NOT_RUNNING

        next = self._zone.runs.next_run
        if next is not None:
            if next.schedule is not None:
                attr["next_schedule"] = next.schedule.schedule_index + 1
                attr["next_name"] = next.schedule.name
            else:
                attr["next_schedule"] = RES_MANUAL
                attr["next_name"] = RES_MANUAL
            attr["next_start"] = next.start_time
            attr["next_duration"] = str(next.duration)
        else:
            attr["next_schedule"] = RES_NONE

        return attr

    async def async_added_to_hass(self):
        self._zone.zone_sensor_issetup = True
        return
