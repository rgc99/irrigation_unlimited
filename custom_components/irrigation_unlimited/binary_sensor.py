"""Binary sensor platform for irrigation_unlimited."""
from homeassistant.helpers import entity_platform
from homeassistant.helpers import config_validation as cv
import homeassistant.util.dt as dt

from .entity import IUEntity
from custom_components.irrigation_unlimited.service import register_platform_services
from .const import (
    DOMAIN,
    COORDINATOR,
    ICON_OFF,
    ICON_ON,
    ICON_DISABLED,
    ICON_BLOCKED,
    NAME,
)

RES_MANUAL = "Manual"
RES_NOT_RUNNING = "not running"
RES_NONE = "none"
RES_CONTROLLER = "Controller"
RES_ZONE = "Zone"
RES_MASTER = "Master"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup binary_sensor platform."""

    coordinator = hass.data[DOMAIN][COORDINATOR]
    entities = []
    for controller in coordinator._controllers:
        entities.append(IUMasterEntity(coordinator, controller, None))
        for zone in controller.zones:
            entities.append(IUZoneEntity(coordinator, controller, zone))
    async_add_entities(entities)

    platform = entity_platform.current_platform.get()
    register_platform_services(platform)

    return


class IUMasterEntity(IUEntity):
    """irrigation_unlimited controller binary_sensor class."""

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
        """Return the icon to use in the frontend."""
        if self._controller.enabled:
            if self._controller.is_on:
                return ICON_ON
            else:
                return ICON_OFF
        else:
            return ICON_DISABLED

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
            attr["current_start"] = dt.as_local(current.start_time)
            attr["current_duration"] = str(current.duration)
            attr["time_remaining"] = str(current.time_remaining)
            attr["percent_complete"] = current.percent_complete
        else:
            attr["current_schedule"] = RES_NOT_RUNNING
            attr["percent_complete"] = 0

        next = self._controller.runs.next_run
        if next is not None:
            attr["next_zone"] = next.index + 1
            attr["next_name"] = next.zone.name
            attr["next_start"] = dt.as_local(next.start_time)
            attr["next_duration"] = str(next.duration)
        else:
            attr["next_schedule"] = RES_NONE

        return attr


class IUZoneEntity(IUEntity):
    """irrigation_unlimited zone binary_sensor class."""

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
        """Return the icon to use in the frontend."""
        if self._controller.enabled:
        if self._zone.enabled:
            if self._zone.is_on:
                return ICON_ON
            else:
                return ICON_OFF
        else:
            return ICON_DISABLED
        else:
            return ICON_BLOCKED

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
            attr["current_start"] = dt.as_local(current.start_time)
            attr["current_duration"] = str(current.duration)
            attr["time_remaining"] = str(current.time_remaining)
            attr["percent_complete"] = current.percent_complete
        else:
            attr["current_schedule"] = RES_NOT_RUNNING
            attr["percent_complete"] = 0

        next = self._zone.runs.next_run
        if next is not None:
            if next.schedule is not None:
                attr["next_schedule"] = next.schedule.schedule_index + 1
                attr["next_name"] = next.schedule.name
            else:
                attr["next_schedule"] = RES_MANUAL
                attr["next_name"] = RES_MANUAL
            attr["next_start"] = dt.as_local(next.start_time)
            attr["next_duration"] = str(next.duration)
        else:
            attr["next_schedule"] = RES_NONE

        return attr
