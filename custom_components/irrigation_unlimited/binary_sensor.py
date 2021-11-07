"""Binary sensor platform for irrigation_unlimited."""
from datetime import datetime, timedelta
import json
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity_platform import (
    EntityPlatform,
    current_platform,
    async_get_platforms,
)
import homeassistant.util.dt as dt
from homeassistant.const import MAJOR_VERSION, MINOR_VERSION

from .irrigation_unlimited import IUCoordinator
from .entity import IUEntity
from .service import register_platform_services
from .const import (
    ATTR_ENABLED,
    ATTR_STATUS,
    ATTR_INDEX,
    BINARY_SENSOR,
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

if MAJOR_VERSION >= 2021 and MINOR_VERSION >= 6:
    from homeassistant.components.recorder import history
else:
    from homeassistant.components import history

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
ATTR_NEXT_SCHEDULE = "next_schedule"
ATTR_NEXT_ZONE = "next_zone"
ATTR_NEXT_NAME = "next_name"
ATTR_NEXT_ADJUSTMENT = "next_adjustment"
ATTR_NEXT_START = "next_start"
ATTR_NEXT_DURATION = "next_duration"
ATTR_TIME_REMAINING = "time_remaining"
ATTR_PERCENT_COMPLETE = "percent_complete"
ATTR_ZONE_COUNT = "zone_count"
ATTR_CURRENT_ZONE = "current_zone"
ATTR_TOTAL_TODAY = "today_total"
ATTR_SCHEDULE_COUNT = "schedule_count"
ATTR_ADJUSTMENT = "adjustment"
ATTR_CONFIGURATION = "configuration"
ATTR_TIMELINE = "timeline"


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
) -> None:
    """Setup binary_sensor platform."""
    # pylint: disable=unused-argument

    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]
    entities = []
    for controller in coordinator.controllers:
        entities.append(IUMasterEntity(coordinator, controller, None))
        for zone in controller.zones:
            entities.append(IUZoneEntity(coordinator, controller, zone))
    async_add_entities(entities)

    platform = current_platform.get()
    register_platform_services(platform)

    return


async def async_reload_platform(
    component: EntityComponent, coordinator: IUCoordinator
) -> None:
    """Handle the reloading of this platform"""

    def find_platform(hass: HomeAssistant, name: str) -> EntityPlatform:
        platforms = async_get_platforms(hass, DOMAIN)
        for platform in platforms:
            if platform.domain == name:
                return platform
        return None

    def remove_entity(entities: "dict[Entity]", entity_id: str) -> bool:
        entity_id = f"{BINARY_SENSOR}.{DOMAIN}_{entity_id}"
        if entity_id in entities:
            entities.pop(entity_id)
            return True
        return False

    platform = find_platform(component.hass, BINARY_SENSOR)
    if platform is not None:
        old_entities: dict[Entity] = platform.entities.copy()
        new_entities: list[Entity] = []

        for controller in coordinator.controllers:
            if not remove_entity(old_entities, controller.unique_id):
                new_entities.append(IUMasterEntity(coordinator, controller, None))
            for zone in controller.zones:
                if not remove_entity(old_entities, zone.unique_id):
                    new_entities.append(IUZoneEntity(coordinator, controller, zone))
        if len(new_entities) > 0:
            await platform.async_add_entities(new_entities)
            coordinator.initialise()
        for entity in old_entities:
            await platform.async_remove_entity(entity)
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
    """Return the total on time for today"""
    start = midnight(time)
    return on_duration(hass, start, time, entity_id)


class IUMasterEntity(IUEntity):
    """irrigation_unlimited controller binary_sensor class."""

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._controller.unique_id

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
            if self._controller.is_paused:
                return ICON_CONTROLLER_PAUSED
            return ICON_CONTROLLER_OFF
        return ICON_DISABLED

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}
        attr[ATTR_INDEX] = self._controller.index
        attr[ATTR_ENABLED] = self._controller.enabled
        attr[ATTR_STATUS] = self._controller.status
        attr[ATTR_ZONE_COUNT] = len(self._controller.zones)
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
            attr[ATTR_CURRENT_SCHEDULE] = "deprecated (use current_zone)"
            attr[ATTR_CURRENT_ZONE] = RES_NOT_RUNNING
            attr[ATTR_PERCENT_COMPLETE] = 0

        next_run = self._controller.runs.next_run
        if next_run is not None:
            attr[ATTR_NEXT_ZONE] = next_run.zone.index + 1
            attr[ATTR_NEXT_NAME] = next_run.zone.name
            attr[ATTR_NEXT_START] = dt.as_local(next_run.start_time)
            attr[ATTR_NEXT_DURATION] = str(next_run.duration)
        else:
            attr[ATTR_NEXT_SCHEDULE] = "deprecated (use next_zone)"
            attr[ATTR_NEXT_ZONE] = RES_NONE
        return attr


class IUZoneEntity(IUEntity):
    """irrigation_unlimited zone binary_sensor class."""

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._zone.unique_id

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
        """Indicate that we need to poll data"""
        return False

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        if self._controller.enabled:
            if self._zone.enabled:
                if self._zone.is_on:
                    return ICON_ON
                return ICON_OFF
            return ICON_DISABLED
        return ICON_BLOCKED

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        # pylint: disable=too-many-branches
        attr = {}
        attr[CONF_ZONE_ID] = self._zone.zone_id
        attr[ATTR_INDEX] = self._zone.index
        attr[ATTR_ENABLED] = self._zone.enabled
        attr[ATTR_STATUS] = self._zone.status
        attr[ATTR_SCHEDULE_COUNT] = len(self._zone.schedules)
        attr[CONF_SCHEDULES] = ""
        attr[ATTR_ADJUSTMENT] = str(self._zone.adjustment)
        current = self._zone.runs.current_run
        if current is not None:
            if current.schedule is not None:
                attr[ATTR_CURRENT_SCHEDULE] = current.schedule.index + 1
                attr[ATTR_CURRENT_NAME] = current.schedule.name
                if current.sequence_has_adjustment(True):
                    attr[ATTR_CURRENT_ADJUSTMENT] = current.sequence_adjustment()
                else:
                    attr[ATTR_CURRENT_ADJUSTMENT] = str(self._zone.adjustment)
            else:
                attr[ATTR_CURRENT_SCHEDULE] = RES_MANUAL
                attr[ATTR_CURRENT_NAME] = RES_MANUAL
                attr[ATTR_CURRENT_ADJUSTMENT] = RES_NONE
            attr[ATTR_CURRENT_START] = dt.as_local(current.start_time)
            attr[ATTR_CURRENT_DURATION] = str(current.duration)
            attr[ATTR_TIME_REMAINING] = str(current.time_remaining)
            attr[ATTR_PERCENT_COMPLETE] = current.percent_complete
        else:
            attr[ATTR_CURRENT_SCHEDULE] = RES_NOT_RUNNING
            attr[ATTR_PERCENT_COMPLETE] = 0

        next_run = self._zone.runs.next_run
        if next_run is not None:
            if next_run.schedule is not None:
                attr[ATTR_NEXT_SCHEDULE] = next_run.schedule.index + 1
                attr[ATTR_NEXT_NAME] = next_run.schedule.name
            else:
                attr[ATTR_NEXT_SCHEDULE] = RES_MANUAL
                attr[ATTR_NEXT_NAME] = RES_MANUAL
            attr[ATTR_NEXT_START] = dt.as_local(next_run.start_time)
            attr[ATTR_NEXT_DURATION] = str(next_run.duration)
            if next_run.sequence_has_adjustment(True):
                attr[ATTR_NEXT_ADJUSTMENT] = next_run.sequence_adjustment()
            else:
                attr[ATTR_NEXT_ADJUSTMENT] = str(self._zone.adjustment)
        else:
            attr[ATTR_NEXT_SCHEDULE] = RES_NONE
        attr[ATTR_TOTAL_TODAY] = round(
            today_on_duration(
                self.hass, self.entity_id, self._coordinator.service_time()
            ).total_seconds()
            / 60,
            1,
        )
        if self._zone.show_config:
            attr[ATTR_CONFIGURATION] = json.dumps(self._zone.as_dict(), default=str)
        if self._zone.show_timeline:
            attr[ATTR_TIMELINE] = json.dumps(self._zone.runs.as_list(), default=str)
        return attr
