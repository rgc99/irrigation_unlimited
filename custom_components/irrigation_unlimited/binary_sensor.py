"""Binary sensor platform for irrigation_unlimited."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
import homeassistant.util.dt as dt
from datetime import datetime, timedelta
from homeassistant.components import history
from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUSchedule,
    IUZone,
)
import json

from homeassistant.const import (
    STATE_ON,
)

from .entity import IUEntity
from .service import register_platform_services
from .const import (
    ATTR_ENABLED,
    ATTR_STATUS,
    ATTR_INDEX,
    DOMAIN,
    COORDINATOR,
    ICON_CONTROLLER_OFF,
    ICON_CONTROLLER_ON,
    ICON_CONTROLLER_PAUSED,
    ICON_OFF,
    ICON_ON,
    ICON_DISABLED,
    ICON_BLOCKED,
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


def on_duration(
    hass: HomeAssistant, start: datetime, end: datetime, entity_id: str
) -> timedelta:
    """Return the total on time between start and end"""
    history_list = history.state_changes_during_period(hass, start, end, entity_id)

    elapsed = timedelta()
    current_state: str = None
    current_time: datetime = None

    if len(history_list) > 0:
        for item in history_list.get(entity_id):

            # Initialise on first pass
            if current_state is None:
                current_state = item.state
                current_time = item.last_changed
                continue

            if current_state == STATE_ON and item.state != STATE_ON:
                elapsed += item.last_changed - current_time

            current_state = item.state
            current_time = item.last_changed

        if current_state == STATE_ON:
            elapsed += end - current_time

    return timedelta(seconds=round(elapsed.total_seconds()))


def midnight(utc: datetime) -> datetime:
    """Accept a UTC time and return midnight for that day"""
    return dt.as_utc(
        dt.as_local(utc).replace(hour=0, minute=0, second=0, microsecond=0)
    )


def today_on_duration(hass: HomeAssistant, entity_id: str) -> timedelta:
    end = dt.utcnow()
    start = midnight(end)
    return on_duration(hass, start, end, entity_id)


class IUMasterEntity(IUEntity):
    """irrigation_unlimited controller binary_sensor class."""

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"c{self._controller.index + 1}_m"

    @property
    def name(self):
        """Return the friendly name of the binary_sensor."""
        return self._controller.name

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
                return ICON_CONTROLLER_ON
            else:
                if self._controller.is_paused:
                    return ICON_CONTROLLER_PAUSED
                else:
                    return ICON_CONTROLLER_OFF
        else:
            return ICON_DISABLED

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}
        attr[ATTR_INDEX] = self._controller.index
        attr[ATTR_ENABLED] = self._controller.enabled
        attr[ATTR_STATUS] = self._controller.status
        attr["zone_count"] = len(self._controller._zones)
        attr["zones"] = ""
        current = self._controller.runs.current_run
        if current is not None:
            if isinstance(current.parent, IUZone):
                attr["current_zone"] = current.parent.index + 1
                attr["current_name"] = current.parent.name
            attr["current_start"] = dt.as_local(current.start_time)
            attr["current_duration"] = str(current.duration)
            attr["time_remaining"] = str(current.time_remaining)
            attr["percent_complete"] = current.percent_complete
        else:
            attr["current_schedule"] = RES_NOT_RUNNING
            attr["percent_complete"] = 0

        next = self._controller.runs.next_run
        if next is not None:
            if isinstance(next.parent, IUZone):
                attr["next_zone"] = next.parent.index + 1
                attr["next_name"] = next.parent.name
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
        return f"c{self._controller.index + 1}_z{self._zone.index + 1}"

    @property
    def name(self):
        """Return the friendly name of the binary_sensor."""
        return self._zone.name

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
        attr["zone_id"] = self._zone.zone_id
        attr[ATTR_INDEX] = self._zone.index
        attr[ATTR_ENABLED] = self._zone.enabled
        attr[ATTR_STATUS] = self._zone.status
        attr["schedule_count"] = len(self._zone.schedules)
        attr["schedules"] = ""
        attr["adjustment"] = self._zone.adjustment.as_string
        current = self._zone.runs.current_run
        if current is not None:
            if isinstance(current.parent, IUSchedule):
                attr["current_schedule"] = current.parent.index + 1
                attr["current_name"] = current.parent.name
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
            if isinstance(next.parent, IUSchedule):
                attr["next_schedule"] = next.parent.index + 1
                attr["next_name"] = next.parent.name
            else:
                attr["next_schedule"] = RES_MANUAL
                attr["next_name"] = RES_MANUAL
            attr["next_start"] = dt.as_local(next.start_time)
            attr["next_duration"] = str(next.duration)
        else:
            attr["next_schedule"] = RES_NONE
        attr["today_total"] = round(
            today_on_duration(self.hass, self.entity_id).total_seconds() / 60, 1
        )
        if self._zone.show_config:
            attr["configuration"] = json.dumps(self._zone.as_dict(), default=str)
        if self._zone.show_timeline:
            attr["timeline"] = json.dumps(self._zone.runs.as_list(), default=str)
        return attr
