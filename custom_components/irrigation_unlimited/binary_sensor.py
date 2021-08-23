"""Binary sensor platform for irrigation_unlimited."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
import homeassistant.util.dt as dt
from datetime import datetime, timedelta
from homeassistant.const import MAJOR_VERSION, MINOR_VERSION

if MAJOR_VERSION >= 2021 and MINOR_VERSION >= 6:
    from homeassistant.components.recorder import history
else:
    from homeassistant.components import history

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
    CONF_SCHEDULES,
    CONF_ZONES,
    CONF_ZONE_ID,
)

RES_MANUAL = "Manual"
RES_NOT_RUNNING = "not running"
RES_NONE = "none"
RES_CONTROLLER = "Controller"
RES_ZONE = "Zone"
RES_MASTER = "Master"

ATTR_CURRENT_SCHEDULE = "current_schedule"
ATTR_CURRENT_NAME = "current_name"
ATTR_CURRENT_ADJUSTMENT = "current_adjustment"
ATTR_CURRENT_START = "current_start"
ATTR_CURRENT_DURATION = "current_duration"
ATTR_TIME_REMAINING = "time_remaining"
ATTR_PERCENT_COMPLETE = "percent_complete"
ATTR_ZONE_COUNT = "zone_count"
ATTR_CURRENT_ZONE = "current_zone"
ATTR_TOTAL_TODAY = "today_total"


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

    elapsed = timedelta(0)
    current_state: str = None
    current_time: datetime = None

    if len(history_list) > 0:
        if entity_id in history_list:
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


def today_on_duration(hass: HomeAssistant, entity_id: str, time: datetime) -> timedelta:
    start = midnight(time)
    return on_duration(hass, start, time, entity_id)


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
        attr[ATTR_ZONE_COUNT] = len(self._controller._zones)
        attr[CONF_ZONES] = ""
        current = self._controller.runs.current_run
        if current is not None:
            attr[ATTR_CURRENT_ZONE] = current.zone.index + 1
            attr[ATTR_CURRENT_NAME] = current.zone.name
            attr[ATTR_CURRENT_START] = dt.as_local(current.start_time)
            attr[ATTR_CURRENT_DURATION] = str(current.duration)
            attr[ATTR_TIME_REMAINING] = str(current.time_remaining)
            attr[ATTR_PERCENT_COMPLETE] = current.percent_complete
        else:
            attr["current_schedule"] = "deprecated (use current_zone)"
            attr[ATTR_CURRENT_ZONE] = RES_NOT_RUNNING
            attr[ATTR_PERCENT_COMPLETE] = 0

        next = self._controller.runs.next_run
        if next is not None:
            attr["next_zone"] = next.zone.index + 1
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
        attr[CONF_ZONE_ID] = self._zone.zone_id
        attr[ATTR_INDEX] = self._zone.index
        attr[ATTR_ENABLED] = self._zone.enabled
        attr[ATTR_STATUS] = self._zone.status
        attr["schedule_count"] = len(self._zone.schedules)
        attr[CONF_SCHEDULES] = ""
        attr["adjustment"] = str(self._zone.adjustment)
        current = self._zone.runs.current_run
        if current is not None:
            if current.schedule is not None:
                attr[ATTR_CURRENT_SCHEDULE] = current.schedule.index + 1
                attr[ATTR_CURRENT_NAME] = current.schedule.name
                if current.is_sequence and current.sequence.adjustment.has_adjustment:
                    attr[ATTR_CURRENT_ADJUSTMENT] = str(current.sequence.adjustment)
                else:
                    attr[ATTR_CURRENT_ADJUSTMENT] = str(self._zone.adjustment)
            else:
                attr[ATTR_CURRENT_SCHEDULE] = RES_MANUAL
                attr[ATTR_CURRENT_NAME] = RES_MANUAL
                attr[ATTR_CURRENT_ADJUSTMENT] = "None"
            attr[ATTR_CURRENT_START] = dt.as_local(current.start_time)
            attr[ATTR_CURRENT_DURATION] = str(current.duration)
            attr[ATTR_TIME_REMAINING] = str(current.time_remaining)
            attr[ATTR_PERCENT_COMPLETE] = current.percent_complete
        else:
            attr[ATTR_CURRENT_SCHEDULE] = RES_NOT_RUNNING
            attr[ATTR_PERCENT_COMPLETE] = 0

        next = self._zone.runs.next_run
        if next is not None:
            if next.schedule is not None:
                attr["next_schedule"] = next.schedule.index + 1
                attr["next_name"] = next.schedule.name
            else:
                attr["next_schedule"] = RES_MANUAL
                attr["next_name"] = RES_MANUAL
            attr["next_start"] = dt.as_local(next.start_time)
            attr["next_duration"] = str(next.duration)
            if next.is_sequence and next.sequence.adjustment.has_adjustment:
                attr["next_adjustment"] = str(next.sequence.adjustment)
            else:
                attr["next_adjustment"] = str(self._zone.adjustment)
        else:
            attr["next_schedule"] = RES_NONE
        attr[ATTR_TOTAL_TODAY] = round(
            today_on_duration(
                self.hass, self.entity_id, self._coordinator.service_time()
            ).total_seconds()
            / 60,
            1,
        )
        if self._zone.show_config:
            attr["configuration"] = json.dumps(self._zone.as_dict(), default=str)
        if self._zone.show_timeline:
            attr["timeline"] = json.dumps(self._zone.runs.as_list(), default=str)
        return attr
