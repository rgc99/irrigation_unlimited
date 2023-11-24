"""Irrigation Unlimited Coordinator and sub classes"""
# pylint: disable=too-many-lines
import weakref
from datetime import datetime, time, timedelta, timezone, date
from collections import deque
from types import MappingProxyType
from typing import OrderedDict, NamedTuple, Callable, Awaitable
from logging import WARNING, Logger, getLogger, INFO, DEBUG, ERROR
import uuid
import time as tm
import json
from enum import Enum, Flag, auto
import voluptuous as vol
from crontab import CronTab
from homeassistant.core import (
    HomeAssistant,
    HassJob,
    CALLBACK_TYPE,
    DOMAIN as HADOMAIN,
    Event as HAEvent,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.template import Template, render_complex
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_call_later,
    async_track_state_change_event,
)
from homeassistant.helpers import sun
from homeassistant.util import dt
from homeassistant.helpers import config_validation as cv

from homeassistant.const import (
    ATTR_ICON,
    CONF_AFTER,
    CONF_BEFORE,
    CONF_DELAY,
    CONF_ENTITY_ID,
    CONF_ICON,
    CONF_NAME,
    CONF_REPEAT,
    CONF_STATE,
    CONF_WEEKDAY,
    EVENT_HOMEASSISTANT_STOP,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    WEEKDAYS,
    ATTR_ENTITY_ID,
    CONF_FOR,
    CONF_UNTIL,
)

from .history import IUHistory

from .const import (
    ATTR_ADJUSTED_DURATION,
    ATTR_ADJUSTMENT,
    ATTR_BASE_DURATION,
    ATTR_CURRENT_DURATION,
    ATTR_DEFAULT_DELAY,
    ATTR_DEFAULT_DURATION,
    ATTR_DURATION,
    ATTR_DURATION_FACTOR,
    ATTR_ENABLED,
    ATTR_FINAL_DURATION,
    ATTR_INDEX,
    ATTR_NAME,
    ATTR_SCHEDULE,
    ATTR_START,
    ATTR_STATUS,
    ATTR_SWITCH_ENTITIES,
    ATTR_TOTAL_DELAY,
    ATTR_TOTAL_DURATION,
    ATTR_ZONE_IDS,
    ATTR_ZONES,
    ATTR_SUSPENDED,
    BINARY_SENSOR,
    CONF_ACTUAL,
    CONF_ALL_ZONES_CONFIG,
    CONF_ALLOW_MANUAL,
    CONF_CLOCK,
    CONF_CONTROLLER,
    CONF_ZONE,
    CONF_MODE,
    CONF_RENAME_ENTITIES,
    CONF_ENTITY_BASE,
    CONF_RUN,
    CONF_SYNC_SWITCHES,
    DOMAIN,
    CONF_DAY,
    CONF_DECREASE,
    CONF_FINISH,
    CONF_INCREASE,
    CONF_INDEX,
    CONF_LOGGING,
    CONF_OUTPUT_EVENTS,
    CONF_PERCENTAGE,
    CONF_REFRESH_INTERVAL,
    CONF_RESET,
    CONF_RESULTS,
    CONF_SCHEDULE,
    CONF_SEQUENCE,
    CONF_SEQUENCE_ZONES,
    CONF_SEQUENCES,
    CONF_SEQUENCE_ID,
    CONF_SHOW_LOG,
    CONF_AUTOPLAY,
    CONF_ANCHOR,
    CONF_VERSION,
    COORDINATOR,
    DEFAULT_GRANULARITY,
    DEFAULT_REFRESH_INTERVAL,
    DEFAULT_TEST_SPEED,
    CONF_DURATION,
    CONF_ENABLED,
    CONF_GRANULARITY,
    CONF_TIME,
    CONF_SUN,
    CONF_PREAMBLE,
    CONF_POSTAMBLE,
    CONF_TESTING,
    CONF_SPEED,
    CONF_TIMES,
    CONF_START,
    CONF_END,
    CONF_CONTROLLERS,
    CONF_SCHEDULES,
    CONF_ZONES,
    CONF_MINIMUM,
    CONF_MAXIMUM,
    CONF_MONTH,
    EVENT_START,
    EVENT_FINISH,
    ICON_BLOCKED,
    ICON_CONTROLLER_OFF,
    ICON_CONTROLLER_ON,
    ICON_CONTROLLER_PAUSED,
    ICON_DISABLED,
    ICON_SUSPENDED,
    ICON_SEQUENCE_PAUSED,
    ICON_SEQUENCE_ZONE_OFF,
    ICON_SEQUENCE_ZONE_ON,
    ICON_ZONE_OFF,
    ICON_ZONE_ON,
    ICON_SEQUENCE_OFF,
    ICON_SEQUENCE_ON,
    RES_MANUAL,
    RES_TIMELINE_HISTORY,
    RES_TIMELINE_NEXT,
    RES_TIMELINE_RUNNING,
    RES_TIMELINE_SCHEDULED,
    TIMELINE_ADJUSTMENT,
    TIMELINE_END,
    TIMELINE_SCHEDULE_NAME,
    TIMELINE_START,
    MONTHS,
    CONF_ODD,
    CONF_EVEN,
    CONF_SHOW,
    CONF_CONFIG,
    CONF_TIMELINE,
    CONF_CONTROLLER_ID,
    CONF_ZONE_ID,
    CONF_FUTURE_SPAN,
    SERVICE_CANCEL,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_TOGGLE,
    SERVICE_MANUAL_RUN,
    SERVICE_TIME_ADJUST,
    SERVICE_LOAD_SCHEDULE,
    SERVICE_SUSPEND,
    STATUS_BLOCKED,
    STATUS_PAUSED,
    STATUS_DISABLED,
    STATUS_SUSPENDED,
    STATUS_INITIALISING,
    TIMELINE_STATUS,
    CONF_FIXED,
    CONF_MAX_LOG_ENTRIES,
    DEFAULT_MAX_LOG_ENTRIES,
    CONF_CRON,
    CONF_EVERY_N_DAYS,
    CONF_START_N_DAYS,
    CONF_CHECK_BACK,
    CONF_STATES,
    CONF_RETRIES,
    CONF_RESYNC,
    EVENT_SYNC_ERROR,
    EVENT_SWITCH_ERROR,
    CONF_EXPECTED,
    CONF_STATE_ON,
    CONF_STATE_OFF,
    CONF_SCHEDULE_ID,
    CONF_FROM,
    CONF_VOLUME,
    CONF_PRECISION,
    CONF_QUEUE,
    CONF_QUEUE_MANUAL,
    CONF_USER,
    CONF_TOGGLE,
)

_LOGGER: Logger = getLogger(__package__)


# Useful time manipulation routine
def time_to_timedelta(offset: time) -> timedelta:
    """Create a timedelta from a time object"""
    return datetime.combine(datetime.min, offset) - datetime.min


def dt2lstr(stime: datetime) -> str:
    """Format the passed UTC datetime into a local date time string. The result
    is formatted to 24 hour time notation (YYYY-MM-DD HH:MM:SS).
    Example 2021-12-25 17:00:00 for 5pm on December 25 2021."""
    return datetime.strftime(dt.as_local(stime), "%Y-%m-%d %H:%M:%S")


def to_secs(atime: timedelta) -> int:
    """Convert the supplied time to whole seconds"""
    return round(atime.total_seconds())


# These routines truncate dates, times and deltas to the internal
# granularity. This should be no more than 1 minute and realistically
# no less than 1 second i.e. 1 >= GRANULARITY <= 60
# The current boundaries are whole minutes (60 seconds).
SYSTEM_GRANULARITY: int = DEFAULT_GRANULARITY  # Granularity in seconds


def reset_granularity() -> None:
    """Restore the original granularity"""
    global SYSTEM_GRANULARITY  # pylint: disable=global-statement
    SYSTEM_GRANULARITY = DEFAULT_GRANULARITY


def granularity_time() -> timedelta:
    """Return the system granularity as a timedelta"""
    return timedelta(seconds=SYSTEM_GRANULARITY)


def wash_td(delta: timedelta, granularity: int = None) -> timedelta:
    """Truncate the supplied timedelta to internal boundaries"""
    if delta is not None:
        if granularity is None:
            granularity = SYSTEM_GRANULARITY
        whole_seconds = int(delta.total_seconds())
        rounded_seconds = int(whole_seconds / granularity) * granularity
        return timedelta(seconds=rounded_seconds)
    return None


def wash_dt(value: datetime, granularity: int = None) -> datetime:
    """Truncate the supplied datetime to internal boundaries"""
    if value is not None:
        if granularity is None:
            granularity = SYSTEM_GRANULARITY
        rounded_seconds = int(value.second / granularity) * granularity
        return value.replace(second=rounded_seconds, microsecond=0)
    return None


def wash_t(stime: time, granularity: int = None) -> time:
    """Truncate the supplied time to internal boundaries"""
    if stime is not None:
        if granularity is None:
            granularity = SYSTEM_GRANULARITY
        utc = dt.utcnow()
        full_date = utc.combine(utc.date(), stime)
        rounded_seconds = int(full_date.second / granularity) * granularity
        return full_date.replace(second=rounded_seconds, microsecond=0).timetz()
    return None


def round_dt(stime: datetime, granularity: int = None) -> datetime:
    """Round the supplied datetime to internal boundaries"""
    if stime is not None:
        base_time = wash_dt(stime, granularity)
        return base_time + round_td(stime - base_time, granularity)
    return None


def round_td(delta: timedelta, granularity: int = None) -> timedelta:
    """Round the supplied timedelta to internal boundaries"""
    if delta is not None:
        if granularity is None:
            granularity = SYSTEM_GRANULARITY
        rounded_seconds = (
            int((delta.total_seconds() + granularity / 2) / granularity) * granularity
        )
        return timedelta(seconds=rounded_seconds)
    return None


def str_to_td(atime: str) -> timedelta:
    """Convert a string in 0:00:00 format to timedelta"""
    dur = datetime.strptime(atime, "%H:%M:%S")
    return timedelta(hours=dur.hour, minutes=dur.minute, seconds=dur.second)


def utc_eot() -> datetime:
    """Return the end of time in UTC format"""
    return datetime.max.replace(tzinfo=timezone.utc)


def render_positive_time_period(data: dict, key: str) -> None:
    """Resolve a template that specifies a timedelta"""
    if key in data:
        schema = vol.Schema({key: cv.positive_time_period})
        rendered = render_complex(data[key])
        data[key] = schema({key: rendered})[key]


def render_positive_float(hass: HomeAssistant, data: dict, key: str) -> None:
    """Resolve a template that specifies a float"""
    if isinstance(data.get(key), Template):
        template: Template = data[key]
        template.hass = hass
        schema = vol.Schema({key: cv.positive_float})
        data[key] = schema({key: template.async_render()})[key]


class IUJSONEncoder(json.JSONEncoder):
    """JSON serialiser to handle ISO datetime output"""

    def default(self, o):
        if isinstance(o, datetime):
            return dt.as_local(o).isoformat()
        if isinstance(o, timedelta):
            return round(o.total_seconds())
        return str(o)


class IUBase:
    """Irrigation Unlimited base class"""

    def __init__(self, index: int) -> None:
        # Private variables
        self._uid: int = uuid.uuid4().int
        self._index: int = index

    def __eq__(self, other) -> bool:
        return isinstance(other, IUBase) and self._uid == other._uid

    def __hash__(self) -> int:
        return self._uid

    @property
    def index(self) -> int:
        """Return position within siblings"""
        return self._index

    @property
    def id1(self) -> int:
        """Return the 1's based index"""
        return self._index + 1

    @staticmethod
    def ids(obj: "IUBase", default: str = "", offset: int = 0) -> str:
        """Return the index as a str"""
        if isinstance(obj, IUBase):
            return str(obj.index + offset)
        return default

    @staticmethod
    def idl(obj: "list[IUBase]", default: str = "", offset: int = 0) -> "list[str]":
        """Return a list of indexes"""
        result = []
        for item in obj:
            result.append(IUBase.ids(item, default, offset))
        return result


class IUAdjustment:
    """Irrigation Unlimited class to handle run time adjustment"""

    def __init__(self, adjustment: str = None) -> None:
        self._method: str = None
        self._time_adjustment = None
        self._minimum: timedelta = None
        self._maximum: timedelta = None
        if (
            adjustment is not None
            and isinstance(adjustment, str)
            and len(adjustment) >= 2
        ):
            method = adjustment[0]
            adj = adjustment[1:]
            if method == "=":
                self._method = CONF_ACTUAL
                self._time_adjustment = wash_td(str_to_td(adj))
            elif method == "%":
                self._method = CONF_PERCENTAGE
                self._time_adjustment = float(adj)
            elif method == "+":
                self._method = CONF_INCREASE
                self._time_adjustment = wash_td(str_to_td(adj))
            elif method == "-":
                self._method = CONF_DECREASE
                self._time_adjustment = wash_td(str_to_td(adj))

    def __str__(self) -> str:
        """Return the adjustment as a string notation"""
        if self._method == CONF_ACTUAL:
            return f"={self._time_adjustment}"
        if self._method == CONF_PERCENTAGE:
            return f"%{self._time_adjustment}"
        if self._method == CONF_INCREASE:
            return f"+{self._time_adjustment}"
        if self._method == CONF_DECREASE:
            return f"-{self._time_adjustment}"
        return ""

    @property
    def has_adjustment(self) -> bool:
        """Return True if an adjustment is in play"""
        return self._method is not None

    def load(self, data: MappingProxyType) -> bool:
        """Read the adjustment configuration. Return true if anything has changed"""

        # Save current settings
        old_method = self._method
        old_time_adjustment = self._time_adjustment
        old_minimum = self._minimum
        old_maximum = self._maximum

        if CONF_ACTUAL in data:
            self._method = CONF_ACTUAL
            self._time_adjustment = wash_td(data.get(CONF_ACTUAL))
        elif CONF_PERCENTAGE in data:
            self._method = CONF_PERCENTAGE
            self._time_adjustment = data.get(CONF_PERCENTAGE)
        elif CONF_INCREASE in data:
            self._method = CONF_INCREASE
            self._time_adjustment = wash_td(data.get(CONF_INCREASE))
        elif CONF_DECREASE in data:
            self._method = CONF_DECREASE
            self._time_adjustment = wash_td(data.get(CONF_DECREASE))
        elif CONF_RESET in data:
            self._method = None
            self._time_adjustment = None
            self._minimum = None
            self._maximum = None

        self._minimum = wash_td(data.get(CONF_MINIMUM, None))
        if self._minimum is not None:
            self._minimum = max(self._minimum, granularity_time())  # Set floor

        self._maximum = wash_td(data.get(CONF_MAXIMUM, None))

        return (
            self._method != old_method
            or self._time_adjustment != old_time_adjustment
            or self._minimum != old_minimum
            or self._maximum != old_maximum
        )

    def adjust(self, stime: timedelta) -> timedelta:
        """Return the adjusted time"""
        new_time: timedelta

        if self._method is None:
            new_time = stime
        elif self._method == CONF_ACTUAL:
            new_time = self._time_adjustment
        elif self._method == CONF_PERCENTAGE:
            new_time = round_td(stime * self._time_adjustment / 100)
        elif self._method == CONF_INCREASE:
            new_time = stime + self._time_adjustment
        elif self._method == CONF_DECREASE:
            new_time = stime - self._time_adjustment
        else:
            new_time = stime

        if self._minimum is not None:
            new_time = max(new_time, self._minimum)

        if self._maximum is not None:
            new_time = min(new_time, self._maximum)

        return new_time

    def to_str(self) -> str:
        """Return this adjustment as string or None if empty"""
        if self._method is not None:
            return str(self)
        return "None"

    def to_dict(self) -> dict:
        """Return this adjustment as a dict"""
        result = {}
        if self._method is not None:
            result[self._method] = self._time_adjustment
        if self._minimum is not None:
            result[CONF_MINIMUM] = self._minimum
        if self._maximum is not None:
            result[CONF_MAXIMUM] = self._maximum
        return result


class IURQStatus(Flag):
    """Define the return status of the run queues"""

    NONE = 0
    CLEARED = auto()
    EXTENDED = auto()
    REDUCED = auto()
    SORTED = auto()
    UPDATED = auto()
    CANCELED = auto()
    CHANGED = auto()

    def is_empty(self) -> bool:
        """Return True if there are no flags set"""
        return self.value == 0

    def has_any(self, other: "IURQStatus") -> bool:
        """Return True if the intersect is not empty"""
        return other.value & self.value != 0


class IUUser(dict):
    """Class to hold arbitrary static user information"""

    def load(self, config: OrderedDict, all_zones: OrderedDict):
        """Load info data from the configuration"""

        def load_params(config: OrderedDict) -> None:
            if config is None:
                return
            for key, data in config.items():
                self[f"{CONF_USER}_{key}"] = data

        self.clear()
        if all_zones is not None:
            load_params(all_zones.get(CONF_USER))
        load_params(config.get(CONF_USER))


class IUSchedule(IUBase):
    """Irrigation Unlimited Schedule class. Schedules are not actual
    points in time but describe a future event i.e. next Monday at
    sunrise"""

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: "IUCoordinator",
        schedule_index: int,
    ) -> None:
        super().__init__(schedule_index)
        # Passed parameters
        self._hass = hass
        self._coordinator = coordinator
        # Config parameters
        self._schedule_id: str = None
        self._time = None
        self._duration: timedelta = None
        self._name: str = None
        self._weekdays: list[int] = None
        self._months: list[int] = None
        self._days = None
        self._anchor: str = None
        self._from: date = None
        self._until: date = None
        self._enabled = True
        # Private variables

    @property
    def schedule_id(self) -> str:
        """Return the unique id for this schedule"""
        return self._schedule_id

    @property
    def name(self) -> str:
        """Return the friendly name of this schedule"""
        return self._name

    @property
    def is_setup(self) -> bool:
        """Return True if this schedule is setup"""
        return True

    @property
    def duration(self) -> timedelta:
        """Return the duration"""
        return self._duration

    @property
    def enabled(self) -> bool:
        """Return enabled status"""
        return self._enabled

    def load(self, config: OrderedDict, update: bool = False) -> "IUSchedule":
        """Load schedule data from config"""
        if not update:
            self._schedule_id = None
            self._time = None
            self._duration = None
            self._name = f"Schedule {self.index + 1}"
            self._weekdays = None
            self._months = None
            self._days = None
            self._anchor = None
            self._from = None
            self._until = None

        self._schedule_id = config.get(CONF_SCHEDULE_ID, self.schedule_id)
        self._time = config.get(CONF_TIME, self._time)
        self._anchor = config.get(CONF_ANCHOR, self._anchor)
        self._duration = wash_td(config.get(CONF_DURATION, self._duration))
        self._name = config.get(CONF_NAME, self._name)
        self._enabled = config.get(CONF_ENABLED, self._enabled)

        if CONF_WEEKDAY in config:
            self._weekdays = []
            for i in config[CONF_WEEKDAY]:
                self._weekdays.append(WEEKDAYS.index(i))

        if CONF_MONTH in config:
            self._months = []
            for i in config[CONF_MONTH]:
                self._months.append(MONTHS.index(i) + 1)

        self._days = config.get(CONF_DAY, self._days)
        self._from = config.get(CONF_FROM, self._from)
        self._until = config.get(CONF_UNTIL, self._until)

        return self

    def as_dict(self) -> OrderedDict:
        """Return the schedule as a dict"""
        result = OrderedDict()

        result[CONF_TIME] = self._time
        result[CONF_ANCHOR] = self._anchor
        result[CONF_DURATION] = self._duration
        result[CONF_NAME] = self._name
        result[CONF_ENABLED] = self._enabled
        if self._weekdays is not None:
            result[CONF_WEEKDAY] = [WEEKDAYS[d] for d in self._weekdays]
        if self._months is not None:
            result[CONF_MONTH] = [MONTHS[m - 1] for m in self._months]
        if self._days is not None:
            result[CONF_DAY] = self._days
        return result

    def get_next_run(
        self,
        stime: datetime,
        ftime: datetime,
        adjusted_duration: timedelta,
        is_running: bool,
    ) -> datetime:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        """
        Determine the next start time. Date processing in this routine
        is done in local time and returned as UTC. stime is the current time
        and ftime is the farthest time we are interested in. adjusted_duration
        is the total time this schedule will run for, used to work backwards when
        the anchor is finish
        """
        local_time = dt.as_local(stime)
        final_time = dt.as_local(ftime)

        current_time: datetime = None
        next_run: datetime = None
        advancement = timedelta(days=1)
        while True:
            if current_time is None:  # Initialise on first pass
                current_time = local_time
            else:
                current_time += advancement  # Advance to next day
            next_run = current_time

            # Sanity check. Note: Astral events like sunrise might be months
            # away i.e. Antarctica winter
            if next_run > final_time:
                return None

            # DOW filter
            if self._weekdays is not None and next_run.weekday() not in self._weekdays:
                continue

            # Month filter
            if self._months is not None and next_run.month not in self._months:
                continue

            # Day filter
            if self._days is not None:
                if self._days == CONF_ODD:
                    if next_run.day % 2 == 0:
                        continue
                elif self._days == CONF_EVEN:
                    if next_run.day % 2 != 0:
                        continue
                elif isinstance(self._days, dict) and CONF_EVERY_N_DAYS in self._days:
                    n_days: int = self._days[CONF_EVERY_N_DAYS]
                    start_date: date = self._days[CONF_START_N_DAYS]
                    if (next_run.date() - start_date).days % n_days != 0:
                        continue
                elif next_run.day not in self._days:
                    continue

            # From/Until filter
            if self._from is not None and self._until is not None:
                dts = datetime.combine(
                    self._from.replace(year=next_run.year),
                    datetime.min.time(),
                    next_run.tzinfo,
                )
                dte = datetime.combine(
                    self._until.replace(year=next_run.year),
                    datetime.max.time(),
                    next_run.tzinfo,
                )
                if dte < dts:
                    if next_run >= dts:
                        dte = dte.replace(year=dte.year + 1)
                    else:
                        dts = dts.replace(year=dts.year - 1)

                if not dts <= next_run <= dte:
                    continue

            # Adjust time component
            if isinstance(self._time, time):
                next_run = datetime.combine(
                    next_run.date(), self._time, next_run.tzinfo
                )
            elif isinstance(self._time, dict) and CONF_SUN in self._time:
                sun_event = sun.get_astral_event_date(
                    self._hass, self._time[CONF_SUN], next_run
                )
                if sun_event is None:
                    continue  # Astral event did not occur today

                next_run = dt.as_local(sun_event)
                if CONF_AFTER in self._time:
                    next_run += self._time[CONF_AFTER]
                if CONF_BEFORE in self._time:
                    next_run -= self._time[CONF_BEFORE]
            elif isinstance(self._time, dict) and CONF_CRON in self._time:
                try:
                    cron = CronTab(self._time[CONF_CRON])
                    cron_event = cron.next(
                        now=local_time, return_datetime=True, default_utc=True
                    )
                    if cron_event is None:
                        return None
                    next_run = dt.as_local(cron_event)
                except ValueError as error:
                    self._coordinator.logger.log_invalid_crontab(
                        stime, self, self._time[CONF_CRON], error
                    )
                    self._enabled = False  # Shutdown this schedule
                    return None
            else:  # Some weird error happened
                return None

            if self._anchor == CONF_FINISH:
                next_run -= adjusted_duration

            next_run = wash_dt(next_run)
            if (is_running and next_run > local_time) or (
                not is_running and next_run + adjusted_duration > local_time
            ):
                break

        return dt.as_utc(next_run)


class IUSwitch:
    """Manager for the phsical switch entity"""

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: "IUCoordinator",
        controller: "IUController",
        zone: "IUZone",
    ) -> None:
        # Passed paramaters
        self._hass = hass
        self._coordinator = coordinator
        self._controller = controller
        self._zone = zone
        # Config parameters
        self._switch_entity_id: list[str]
        self._check_back_states = "all"
        self._check_back_delay = timedelta(seconds=30)
        self._check_back_retries: int = 3
        self._check_back_resync: bool = True
        self._state_on = STATE_ON
        self._state_off = STATE_OFF
        self._check_back_entity_id: str = None
        self._check_back_toggle: bool = False
        # private variables
        self._state: bool = None  # This parameter should mirror IUZone._is_on
        self._check_back_time: timedelta = None
        self._check_back_resync_count: int = 0

    @property
    def switch_entity_id(self) -> list[str] | None:
        """Return the switch entity"""
        return self._switch_entity_id

    def _set_switch(self, entity_id: str | list[str], state: bool) -> None:
        """Make the HA call to physically turn the switch on/off"""
        self._hass.async_create_task(
            self._hass.services.async_call(
                HADOMAIN,
                SERVICE_TURN_ON if state else SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: entity_id},
            )
        )

    def _check_back(self, atime: datetime) -> None:
        """Recheck the switch in HA to see if state concurs"""
        if (
            self._check_back_resync_count >= self._check_back_retries
            or not self._check_back_resync
        ):
            if entities := self.check_switch(atime, False, False):
                expected = self._state_on if self._state else self._state_off
                self._coordinator.logger.log_switch_error(atime, expected, entities)
                self._coordinator.notify_switch(
                    EVENT_SWITCH_ERROR, expected, entities, self._controller, self._zone
                )
            self._check_back_time = None
        else:
            if entities := self.check_switch(atime, self._check_back_resync, True):
                self._check_back_resync_count += 1
                self._check_back_time = atime + self._check_back_delay
            else:
                self._check_back_time = None

    def next_event(self) -> datetime:
        """Return the next time of interest"""
        if self._check_back_time is not None:
            return self._check_back_time
        return utc_eot()

    def clear(self) -> None:
        """Reset this object"""
        self._state = False

    def load(self, config: OrderedDict, all_zones: OrderedDict) -> "IUSwitch":
        """Load switch data from the configuration"""

        def load_params(config: OrderedDict) -> None:
            if config is None:
                return
            self._check_back_states = config.get(CONF_STATES, self._check_back_states)
            self._check_back_retries = config.get(
                CONF_RETRIES, self._check_back_retries
            )
            self._check_back_resync = config.get(CONF_RESYNC, self._check_back_resync)
            self._state_on = config.get(CONF_STATE_ON, self._state_on)
            self._state_off = config.get(CONF_STATE_OFF, self._state_off)
            delay = config.get(CONF_DELAY, self._check_back_delay.total_seconds())
            self._check_back_delay = wash_td(timedelta(seconds=delay))
            self._check_back_entity_id = config.get(
                CONF_ENTITY_ID, self._check_back_entity_id
            )
            self._check_back_toggle = config.get(CONF_TOGGLE, self._check_back_toggle)

        self.clear()
        self._switch_entity_id = config.get(CONF_ENTITY_ID)
        if all_zones is not None:
            load_params(all_zones.get(CONF_CHECK_BACK))
        load_params(config.get(CONF_CHECK_BACK))
        return self

    def muster(self, stime: datetime) -> int:
        """Muster this switch"""
        if self._check_back_time is not None and stime >= self._check_back_time:
            self._check_back(stime)

    def check_switch(self, stime: datetime, resync: bool, log: bool) -> list[str]:
        """Check the linked entity is in sync. Returns a list of entities
        that are not in sync"""

        result: list[str] = []

        def _check_entity(entity_id: str, expected: str) -> bool:
            is_valid = self._hass.states.is_state(entity_id, expected)
            if not is_valid:
                result.append(entity_id)
                if log:
                    self._coordinator.logger.log_sync_error(stime, expected, entity_id)
                    self._coordinator.notify_switch(
                        EVENT_SYNC_ERROR,
                        expected,
                        [entity_id],
                        self._controller,
                        self._zone,
                    )

            return is_valid

        def do_resync(entity_id: str) -> None:
            if self._check_back_toggle:
                self._set_switch(entity_id, not self._state)
            self._set_switch(entity_id, self._state)

        if self._switch_entity_id is not None:
            expected = self._state_on if self._state else self._state_off
            if self._check_back_entity_id is None:
                for entity_id in self._switch_entity_id:
                    if not _check_entity(entity_id, expected):
                        if resync:
                            do_resync(entity_id)
            else:
                if not _check_entity(self._check_back_entity_id, expected):
                    if resync and len(self._switch_entity_id) == 1:
                        do_resync(self._switch_entity_id)
        return result

    def call_switch(self, state: bool, stime: datetime = None) -> None:
        """Turn the HA entity on or off"""
        # pylint: disable=too-many-boolean-expressions
        if self._switch_entity_id is not None:
            if self._check_back_time is not None:
                # Switch state was changed before the recheck. Check now.
                self.check_switch(stime, False, True)
                self._check_back_time = None
            self._state = state
            self._set_switch(self._switch_entity_id, state)
            if stime is not None and (
                self._check_back_states == "all"
                or (self._check_back_states == "on" and state)
                or (self._check_back_states == "off" and not state)
            ):
                self._check_back_resync_count = 0
                self._check_back_time = stime + self._check_back_delay


class IUVolume:
    """Irrigation Unlimited Volume class"""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, hass: HomeAssistant, coordinator: "IUCoordinator") -> None:
        # Passed parameters
        self._hass = hass
        self._coordinator = coordinator
        # Config parameters
        self._sensor_id: str = None
        self._volume_rounding = 3
        self._volume_scale = 1
        self._flow_rounding = 3
        self._flow_scale = 3600
        # Private variables
        self._callback_remove: CALLBACK_TYPE = None
        self._start_volume: float = None
        self._total_volume: float = None
        self._start_time: datetime = None
        self._duration: timedelta = None

    @property
    def total(self) -> float | None:
        """Return the total value"""
        if self._total_volume is not None:
            return round(self._total_volume * self._volume_scale, self._volume_rounding)
        return None

    @property
    def flow_rate(self) -> str | None:
        """Return the flow rate"""
        if self._total_volume is not None and self._duration is not None:
            rate = (
                self._total_volume * self._flow_scale / self._duration.total_seconds()
            )
            return round(rate, self._flow_rounding)
        return None

    def load(self, config: OrderedDict, all_zones: OrderedDict) -> "IUSwitch":
        """Load volume data from the configuration"""

        def load_params(config: OrderedDict) -> None:
            if config is None:
                return
            self._sensor_id = config.get(CONF_ENTITY_ID, self._sensor_id)
            self._volume_rounding = config.get(CONF_PRECISION, self._volume_rounding)

        if all_zones is not None:
            load_params(all_zones.get(CONF_VOLUME))
        load_params(config.get(CONF_VOLUME))

    def start_record(self, stime: datetime) -> None:
        """Start recording volume information"""
        if self._sensor_id is None:
            return

        def sensor_state_change(event: HAEvent):
            # pylint: disable=unused-argument
            sensor = self._hass.states.get(self._sensor_id)
            if sensor is not None:
                try:
                    value = float(sensor.state)
                except ValueError:
                    return
                self._total_volume = value - self._start_volume

        self._start_volume = self._total_volume = None
        self._start_time = self._duration = None
        sensor = self._hass.states.get(self._sensor_id)
        if sensor is not None:
            try:
                self._start_volume = float(sensor.state)
            except ValueError:
                self._coordinator.logger.log_invalid_meter_value(stime, sensor.state)
            else:
                self._callback_remove = async_track_state_change_event(
                    self._hass, self._sensor_id, sensor_state_change
                )
                self._start_time = stime
        else:
            self._coordinator.logger.log_invalid_meter_id(stime, self._sensor_id)

    def end_record(self, stime: datetime) -> None:
        """Finish recording volume information"""
        if self._callback_remove is not None:
            self._callback_remove()
            self._callback_remove = None
        if self._start_volume is not None:
            sensor = self._hass.states.get(self._sensor_id)
            if sensor is not None:
                try:
                    value = float(sensor.state)
                except ValueError:
                    self._coordinator.logger.log_invalid_meter_value(
                        stime, sensor.state
                    )
                    self._total_volume = None
                else:
                    self._total_volume = value - self._start_volume
                    self._duration = stime - self._start_time
            else:
                self._coordinator.logger.log_invalid_meter_id(stime, self._sensor_id)
                self._total_volume = None
                self._duration = None


class IURunStatus(Enum):
    """Flags for the status of IURun object"""

    UNKNOWN = 0
    FUTURE = auto()
    RUNNING = auto()
    EXPIRED = auto()

    @staticmethod
    def status(
        stime: datetime, start_time: datetime, end_time: datetime
    ) -> "IURunStatus":
        """Determine the state of this object"""
        if start_time > stime:
            return IURunStatus.FUTURE
        if start_time <= stime < end_time:
            return IURunStatus.RUNNING
        if stime >= end_time:
            return IURunStatus.EXPIRED
        return IURunStatus.UNKNOWN


class IURun(IUBase):
    """Irrigation Unlimited Run class. A run is an actual point
    in time. If schedule is None then it is a manual run.
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

    def __init__(
        self,
        stime: datetime,
        start_time: datetime,
        duration: timedelta,
        zone: "IUZone",
        schedule: "IUSchedule",
        sequence_run: "IUSequenceRun",
        zone_run: "IURun",
    ) -> None:
        # pylint: disable=too-many-arguments
        super().__init__(None)
        # Passed parameters
        self._start_time: datetime = start_time
        self._duration: timedelta = duration
        self._zone = zone
        self._schedule = schedule
        self._sequence_run = sequence_run
        self._zone_run = zone_run
        # Private variables
        self._end_time: datetime = self._start_time + self._duration
        self._remaining_time: timedelta = self._end_time - self._start_time
        self._percent_complete: int = 0
        self._status = self._get_status(stime)

    @property
    def expired(self) -> bool:
        """Indicate if run has expired"""
        return self._status == IURunStatus.EXPIRED

    @property
    def running(self) -> bool:
        """Indicate if run is running"""
        return self._status == IURunStatus.RUNNING

    @property
    def future(self) -> bool:
        """Indicate if run is in the future"""
        return self._status == IURunStatus.FUTURE

    @property
    def start_time(self) -> datetime:
        """Return the start time"""
        return self._start_time

    @property
    def duration(self) -> timedelta:
        """Return the duration"""
        return self._duration

    @property
    def zone(self) -> "IUZone":
        """Return the zone for this run"""
        return self._zone

    @property
    def schedule(self) -> "IUSchedule":
        """Return the schedule"""
        return self._schedule

    @property
    def schedule_name(self) -> str:
        """Return the name of the schedule"""
        if self._schedule is not None:
            return self._schedule.name
        return RES_MANUAL

    @property
    def adjustment(self) -> str:
        """Return the adjustment in play"""
        if self._schedule is None:
            return ""
        if self.sequence_has_adjustment(True):
            return self.sequence_adjustment()
        return str(self._zone.adjustment)

    @property
    def end_time(self) -> datetime:
        """Return the finish time"""
        return self._end_time

    @property
    def time_remaining(self) -> timedelta:
        """Return the amount of time left to run"""
        return self._remaining_time

    @property
    def percent_complete(self) -> float:
        """Return the percentage completed"""
        return self._percent_complete

    @property
    def is_sequence(self) -> bool:
        """Return True if this run is a sequence"""
        return self._sequence_run is not None

    @property
    def sequence_run(self) -> "IUSequenceRun":
        """If a sequence then return the details"""
        return self._sequence_run

    @property
    def sequence(self) -> "IUSequence":
        """Return the associated sequence"""
        if self.is_sequence:
            return self._sequence_run.sequence
        return None

    @property
    def sequence_zone(self) -> "IUSequenceZone":
        """Return the sequence zone for this run"""
        if self.is_sequence:
            if self._zone_run is not None:
                return self._zone_run.sequence_zone
            return self._sequence_run.sequence_zone(self)
        return None

    @property
    def sequence_running(self) -> bool:
        """Return True if this run is a sequence and running"""
        return self.is_sequence and self._sequence_run.running

    @property
    def crumbs(self) -> str:
        """Return the debugging details for this run"""
        return self._crumbs()

    def _crumbs(self) -> str:
        def get_index(obj: IUBase) -> int:
            if obj is not None:
                return obj.index + 1
            return 0

        if self.is_sequence:
            sidx = self.sequence_run.run_index(self) + 1
        else:
            sidx = 0

        return (
            f"{get_index(self._zone)}"
            f".{get_index(self._schedule)}"
            f".{get_index(self.sequence)}"
            f".{get_index(self.sequence_zone)}"
            f".{sidx}"
        )

    def sequence_has_adjustment(self, deep: bool) -> bool:
        """Return True if this run is a sequence and has an adjustment"""
        if self.is_sequence:
            return self.sequence.has_adjustment(deep)
        return False

    def sequence_adjustment(self) -> str:
        """Return the adjustment for the sequence"""
        if self.is_sequence:
            result = str(self._sequence_run.sequence.adjustment)
            sequence_zone = self._sequence_run.sequence_zone(self)
            if sequence_zone is not None and sequence_zone.has_adjustment:
                result = f"{result},{str(sequence_zone.adjustment)}"
            return result
        return None

    def is_manual(self) -> bool:
        """Check if this is a manual run"""
        return self._schedule is None

    def _get_status(self, stime: datetime) -> IURunStatus:
        """Determine the state of this run"""
        return IURunStatus.status(stime, self._start_time, self._end_time)

    def update_status(self, stime: datetime) -> None:
        """Update the status of the run"""
        self._status = self._get_status(stime)

    def update_time_remaining(self, stime: datetime) -> bool:
        """Update the count down timers"""
        if self.running:
            self._remaining_time = self._end_time - stime
            total_duration: timedelta = self._end_time - self._start_time
            time_elapsed: timedelta = stime - self._start_time
            self._percent_complete = int((time_elapsed / total_duration) * 100)
            return True
        return False

    def as_dict(self) -> OrderedDict:
        """Return this run as a dict"""
        result = OrderedDict()
        result[TIMELINE_START] = self._start_time
        result[TIMELINE_END] = self._end_time
        result[TIMELINE_SCHEDULE_NAME] = self.schedule_name
        result[TIMELINE_ADJUSTMENT] = self.adjustment
        return result


class IURunQueue(list[IURun]):
    """Irrigation Unlimited class to hold the upcoming runs"""

    # pylint: disable=too-many-public-methods

    DAYS_SPAN: int = 3

    def __init__(self) -> None:
        super().__init__()
        # Config parameters
        self._future_span = wash_td(timedelta(days=self.DAYS_SPAN))
        # Private variables
        self._current_run: IURun = None
        self._next_run: IURun = None
        self._sorted: bool = False
        self._cancel_request: datetime = None
        self._next_event: datetime = None

    @property
    def current_run(self) -> IURun:
        """Return the current run"""
        return self._current_run

    @property
    def next_run(self) -> IURun:
        """Return the next run"""
        return self._next_run

    @property
    def in_sequence(self) -> bool:
        """Return True if this run is part of a sequence"""
        for run in self:
            if run.sequence_running:
                return True
        return False

    def add(
        self,
        stime: datetime,
        start_time: datetime,
        duration: timedelta,
        zone: "IUZone",
        schedule: "IUSchedule",
        sequence_run: "IUSequenceRun",
        zone_run: IURun,
    ) -> IURun:
        # pylint: disable=too-many-arguments
        """Add a run to the queue"""
        run = IURun(stime, start_time, duration, zone, schedule, sequence_run, zone_run)
        self.append(run)
        self._sorted = False
        return run

    def cancel(self, stime: datetime) -> None:
        """Flag the current run to be cancelled"""
        self._cancel_request = stime

    def clear_all(self) -> None:
        """Clear out all runs"""
        self._current_run = None
        self._next_run = None
        super().clear()

    def clear_runs(self, include_sequence: bool) -> bool:
        """Clear out the queue except for manual and running schedules"""
        modified = False
        i = len(self) - 1
        while i >= 0:
            run = self[i]
            if (include_sequence or not run.is_sequence) and not (
                run.running or run.is_manual()
            ):
                self.pop_run(i)
                modified = True
            i -= 1
        if modified:
            self._next_run = None
        return modified

    def find_last_index(self, schedule: IUSchedule) -> int:
        """Return the index of the run that finishes last in the queue.
        This routine does not require the list to be sorted."""
        result: int = None
        last_time: datetime = None
        for i, run in enumerate(self):
            if run.schedule is not None and run.schedule == schedule:
                if last_time is None or run.end_time > last_time:
                    last_time = run.end_time
                    result = i
        return result

    def find_last_run(self, schedule: IUSchedule) -> IURun:
        """Find the last run for the matching schedule"""
        i = self.find_last_index(schedule)
        if i is not None:
            return self[i]
        return None

    def last_time(self, stime: datetime) -> datetime:
        """Return the further most look ahead date"""
        return stime + self._future_span

    def load(self, config: OrderedDict, all_zones: OrderedDict):
        """Load the config settings"""
        fsd = IURunQueue.DAYS_SPAN
        if all_zones is not None:
            fsd = all_zones.get(CONF_FUTURE_SPAN, fsd)
        fsd = max(config.get(CONF_FUTURE_SPAN, fsd), 1)
        self._future_span = wash_td(timedelta(days=fsd))
        return self

    def sort(self) -> bool:
        """Sort the run queue."""

        def sorter(run: IURun) -> datetime:
            """Sort call back routine. Items are sorted by start_time."""
            if run.is_manual():
                start = datetime.min  # Always put manual run at head
            else:
                start = run.start_time
            return start.replace(tzinfo=None).isoformat(timespec="seconds")

        modified: bool = False
        if not self._sorted:
            super().sort(key=sorter)
            self._current_run = None
            self._next_run = None
            self._sorted = True
            modified = True
        return modified

    def remove_expired(self, stime: datetime, postamble: timedelta) -> bool:
        """Remove any expired runs from the queue"""
        modified: bool = False
        if postamble is None:
            postamble = timedelta(0)
        i = len(self) - 1
        while i >= 0:
            run = self[i]
            if not run.is_sequence:
                if run.expired and stime > run.end_time + postamble:
                    self.pop_run(i)
                    modified = True
            else:
                if (
                    run.sequence_run.expired
                    and run.expired
                    and stime > run.end_time + postamble
                ):
                    self.pop_run(i)
                    modified = True
            i -= 1
        return modified

    def remove_current(self) -> bool:
        """Remove the current run or upcoming manual run"""
        modified: bool = False
        if self._current_run is not None or (
            self._next_run is not None and self._next_run.is_manual()
        ):
            if len(self) > 0:
                self.pop_run(0)
            self._current_run = None
            self._next_run = None
            modified = True
        return modified

    def pop_run(self, index) -> "IURun":
        """Remove run from queue by index"""
        run = self.pop(index)
        if run == self._current_run:
            self._current_run = None
            self._next_run = None
        if run == self._next_run:
            self._next_run = None
        return run

    def remove_run(self, run: IURun) -> "IURun":
        """Remove the run from the queue"""
        return self.pop_run(self.index(run))

    def update_run_status(self, stime) -> None:
        """Update the status of the runs"""
        for run in self:
            run.update_status(stime)

    def update_queue(self) -> IURQStatus:
        """Update the run queue. Sort the queue, remove expired runs
        and set current and next runs. This is the final operation after
        all additions and deletions.

        Returns a bit field of changes to queue.
        """
        # pylint: disable=too-many-branches
        status = IURQStatus(0)

        if self.sort():
            status |= IURQStatus.SORTED

        if self._cancel_request is not None:
            if self.remove_current():
                status |= IURQStatus.CANCELED
            self._cancel_request = None

        # Try to find a running schedule
        if self._current_run is not None and self._current_run.expired:
            self._current_run = None
            status |= IURQStatus.UPDATED
        if self._current_run is None:
            for run in self:
                if run.running and run.duration != timedelta(0):
                    self._current_run = run
                    self._next_run = None
                    status |= IURQStatus.UPDATED
                    break

        # Try to find the next schedule
        if self._next_run is not None and self._next_run.expired:
            self._next_run = None
            status |= IURQStatus.UPDATED
        if self._next_run is None:
            for run in self:
                if run.future and run.duration != timedelta(0):
                    self._next_run = run
                    status |= IURQStatus.UPDATED
                    break

        # Figure out the next state change
        dates: list[datetime] = [utc_eot()]
        for run in self:
            if not run.expired:
                if run.running:
                    dates.append(run.end_time)
                else:
                    dates.append(run.start_time)
        self._next_event = min(dates)

        return status

    def update_sensor(self, stime: datetime) -> bool:
        """Update the count down timers"""
        if self._current_run is None:
            return False
        return self._current_run.update_time_remaining(stime)

    def next_event(self) -> datetime:
        """Return the time of the next state change"""
        dates: list[datetime] = [self._next_event]
        dates.append(self._cancel_request)
        return min(d for d in dates if d is not None)

    def as_list(self) -> list:
        """Return a list of runs"""
        result = []
        for run in self:
            result.append(run.as_dict())
        return result


class IUScheduleQueue(IURunQueue):
    """Class to hold the upcoming schedules to run"""

    def __init__(self) -> None:
        super().__init__()
        # Config variables
        self._minimum: timedelta = None
        self._maximum: timedelta = None

    def constrain(self, duration: timedelta) -> timedelta:
        """Impose constraints on the duration"""
        if self._minimum is not None:
            duration = max(duration, self._minimum)
        if self._maximum is not None:
            duration = min(duration, self._maximum)
        return duration

    def clear_runs(self) -> bool:
        """Clear out the queue except for manual and running schedules"""
        # pylint: disable=arguments-differ
        return super().clear_runs(False)

    def add(
        self,
        stime: datetime,
        start_time: datetime,
        duration: timedelta,
        zone: "IUZone",
        schedule: "IUSchedule",
        sequence_run: "IUSequenceRun",
    ) -> IURun:
        """Add a new run to the queue"""
        # pylint: disable=arguments-differ
        # pylint: disable=too-many-arguments
        return super().add(
            stime,
            start_time,
            self.constrain(duration),
            zone,
            schedule,
            sequence_run,
            None,
        )

    def add_manual(
        self,
        stime: datetime,
        start_time: datetime,
        duration: timedelta,
        zone: "IUZone",
        queue: bool,
    ) -> IURun:
        """Add a manual run to the queue. Cancel any existing
        manual or running schedule"""

        if self._current_run is not None:
            self.pop_run(0)

        # Remove any existing manual schedules
        if not queue:
            for manual in (run for run in self if run.is_manual()):
                self.remove_run(manual)

        self._current_run = None
        self._next_run = None
        duration = max(duration, granularity_time())
        return self.add(stime, start_time, duration, zone, None, None)

    def merge_one(
        self,
        stime: datetime,
        zone: "IUZone",
        schedule: IUSchedule,
        adjustment: IUAdjustment,
    ) -> bool:
        """Extend the run queue. Return True if it was extended"""
        modified: bool = False

        # See if schedule already exists in run queue. If so get
        # the finish time of the last entry.
        last_run = self.find_last_run(schedule)
        if last_run is not None:
            next_time = last_run.end_time + granularity_time()
            is_running = last_run.running
        else:
            next_time = stime
            is_running = False

        duration = self.constrain(adjustment.adjust(schedule.duration))
        next_run = schedule.get_next_run(
            next_time, self.last_time(stime), duration, is_running
        )

        if next_run is not None:
            self.add(stime, next_run, duration, zone, schedule, None)
            modified = True

        return modified

    def merge_fill(
        self,
        stime: datetime,
        zone: "IUZone",
        schedule: IUSchedule,
        adjustment: IUAdjustment,
    ) -> bool:
        """Merge the schedule into the run queue. Add as many until the span is
        reached. Return True if the schedule was added."""
        modified: bool = False

        while self.merge_one(stime, zone, schedule, adjustment):
            modified = True

        return modified

    def load(self, config: OrderedDict, all_zones: OrderedDict) -> "IUScheduleQueue":
        """Load the configuration settings"""
        self._minimum = None
        self._maximum = None

        super().load(config, all_zones)
        if all_zones is not None:
            self._minimum = wash_td(all_zones.get(CONF_MINIMUM, self._minimum))
            self._maximum = wash_td(all_zones.get(CONF_MAXIMUM, self._maximum))
        self._minimum = wash_td(config.get(CONF_MINIMUM, self._minimum))
        self._maximum = wash_td(config.get(CONF_MAXIMUM, self._maximum))
        return self


class IUZone(IUBase):
    """Irrigation Unlimited Zone class"""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: "IUCoordinator",
        controller: "IUController",
        zone_index: int,
    ) -> None:
        super().__init__(zone_index)
        # Passed parameters
        self._hass = hass
        self._coordinator = coordinator
        self._controller = controller
        # Config parameters
        self._zone_id: str = None
        self._enabled: bool = True
        self._allow_manual: bool = False
        self._name: str = None
        self._show_config: bool = False
        self._show_timeline: bool = False
        self._duration: timedelta = None
        # Private variables
        self._initialised: bool = False
        self._finalised: bool = False
        self._schedules: list[IUSchedule] = []
        self._run_queue = IUScheduleQueue()
        self._adjustment = IUAdjustment()
        self._zone_sensor: Entity = None
        self._is_on: bool = False
        self._sensor_update_required: bool = False
        self._sensor_last_update: datetime = None
        self._suspend_until: datetime = None
        self._dirty: bool = True
        self._switch = IUSwitch(hass, coordinator, controller, self)
        self._volume = IUVolume(hass, coordinator)
        self._user = IUUser()

    @property
    def unique_id(self) -> str:
        """Return the HA unique_id for the zone"""
        return f"c{self._controller.index + 1}_z{self.index + 1}"

    @property
    def entity_base(self) -> str:
        """Return the base of the entity_id"""
        if self._coordinator.rename_entities:
            return f"{self._controller.controller_id}_{self._zone_id}"
        return self.unique_id

    @property
    def entity_id(self) -> str:
        """Return the HA entity_id for the zone"""
        return f"{BINARY_SENSOR}.{DOMAIN}_{self.entity_base}"

    @property
    def schedules(self) -> "list[IUSchedule]":
        """Return a list of schedules associated with this zone"""
        return self._schedules

    @property
    def runs(self) -> IUScheduleQueue:
        """Return the run queue for this zone"""
        return self._run_queue

    @property
    def adjustment(self) -> IUAdjustment:
        """Return the adjustment for this zone"""
        return self._adjustment

    @property
    def volume(self) -> IUVolume:
        """Return the volume for this zone"""
        return self._volume

    @property
    def zone_id(self) -> str:
        """Return the zone_id. Should match the zone_id used in sequences"""
        return self._zone_id

    @property
    def name(self) -> str:
        """Return the friendly name for this zone"""
        if self._name is not None:
            return self._name
        return f"Zone {self._index + 1}"

    @property
    def is_on(self) -> bool:
        """Indicate if zone is on or off"""
        return self._is_on

    @property
    def is_setup(self) -> bool:
        """Return True if this zone is setup and ready to go"""
        return self._is_setup()

    @property
    def is_enabled(self) -> bool:
        """Return true is this zone is enabled and not suspended"""
        return self._enabled and self._suspend_until is None

    @property
    def enabled(self) -> bool:
        """Return true if this zone is enabled"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable/disable zone"""
        if value != self._enabled:
            self._enabled = value
            self._dirty = True
            self.request_update()

    @property
    def suspended(self) -> datetime:
        """Return the suspend date"""
        return self._suspend_until

    @suspended.setter
    def suspended(self, value: datetime) -> None:
        """Set the suspend time"""
        if value != self._suspend_until:
            self._suspend_until = value
            self._dirty = True
            self.request_update()

    @property
    def allow_manual(self) -> bool:
        """Return True if manual overide allowed"""
        return self._allow_manual

    @property
    def zone_sensor(self) -> Entity:
        """Return the HA entity associated with this zone"""
        return self._zone_sensor

    @zone_sensor.setter
    def zone_sensor(self, value: Entity) -> None:
        self._zone_sensor = value

    @property
    def status(self) -> str:
        """Return the state of the zone"""
        return self._status()

    @property
    def show_config(self) -> bool:
        """Indicate if the config show be shown as an attribute"""
        return self._show_config

    @property
    def show_timeline(self) -> bool:
        """Indicate if the timeline (run queue) should be shown as an attribute"""
        return self._show_timeline

    @property
    def today_total(self) -> timedelta:
        """Return the total on time for today"""
        return self._coordinator.history.today_total(self.entity_id)

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self._controller.is_enabled:
            if self.enabled:
                if self.suspended is None:
                    if self.is_on:
                        return ICON_ZONE_ON
                    return ICON_ZONE_OFF
                return ICON_SUSPENDED
            return ICON_DISABLED
        return ICON_BLOCKED

    @property
    def configuration(self) -> str:
        """Return this zone as JSON"""
        return json.dumps(self.as_dict(), cls=IUJSONEncoder)

    @property
    def user(self) -> dict:
        """Return the arbitrary user information"""
        return self._user

    def _is_setup(self) -> bool:
        """Check if this object is setup"""
        self._initialised = self._zone_sensor is not None

        if self._initialised:
            for schedule in self._schedules:
                self._initialised = self._initialised and schedule.is_setup
        return self._initialised

    def _status(self) -> str:
        """Return status of zone"""
        if self._initialised:
            if self._controller.is_enabled:
                if self.enabled:
                    if self.suspended is None:
                        if self.is_on:
                            return STATE_ON
                        return STATE_OFF
                    return STATUS_SUSPENDED
                return STATUS_DISABLED
            return STATUS_BLOCKED
        return STATUS_INITIALISING

    def service_call(
        self, data: MappingProxyType, stime: datetime, service: str
    ) -> bool:
        """Handler for enable/disable/toggle service call"""
        # pylint: disable=unused-argument

        if service == SERVICE_ENABLE:
            new_state = True
        elif service == SERVICE_DISABLE:
            new_state = False
        else:
            new_state = not self.enabled  # Must be SERVICE_TOGGLE

        result = self.enabled != new_state
        if result:
            self.enabled = new_state
        return result

    def service_suspend(self, data: MappingProxyType, stime: datetime) -> bool:
        """Handler for the suspend service call"""
        sequence_id = data.get(CONF_SEQUENCE_ID)
        if sequence_id is not None:
            self._coordinator.logger.log_sequence_entity(stime)
        suspend_time = self._controller.suspend_until_date(data, stime)
        if suspend_time != self._suspend_until:
            self.suspended = suspend_time
            return True
        return False

    def service_adjust_time(self, data: MappingProxyType, stime: datetime) -> bool:
        """Adjust the scheduled run times. Return true if adjustment changed"""
        sequence_id = data.get(CONF_SEQUENCE_ID)
        if sequence_id is not None:
            self._coordinator.logger.log_sequence_entity(stime)
        return self._adjustment.load(data)

    def service_manual_run(self, data: MappingProxyType, stime: datetime) -> None:
        """Add a manual run."""
        if self._allow_manual or (self.is_enabled and self._controller.is_enabled):
            duration = wash_td(data.get(CONF_TIME))
            delay = wash_td(data.get(CONF_DELAY, timedelta(0)))
            queue = data.get(CONF_QUEUE, self._controller.queue_manual)
            if duration is None or duration == timedelta(0):
                duration = self._duration
                if duration is None:
                    return
                duration = self._adjustment.adjust(duration)
            self._run_queue.add_manual(
                stime,
                self._controller.manual_run_start(stime, delay, queue),
                duration,
                self,
                queue,
            )

    def service_cancel(self, data: MappingProxyType, stime: datetime) -> None:
        """Cancel the current running schedule"""
        # pylint: disable=unused-argument
        self._run_queue.cancel(stime)

    def add(self, schedule: IUSchedule) -> IUSchedule:
        """Add a new schedule to the zone"""
        self._schedules.append(schedule)
        return schedule

    def find_add(self, index: int) -> IUSchedule:
        """Look for and add if necessary a new schedule"""
        if index >= len(self._schedules):
            return self.add(IUSchedule(self._hass, self._coordinator, index))
        return self._schedules[index]

    def clear(self) -> None:
        """Reset this zone"""
        self._schedules.clear()
        self.clear_run_queue()

    def clear_run_queue(self) -> None:
        """Clear out the run queue completely"""
        self._run_queue.clear_all()

    def load(self, config: OrderedDict, all_zones: OrderedDict) -> "IUZone":
        """Load zone data from the configuration"""
        self.clear()
        if all_zones is not None:
            self._allow_manual = all_zones.get(CONF_ALLOW_MANUAL, self._allow_manual)
            self._duration = all_zones.get(CONF_DURATION, self._duration)
            if CONF_SHOW in all_zones:
                self._show_config = all_zones[CONF_SHOW].get(
                    CONF_CONFIG, self._show_config
                )
                self._show_timeline = all_zones[CONF_SHOW].get(
                    CONF_TIMELINE, self._show_timeline
                )
        self._zone_id = config.get(CONF_ZONE_ID, str(self.index + 1))
        self._enabled = config.get(CONF_ENABLED, self._enabled)
        self._allow_manual = config.get(CONF_ALLOW_MANUAL, self._allow_manual)
        self._duration = config.get(CONF_DURATION, self._duration)
        self._name = config.get(CONF_NAME, None)
        self._run_queue.load(config, all_zones)
        if CONF_SHOW in config:
            self._show_config = config[CONF_SHOW].get(CONF_CONFIG, self._show_config)
            self._show_timeline = config[CONF_SHOW].get(
                CONF_TIMELINE, self._show_timeline
            )
        if CONF_SCHEDULES in config:
            for sidx, schedule_config in enumerate(config[CONF_SCHEDULES]):
                self.find_add(sidx).load(schedule_config)
        self._switch.load(config, all_zones)
        self._volume.load(config, all_zones)
        self._user.load(config, all_zones)
        self._dirty = True
        return self

    def finalise(self, turn_off: bool) -> None:
        """Shutdown the zone"""
        if not self._finalised:
            if turn_off and self._is_on:
                self.call_switch(False)
            self.clear()
            self._finalised = True

    def as_dict(self) -> OrderedDict:
        """Return this zone as a dict"""
        if self.runs.current_run is not None:
            current_duration = self.runs.current_run.duration
        else:
            current_duration = timedelta(0)
        result = OrderedDict()
        result[CONF_INDEX] = self._index
        result[CONF_NAME] = self.name
        result[CONF_STATE] = STATE_ON if self.is_on else STATE_OFF
        result[CONF_ENABLED] = self.enabled
        result[ATTR_SUSPENDED] = self.suspended
        result[CONF_ICON] = self.icon
        result[CONF_ZONE_ID] = self._zone_id
        result[CONF_ENTITY_BASE] = self.entity_base
        result[ATTR_STATUS] = self.status
        result[ATTR_ADJUSTMENT] = str(self._adjustment)
        result[ATTR_CURRENT_DURATION] = current_duration
        result[CONF_SCHEDULES] = [sch.as_dict() for sch in self._schedules]
        result[ATTR_SWITCH_ENTITIES] = self._switch.switch_entity_id
        return result

    def timeline(self) -> list:
        """Return the on/off timeline. Merge history and future and add
        the status"""
        run_list = self._coordinator.history.timeline(self.entity_id)
        for run in run_list:
            run[TIMELINE_STATUS] = RES_TIMELINE_HISTORY

        for run in self._run_queue:
            dct = run.as_dict()
            if run.running:
                dct[TIMELINE_STATUS] = RES_TIMELINE_RUNNING
            elif run == self._run_queue.next_run:
                dct[TIMELINE_STATUS] = RES_TIMELINE_NEXT
            else:
                dct[TIMELINE_STATUS] = RES_TIMELINE_SCHEDULED
            run_list.append(dct)
        run_list.reverse()
        return run_list

    def muster(self, stime: datetime) -> IURQStatus:
        """Muster this zone"""
        # pylint: disable=unused-argument
        status = IURQStatus(0)

        if self._dirty:
            self._run_queue.clear_all()
            status |= IURQStatus.CLEARED

        if self._suspend_until is not None and stime >= self._suspend_until:
            self._suspend_until = None
            status |= IURQStatus.CHANGED

        self._switch.muster(stime)

        self._dirty = False
        return status

    def muster_schedules(self, stime: datetime) -> IURQStatus:
        """Calculate run times for this zone"""
        status = IURQStatus(0)

        for schedule in self._schedules:
            if not schedule.enabled:
                continue
            if self._run_queue.merge_fill(stime, self, schedule, self._adjustment):
                status |= IURQStatus.EXTENDED

        if not status.is_empty():
            self.request_update()

        return status

    def check_run(self, parent_enabled: bool) -> bool:
        """Update the run status"""
        is_running: bool = False
        state_changed: bool = False

        is_running = parent_enabled and (
            (
                self.is_enabled
                and self._run_queue.current_run is not None
                and self._run_queue.current_run.running
            )
            or (
                self._allow_manual
                and self._run_queue.current_run is not None
                and self._run_queue.current_run.is_manual()
            )
        )

        state_changed = is_running ^ self._is_on
        if state_changed:
            self._is_on = not self._is_on
            self.request_update()

        return state_changed

    def request_update(self) -> None:
        """Flag the sensor needs an update"""
        self._sensor_update_required = True

    def update_sensor(self, stime: datetime, do_on: bool) -> bool:
        """Lazy sensor updater"""
        updated: bool = False
        do_update: bool = False

        if self._zone_sensor is not None:
            if do_on is False:
                updated |= self._run_queue.update_sensor(stime)
                if not self._is_on:
                    # Force a refresh at midnight for the total_today attribute
                    if (
                        self._sensor_last_update is not None
                        and dt.as_local(self._sensor_last_update).toordinal()
                        != dt.as_local(stime).toordinal()
                    ):
                        do_update = True
                    do_update |= self._sensor_update_required
            else:
                if self._is_on:
                    # If we are running then update sensor according to refresh_interval
                    if self._run_queue.current_run is not None:
                        do_update = (
                            self._sensor_last_update is None
                            or stime - self._sensor_last_update
                            >= self._coordinator.refresh_interval
                        )
                    do_update |= self._sensor_update_required
        else:
            do_update = False

        if do_update:
            self._zone_sensor.schedule_update_ha_state()
            self._sensor_update_required = False
            self._sensor_last_update = stime
            updated = True

        return updated

    def next_awakening(self) -> datetime:
        """Return the next event time"""
        dates: list[datetime] = [
            self._run_queue.next_event(),
            self._switch.next_event(),
        ]
        if self._is_on and self._sensor_last_update is not None:
            dates.append(self._sensor_last_update + self._coordinator.refresh_interval)
        dates.append(self._suspend_until)
        return min(d for d in dates if d is not None)

    def check_switch(self, resync: bool, stime: datetime) -> list[str]:
        """Check the linked entity is in sync"""
        return self._switch.check_switch(stime, resync, True)

    def call_switch(self, state: bool, stime: datetime = None) -> None:
        """Turn the HA entity on or off"""
        self._switch.call_switch(state, stime)
        self._coordinator.status_changed(stime, self._controller, self, state)


class IUZoneQueue(IURunQueue):
    """Class to hold the upcoming zones to run"""

    def clear_runs(self) -> bool:
        """Clear out the queue except for manual and running schedules"""
        # pylint: disable=arguments-differ
        return super().clear_runs(True)

    def find_run(
        self,
        start_time: datetime,
        zone_run: IURun,
    ) -> IURun:
        """Find the specified run in the queue"""
        for run in self:
            if (
                start_time == run.start_time
                and zone_run.zone == run.zone
                and run.schedule is not None
                and zone_run.schedule is not None
                and run.schedule == zone_run.schedule
            ):
                return run
        return None

    def add_zone(
        self,
        stime: datetime,
        zone_run: IURun,
        preamble: timedelta,
        postamble: timedelta,
        no_find: bool,
    ) -> IURun:
        """Add a new master run to the queue"""
        start_time = zone_run.start_time
        duration = zone_run.duration
        if preamble is not None:
            start_time -= preamble
            duration += preamble
        if postamble is not None:
            duration += postamble
        if not no_find:
            run = self.find_run(start_time, zone_run)
        else:
            run = None
        if run is None:
            run = self.add(
                stime,
                start_time,
                duration,
                zone_run.zone,
                zone_run.schedule,
                zone_run.sequence_run,
                zone_run,
            )
        return run

    def rebuild_schedule(
        self,
        stime: datetime,
        zones: list[IUZone],
        preamble: timedelta,
        postamble: timedelta,
        clear_all: bool,
    ) -> IURQStatus:
        """Create a superset of all the zones."""
        # pylint: disable=too-many-arguments
        status = IURQStatus(0)
        if clear_all:
            self.clear_all()
        else:
            self.clear_runs()
        for zone in zones:
            for run in zone.runs:
                if not run.expired:
                    self.add_zone(stime, run, preamble, postamble, clear_all)
        status |= IURQStatus.EXTENDED | IURQStatus.REDUCED
        return status


class IUSequenceZone(IUBase):
    """Irrigation Unlimited Sequence Zone class"""

    # pylint: disable=too-many-instance-attributes

    ZONE_OFFSET: int = 1

    def __init__(
        self,
        controller: "IUController",
        sequence: "IUSequence",
        zone_index: int,
    ) -> None:
        super().__init__(zone_index)
        # Passed parameters
        self._controller = controller
        self._sequence = sequence
        # Config parameters
        self._zone_ids: list[str] = None
        self._zones: list[IUZone] = []
        self._delay: timedelta = None
        self._duration: timedelta = None
        self._repeat: int = None
        self._enabled: bool = True
        # Private variables
        self._adjustment = IUAdjustment()
        self._suspend_until: datetime = None

    @property
    def zone_ids(self) -> list[str]:
        """Returns a list of zone_id's"""
        return self._zone_ids

    @property
    def zones(self) -> list[IUZone]:
        """Return the list of associated zones"""
        return self._zones

    @property
    def duration(self) -> timedelta:
        """Returns the duration for this sequence"""
        return self._duration

    @property
    def delay(self) -> timedelta:
        """ "Returns the post delay for this sequence"""
        return self._delay

    @property
    def repeat(self) -> int:
        """Returns the number of repeats for this sequence"""
        return self._repeat

    @property
    def is_enabled(self) -> bool:
        """Return true if this sequence_zone is enabled and not suspended"""
        return self._enabled and self._suspend_until is None

    @property
    def enabled(self) -> bool:
        """Return if this sequence zone is enabled"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set the enabled state"""
        self._enabled = value

    @property
    def suspended(self) -> datetime:
        """Return the suspend date"""
        return self._suspend_until

    @suspended.setter
    def suspended(self, value: datetime) -> None:
        self._suspend_until = value

    @property
    def adjustment(self) -> IUAdjustment:
        """Returns the adjustment for this sequence"""
        return self._adjustment

    @property
    def has_adjustment(self) -> bool:
        """Returns True if this sequence has an active adjustment"""
        return self._adjustment.has_adjustment

    @property
    def is_on(self) -> bool:
        """Return if this sequence zone is running"""
        active_zone = self._sequence.runs.active_zone
        return active_zone is not None and active_zone.sequence_zone == self

    def icon(self, is_on: bool = None) -> str:
        """Return the icon to use in the frontend."""
        if self._controller.is_enabled:
            if self._sequence.is_enabled:
                if self.suspended is None:
                    if self._sequence.zone_enabled(self):
                        if is_on is None:
                            is_on = self.is_on
                        if is_on:
                            return ICON_SEQUENCE_ZONE_ON
                        return ICON_SEQUENCE_ZONE_OFF
                    return ICON_DISABLED
                return ICON_SUSPENDED
        return ICON_BLOCKED

    def status(self, is_on: bool = None) -> str:
        """Return status of the sequence zone"""
        if self._controller.is_enabled:
            if self._sequence.is_enabled:
                if self.suspended is None:
                    if self._sequence.zone_enabled(self):
                        if is_on is None:
                            is_on = self.is_on
                        if is_on:
                            return STATE_ON
                        return STATE_OFF
                    return STATUS_DISABLED
                return STATUS_SUSPENDED
        return STATUS_BLOCKED

    def load(self, config: OrderedDict) -> "IUSequenceZone":
        """Load sequence zone data from the configuration"""

        def build_zones() -> None:
            """Construct a local list of IUZones"""
            self._zones.clear()
            for zone_id in self._zone_ids:
                if (zone := self._controller.find_zone_by_zone_id(zone_id)) is not None:
                    self._zones.append(zone)

        self._zone_ids = config[CONF_ZONE_ID]
        self._delay = wash_td(config.get(CONF_DELAY))
        self._duration = wash_td(config.get(CONF_DURATION))
        self._repeat = config.get(CONF_REPEAT, 1)
        self._enabled = config.get(CONF_ENABLED, self._enabled)
        build_zones()
        return self

    def as_dict(self, duration_factor: float, sqr: "IUSequenceRun" = None) -> dict:
        """Return this sequence zone as a dict"""
        result = OrderedDict()
        result[CONF_INDEX] = self._index
        result[CONF_STATE] = STATE_ON if self.is_on else STATE_OFF
        result[CONF_ENABLED] = self.enabled
        result[ATTR_SUSPENDED] = self.suspended
        result[CONF_ICON] = self.icon()
        result[ATTR_STATUS] = self.status()
        result[CONF_DELAY] = self._sequence.zone_delay(self, sqr)
        result[ATTR_BASE_DURATION] = self._sequence.zone_duration_base(self, sqr)
        result[ATTR_ADJUSTED_DURATION] = self._sequence.zone_duration(self, sqr)
        result[ATTR_FINAL_DURATION] = self._sequence.zone_duration_final(
            self, duration_factor, sqr
        )
        result[CONF_ZONES] = list(zone.index + self.ZONE_OFFSET for zone in self._zones)
        result[ATTR_CURRENT_DURATION] = self._sequence.runs.active_zone_duration(self)
        result[ATTR_ADJUSTMENT] = str(self._adjustment)
        return result

    def muster(self, stime: datetime) -> IURQStatus:
        """Muster this sequence zone"""
        status = IURQStatus(0)
        if self._suspend_until is not None and stime >= self._suspend_until:
            self._suspend_until = None
            status |= IURQStatus.CHANGED
        return status

    def next_awakening(self) -> datetime:
        """Return the next event time"""
        result = utc_eot()
        if self._suspend_until is not None:
            result = min(self._suspend_until, result)
        return result


class IUSequenceZoneRun(NamedTuple):
    """Irrigation Unlimited sequence zone run class"""

    sequence_zone: IUSequenceZone
    sequence_repeat: int
    zone_repeat: int


class IUSequenceRunAllocation(NamedTuple):
    """Irrigation Unlimited sequence zone allocation class"""

    start: datetime
    duration: timedelta
    zone: IUZone
    sequence_zone_run: IUSequenceZoneRun


class IUSequenceRun(IUBase):
    """Irrigation Unlimited sequence run manager class. Ties together the
    individual sequence zones"""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods
    def __init__(
        self,
        coordinator: "IUCoordinator",
        controller: "IUController",
        sequence: "IUSequence",
        schedule: IUSchedule,
    ) -> None:
        # pylint: disable=too-many-arguments
        super().__init__(None)
        # Passed parameters
        self._coordinator = coordinator
        self._controller = controller
        self._sequence = sequence
        self._schedule = schedule
        # Private variables
        self._runs_pre_allocate: list[IUSequenceRunAllocation] = []
        self._runs: dict[IURun, IUSequenceZoneRun] = weakref.WeakKeyDictionary()
        self._active_zone: IUSequenceZoneRun = None
        self._start_time: datetime = None
        self._end_time: datetime = None
        self._accumulated_duration = timedelta(0)
        self._first_zone: IUZone = None
        self._status = IURunStatus.UNKNOWN

    @property
    def sequence(self) -> "IUSequence":
        """Return the sequence associated with this run"""
        return self._sequence

    @property
    def schedule(self) -> IUSchedule:
        """Return the schedule associated with this run"""
        return self._schedule

    @property
    def start_time(self) -> datetime:
        """Return the start time for this sequence"""
        return self._start_time

    @property
    def end_time(self) -> datetime:
        """Return the end time for this sequence"""
        return self._end_time

    @property
    def total_time(self) -> timedelta:
        """Return the total run time for this sequence"""
        return self._end_time - self._start_time

    @property
    def running(self) -> bool:
        """Indicate if this sequence is running"""
        return self._status == IURunStatus.RUNNING

    @property
    def expired(self) -> bool:
        """Indicate if this sequence has expired"""
        return self._status == IURunStatus.EXPIRED

    @property
    def active_zone(self) -> IUSequenceZoneRun:
        """Return the active zone in the sequence"""
        return self._active_zone

    @property
    def runs(self) -> dict[IURun, IUSequenceZoneRun]:
        """Return the runs"""
        return self._runs

    def is_manual(self) -> bool:
        """Check if this is a manual run"""
        return self._schedule is None

    def zone_enabled(self, zone: IUZone) -> bool:
        """Return true if the zone is enabled"""
        return zone is not None and (
            zone.is_enabled or (self.is_manual() and zone.allow_manual)
        )

    def calc_total_time(self, total_time: timedelta) -> timedelta:
        """Calculate the total duration of the sequence"""
        if total_time is None:
            if self._schedule is not None and self._schedule.duration is not None:
                return self._sequence.total_time_final(self._schedule.duration, self)
            return self.sequence.total_time_final(None, self)

        if self._schedule is not None:
            return self._sequence.total_time_final(total_time, self)
        return total_time

    def build(self, duration_factor: float) -> timedelta:
        """Build out the sequence. Pre allocate runs and determine
        the duration"""
        # pylint: disable=too-many-nested-blocks
        next_run = self._start_time = self._end_time = wash_dt(dt.utcnow())
        for sequence_repeat in range(self._sequence.repeat):
            for sequence_zone in self._sequence.zones:
                if not self._sequence.zone_enabled(sequence_zone, self):
                    continue
                duration = self._sequence.zone_duration_final(
                    sequence_zone, duration_factor, self
                )
                duration_max = timedelta(0)
                delay = self._sequence.zone_delay(sequence_zone, self)
                for zone in sequence_zone.zones:
                    if self.zone_enabled(zone):
                        # Don't adjust manual run and no adjustment on adjustment
                        # This code should not really be here. It would be a breaking
                        # change if removed.
                        if not self.is_manual() and not self._sequence.has_adjustment(
                            True
                        ):
                            duration_adjusted = zone.adjustment.adjust(duration)
                            duration_adjusted = zone.runs.constrain(duration_adjusted)
                        else:
                            duration_adjusted = duration

                        zone_run_time = next_run
                        for zone_repeat in range(  # pylint: disable=unused-variable
                            sequence_zone.repeat
                        ):
                            self._runs_pre_allocate.append(
                                IUSequenceRunAllocation(
                                    zone_run_time,
                                    duration_adjusted,
                                    zone,
                                    IUSequenceZoneRun(
                                        sequence_zone, sequence_repeat, zone_repeat
                                    ),
                                )
                            )
                            if self._first_zone is None:
                                self._first_zone = zone
                            if zone_run_time + duration_adjusted > self._end_time:
                                self._end_time = zone_run_time + duration_adjusted
                            zone_run_time += duration_adjusted + delay
                        duration_max = max(duration_max, zone_run_time - next_run)
                next_run += duration_max

        return self._end_time - self._start_time

    def allocate_runs(self, stime: datetime, start_time: datetime) -> None:
        """Allocate runs"""
        delta = start_time - self._start_time
        self._start_time += delta
        self._end_time += delta
        for item in self._runs_pre_allocate:
            zone = item.zone
            run = zone.runs.add(
                stime, item.start + delta, item.duration, zone, self._schedule, self
            )
            self._runs[run] = item.sequence_zone_run
            self._accumulated_duration += run.duration
            zone.request_update()
        self._runs_pre_allocate.clear()
        self._status = IURunStatus.status(stime, self.start_time, self.end_time)

    def first_zone(self) -> IUZone:
        """Return the first zone"""
        return self._first_zone

    def delete_run(self, run: IURun) -> None:
        """Remove a zone run from this sequence run"""
        self._runs.pop(run)

    @staticmethod
    def _calc_on_time(runs: list[IURun]) -> timedelta:
        """Return the total time this list of runs is on. Accounts for
        overlapping time periods"""
        result = timedelta(0)
        period_start: datetime = None
        period_end: datetime = None

        for run in runs:
            if period_end is None or run.start_time > period_end:
                if period_end is not None:
                    result += period_end - period_start
                period_start = run.start_time
                period_end = run.end_time
            else:
                period_end = max(period_end, run.end_time)
        if period_end is not None:
            result += period_end - period_start
        return result

    def on_time(self, include_expired=False) -> timedelta:
        """Return the total time this run is on"""
        return self._calc_on_time(
            run for run in self._runs if include_expired or not run.expired
        )

    def zone_runs(self, sequence_zone: IUSequenceZone) -> list[IURun]:
        """Get the list of runs associated with the sequence zone"""
        return [
            run for run, sqz in self._runs.items() if sqz.sequence_zone == sequence_zone
        ]

    def run_index(self, run: IURun) -> int:
        """Extract the index from the supplied run"""
        for i, key in enumerate(self._runs):
            if key == run:
                return i
        return None

    def sequence_zone(self, run: IURun) -> IUSequenceZone:
        """Extract the sequence zone from the run"""
        sequence_zone_run = self._runs.get(run, None)
        if sequence_zone_run is not None:
            return sequence_zone_run.sequence_zone
        return None

    def update(self) -> bool:
        """Update the status of the sequence"""
        result = False
        for run, sequence_zone_run in self._runs.items():
            if run.running and not self.running:
                # Sequence/sequence zone is starting
                self._status = IURunStatus.RUNNING
                self._active_zone = sequence_zone_run
                self._coordinator.notify_sequence(
                    EVENT_START,
                    self._controller,
                    self._sequence,
                    self._schedule,
                    self,
                )
                result |= True

            elif run.running and sequence_zone_run != self._active_zone:
                # Sequence zone is changing
                self._active_zone = sequence_zone_run
                result |= True

            elif not run.running and sequence_zone_run == self._active_zone:
                # Sequence zone is finishing
                self._active_zone = None
                if self.run_index(run) == len(self._runs) - 1:
                    # Sequence is finishing
                    self._status = IURunStatus.EXPIRED
                    self._coordinator.notify_sequence(
                        EVENT_FINISH,
                        self._controller,
                        self._sequence,
                        self._schedule,
                        self,
                    )
                result |= True

        return result

    def as_dict(self, include_expired=False) -> dict:
        """Return this sequence run as a dict"""
        result = {}
        result[ATTR_INDEX] = self._sequence.index
        result[ATTR_NAME] = self._sequence.name
        result[ATTR_ENABLED] = self._sequence.enabled
        result[ATTR_SUSPENDED] = self._sequence.suspended
        result[ATTR_STATUS] = self._sequence.status
        result[ATTR_ICON] = self._sequence.icon
        result[ATTR_START] = dt.as_local(self._start_time)
        result[ATTR_DURATION] = to_secs(self.on_time(include_expired))
        result[ATTR_ADJUSTMENT] = str(self._sequence.adjustment)
        if not self.is_manual():
            result[ATTR_SCHEDULE] = {
                ATTR_INDEX: self._schedule.index,
                ATTR_NAME: self._schedule.name,
            }
        else:
            result[ATTR_SCHEDULE] = {
                ATTR_INDEX: None,
                ATTR_NAME: RES_MANUAL,
            }
        result[ATTR_ZONES] = []
        for zone in self._sequence.zones:
            runs = (
                run
                for run in self.zone_runs(zone)
                if include_expired or not run.expired
            )
            sqr = {}
            sqr[ATTR_INDEX] = zone.index
            sqr[ATTR_ENABLED] = zone.enabled
            sqr[ATTR_SUSPENDED] = zone.suspended
            sqr[ATTR_STATUS] = zone.status()
            sqr[ATTR_ICON] = zone.icon()
            sqr[ATTR_DURATION] = to_secs(self._calc_on_time(runs))
            sqr[ATTR_ADJUSTMENT] = str(zone.adjustment)
            sqr[ATTR_ZONE_IDS] = zone.zone_ids
            result[ATTR_ZONES].append(sqr)
        return result

    @staticmethod
    def skeleton(sequence: "IUSequence") -> dict:
        """Return a skeleton dict for when no sequence run is
        active. Must match the as_dict method"""

        result = {}
        result[ATTR_INDEX] = sequence.index
        result[ATTR_NAME] = sequence.name
        result[ATTR_ENABLED] = sequence.enabled
        result[ATTR_SUSPENDED] = sequence.suspended
        result[ATTR_STATUS] = sequence.status
        result[ATTR_ICON] = sequence.icon
        result[ATTR_START] = None
        result[ATTR_DURATION] = 0
        result[ATTR_ADJUSTMENT] = str(sequence.adjustment)
        result[ATTR_SCHEDULE] = {
            ATTR_INDEX: None,
            ATTR_NAME: None,
        }
        result[ATTR_ZONES] = []
        for zone in sequence.zones:
            sqr = {}
            sqr[ATTR_INDEX] = zone.index
            sqr[ATTR_ENABLED] = zone.enabled
            sqr[ATTR_SUSPENDED] = zone.suspended
            sqr[ATTR_STATUS] = zone.status(False)
            sqr[ATTR_ICON] = zone.icon(False)
            sqr[ATTR_DURATION] = 0
            sqr[ATTR_ADJUSTMENT] = str(zone.adjustment)
            sqr[ATTR_ZONE_IDS] = zone.zone_ids
            result[ATTR_ZONES].append(sqr)
        return result


class IUSequenceQueue(list[IUSequenceRun]):
    """Irrigation Unlimited class to hold the upcoming sequences"""

    DAYS_SPAN: int = 3

    def __init__(self) -> None:
        super().__init__()
        # Config parameters
        self._future_span = timedelta(days=self.DAYS_SPAN)
        # Private variables
        self._current_run: IUSequenceRun = None
        self._next_run: IUSequenceRun = None
        self._sorted: bool = False
        self._next_event: datetime = None

    @property
    def current_run(self) -> IUSequenceRun | None:
        """Return the current sequence run"""
        return self._current_run

    @property
    def next_run(self) -> IUSequenceRun | None:
        """Return the next sequence run"""
        return self._next_run

    @property
    def current_duration(self) -> timedelta:
        """Return the current active duration"""
        if self._current_run is not None:
            return self._current_run.total_time
        return timedelta(0)

    @property
    def active_zone(self) -> IUSequenceZoneRun | None:
        """Return the current active sequence zone"""
        if self._current_run is not None:
            return self._current_run.active_zone
        return None

    def active_zone_duration(self, sequence_zone: IUSequenceZone) -> timedelta:
        """Return the current duration for the specified sequence zone"""
        if self._current_run is not None:
            for run in self._current_run.zone_runs(sequence_zone):
                return run.duration
        return timedelta(0)

    def add(self, run: IUSequenceRun) -> IUSequenceRun:
        """Add a sequence run to the queue"""
        self.append(run)
        self._sorted = False
        return run

    def clear_all(self) -> bool:
        """Clear out all runs"""
        if len(self) > 0:
            self._current_run = None
            super().clear()
            return True
        return False

    def clear_runs(self) -> bool:
        """Clear out the queue except for manual and running schedules."""
        modified = False
        i = len(self) - 1
        while i >= 0:
            sqr = self[i]
            if not (sqr.is_manual() or sqr.running):
                sqr = self.pop(i)
                for run in sqr.runs:
                    run.zone.runs.remove_run(run)
                modified = True
            i -= 1
        if modified:
            self._next_run = None
        return modified

    def sort(self) -> bool:
        """Sort the run queue"""

        def sorter(run: IUSequenceRun) -> datetime:
            """Sort call back routine. Items are sorted by start_time"""
            if run.is_manual():
                return datetime.min.replace(tzinfo=dt.UTC)
            return run.start_time

        if self._sorted:
            return False
        super().sort(key=sorter)
        self._current_run = None
        self._next_run = None
        self._sorted = True
        return True

    def remove_expired(self, stime: datetime, postamble: timedelta) -> bool:
        """Remove any expired sequence runs from the queue"""
        if postamble is None:
            postamble = timedelta(0)
        modified: bool = False
        i = len(self) - 1
        while i >= 0:
            sqr = self[i]
            if sqr.expired and stime > sqr.end_time + postamble:
                self._current_run = None
                self._next_run = None
                self.pop(i)
                modified = True
            i -= 1
        return modified

    def update_queue(self) -> IURQStatus:
        """Update the run queue"""
        # pylint: disable=too-many-branches
        status = IURQStatus(0)

        if self.sort():
            status |= IURQStatus.SORTED

        for run in self:
            if run.update():
                self._current_run = None
                self._next_run = None
                status |= IURQStatus.CHANGED

        if self._current_run is None:
            for run in self:
                if run.running and run.on_time() != timedelta(0):
                    self._current_run = run
                    self._next_run = None
                    status |= IURQStatus.UPDATED
                    break

        if self._next_run is None:
            for run in self:
                if not run.running and run.on_time() != timedelta(0):
                    self._next_run = run
                    status |= IURQStatus.UPDATED
                    break

        dates: list[datetime] = [utc_eot()]
        for run in self:
            if run.running:
                dates.append(run.end_time)
            else:
                dates.append(run.start_time)
        self._next_event = min(dates)

        return status

    def as_list(self) -> list:
        """Return a list of runs"""
        return [run.as_dict() for run in self]


class IUSequence(IUBase):
    """Irrigation Unlimited Sequence class"""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: "IUCoordinator",
        controller: "IUController",
        sequence_index: int,
    ) -> None:
        super().__init__(sequence_index)
        # Passed parameters
        self._hass = hass
        self._coordinator = coordinator
        self._controller = controller
        # Config parameters
        self._name: str = None
        self._delay: timedelta = None
        self._duration: timedelta = None
        self._repeat: int = None
        self._enabled: bool = True
        # Private variables
        self._is_on = False
        self._is_paused = False
        self._run_queue = IUSequenceQueue()
        self._schedules: list[IUSchedule] = []
        self._zones: list[IUSequenceZone] = []
        self._adjustment = IUAdjustment()
        self._suspend_until: datetime = None
        self._sensor_update_required: bool = False
        self._sensor_last_update: datetime = None
        self._initialised: bool = False
        self._finalised: bool = False
        self._sequence_sensor: Entity = None
        self._dirty = True

    @property
    def unique_id(self) -> str:
        """Return the HA unique_id for the sequence"""
        return f"c{self._controller.index + 1}_s{self.index + 1}"

    @property
    def entity_base(self) -> str:
        """Return the base of the entity_id. Entity rename
        not currently supported"""
        return self.unique_id

    @property
    def entity_id(self) -> str:
        """Return the HA entity_id for the sequence"""
        return f"{BINARY_SENSOR}.{DOMAIN}_{self.entity_base}"

    @property
    def runs(self) -> IUSequenceQueue:
        """Return the run queue for this sequence"""
        return self._run_queue

    @property
    def sequence_sensor(self) -> Entity:
        """Return the HA entity associated with this sequence"""
        return self._sequence_sensor

    @sequence_sensor.setter
    def sequence_sensor(self, value: Entity) -> None:
        self._sequence_sensor = value

    @property
    def is_setup(self) -> bool:
        """Return True if this sequence is setup and ready to go"""
        self._initialised = self._sequence_sensor is not None

        if self._initialised:
            for schedule in self._schedules:
                self._initialised = self._initialised and schedule.is_setup
        return self._initialised

    @property
    def schedules(self) -> "list[IUSchedule]":
        """Return the list of schedules for this sequence"""
        return self._schedules

    @property
    def zones(self) -> "list[IUSequenceZone]":
        """Return the list of sequence zones"""
        return self._zones

    @property
    def name(self) -> str:
        """Return the friendly name of this sequence"""
        return self._name

    @property
    def delay(self) -> timedelta:
        """Returns the default inter zone delay"""
        return self._delay

    @property
    def duration(self) -> timedelta:
        """Returns the default zone duration"""
        return self._duration

    @property
    def repeat(self) -> int:
        """Returns the number of times to repeat this sequence"""
        return self._repeat

    @property
    def is_enabled(self) -> bool:
        """Return true is this sequence is enabled and not suspended"""
        return self._enabled and self._suspend_until is None

    @property
    def enabled(self) -> bool:
        """Return if this sequence is enabled"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set the enabled state"""
        if value != self._enabled:
            self._enabled = value
            self._dirty = True
            self.request_update()

    @property
    def suspended(self) -> datetime:
        """Return the suspend date"""
        return self._suspend_until

    @suspended.setter
    def suspended(self, value: datetime) -> None:
        """Set the suspend date for this sequence"""
        if value != self._suspend_until:
            self._suspend_until = value
            self._dirty = True
            self.request_update()

    @property
    def adjustment(self) -> IUAdjustment:
        """Returns the sequence adjustment"""
        return self._adjustment

    @property
    def is_on(self) -> bool:
        """Return if the sequence is on or off"""
        return self._is_on

    @property
    def is_paused(self) -> bool:
        """Return is the sequence is paused"""
        return self._is_paused

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self._controller.is_enabled:
            if self.enabled:
                if self.suspended is None:
                    if self.is_on:
                        if self.is_paused:
                            return ICON_SEQUENCE_PAUSED
                        return ICON_SEQUENCE_ON
                    return ICON_SEQUENCE_OFF
                return ICON_SUSPENDED
            return ICON_DISABLED
        return ICON_BLOCKED

    @property
    def status(self) -> str:
        """Return status of the sequence"""
        if self._controller.is_enabled:
            if self.enabled:
                if self.suspended is None:
                    if self.is_on:
                        if self.is_paused:
                            return STATUS_PAUSED
                        return STATE_ON
                    return STATE_OFF
                return STATUS_SUSPENDED
            return STATUS_DISABLED
        return STATUS_BLOCKED

    def has_adjustment(self, deep: bool) -> bool:
        """Indicates if this sequence has an active adjustment"""
        if self._adjustment.has_adjustment:
            return True
        if deep:
            for sequence_zone in self._zones:
                if sequence_zone.is_enabled and sequence_zone.adjustment.has_adjustment:
                    return True
        return False

    def zone_enabled(
        self, sequence_zone: IUSequenceZone, sqr: "IUSequenceRun" = None
    ) -> bool:
        """Return True if at least one real zone referenced by the
        sequence_zone is enabled"""
        if (
            (self._controller.is_enabled or (sqr is not None and sqr.is_manual()))
            and self.is_enabled
            and sequence_zone.is_enabled
        ):
            for zone in sequence_zone.zones:
                if zone.is_enabled or (sqr is not None and sqr.zone_enabled(zone)):
                    return True
        return False

    def constrain(
        self, sequence_zone: IUSequenceZone, duration: timedelta
    ) -> timedelta:
        """Apply the zone entity constraints"""
        for zone in sequence_zone.zones:
            duration = zone.runs.constrain(duration)
        return duration

    def zone_delay_config(self, sequence_zone: IUSequenceZone) -> timedelta:
        """Return the configured (static) delay"""
        if sequence_zone.delay is not None:
            delay = sequence_zone.delay
        else:
            delay = self._delay
        if delay is None:
            delay = timedelta(0)
        return delay

    def zone_delay(
        self, sequence_zone: IUSequenceZone, sqr: "IUSequenceRun"
    ) -> timedelta:
        """Return the delay for the specified zone"""
        if self.zone_enabled(sequence_zone, sqr):
            return self.zone_delay_config(sequence_zone)
        return timedelta(0)

    def total_delay(self, sqr: "IUSequenceRun") -> timedelta:
        """Return the total delay for all the zones"""
        delay = timedelta(0)
        last_zone: IUSequenceZone = None
        if len(self._zones) > 0:
            for zone in self._zones:
                if self.zone_enabled(zone, sqr):
                    delay += self.zone_delay(zone, sqr) * zone.repeat
                    last_zone = zone
            delay *= self._repeat
            if last_zone is not None:
                delay -= self.zone_delay(last_zone, sqr)
        return delay

    def zone_duration_config(self, sequence_zone: IUSequenceZone) -> timedelta:
        """Return the configured (static) duration for the specified zone"""
        if sequence_zone.duration is not None:
            duration = sequence_zone.duration
        else:
            duration = self._duration
        if duration is None:
            duration = granularity_time()
        return duration

    def zone_duration_base(
        self, sequence_zone: IUSequenceZone, sqr: "IUSequenceRun"
    ) -> timedelta:
        """Return the base duration for the specified zone"""
        if self.zone_enabled(sequence_zone, sqr):
            return self.zone_duration_config(sequence_zone)
        return timedelta(0)

    def zone_duration(
        self, sequence_zone: IUSequenceZone, sqr: "IUSequenceRun"
    ) -> timedelta:
        """Return the duration for the specified zone including adjustments
        and constraints"""
        if self.zone_enabled(sequence_zone, sqr):
            duration = self.zone_duration_base(sequence_zone, sqr)
            duration = sequence_zone.adjustment.adjust(duration)
            return self.constrain(sequence_zone, duration)
        return timedelta(0)

    def zone_duration_final(
        self,
        sequence_zone: IUSequenceZone,
        duration_factor: float,
        sqr: "IUSequenceRun",
    ) -> timedelta:
        """Return the final zone time after the factor has been applied"""
        duration = self.zone_duration(sequence_zone, sqr) * duration_factor
        duration = self.constrain(sequence_zone, duration)
        return round_td(duration)

    def total_duration(self, sqr: "IUSequenceRun") -> timedelta:
        """Return the total duration for all the zones"""
        duration = timedelta(0)
        for zone in self._zones:
            duration += self.zone_duration(zone, sqr) * zone.repeat
        duration *= self._repeat
        return duration

    def total_duration_adjusted(
        self, total_duration, sqr: "IUSequenceRun"
    ) -> timedelta:
        """Return the adjusted duration"""
        if total_duration is None:
            total_duration = self.total_duration(sqr)
        if self.has_adjustment(False):
            total_duration = self.adjustment.adjust(total_duration)
            total_duration = max(total_duration, timedelta(0))
        return total_duration

    def total_time_final(
        self, total_time: timedelta, sqr: "IUSequenceRun"
    ) -> timedelta:
        """Return the adjusted total time for the sequence"""
        if total_time is not None and self.has_adjustment(False):
            total_delay = self.total_delay(sqr)
            total_duration = self.total_duration_adjusted(total_time - total_delay, sqr)
            return total_duration + total_delay

        if total_time is None:
            return self.total_duration_adjusted(None, sqr) + self.total_delay(sqr)

        return total_time

    def duration_factor(self, total_time: timedelta, sqr: "IUSequenceRun") -> float:
        """Given a new total run time, calculate how much to shrink or expand each
        zone duration. Final time will be approximate as the new durations must
        be rounded to internal boundaries"""
        total_duration = self.total_duration(sqr)
        if total_time is not None and total_duration != timedelta(0):
            total_delay = self.total_delay(sqr)
            if total_time > total_delay:
                return (total_time - total_delay) / total_duration
            return 0.0
        return 1.0

    def clear(self) -> None:
        """Reset this sequence"""
        self._schedules.clear()

    def add_schedule(self, schedule: IUSchedule) -> IUSchedule:
        """Add a new schedule to the sequence"""
        self._schedules.append(schedule)
        return schedule

    def find_add_schedule(self, index: int) -> IUSchedule:
        """Look for and create if required a schedule"""
        if index >= len(self._schedules):
            return self.add_schedule(IUSchedule(self._hass, self._coordinator, index))
        return self._schedules[index]

    def add_zone(self, zone: IUSequenceZone) -> IUSequenceZone:
        """Add a new zone to the sequence"""
        self._zones.append(zone)
        return zone

    def get_zone(self, index: int) -> IUSequenceZone:
        """Return the specified zone object"""
        if index is not None and index >= 0 and index < len(self._zones):
            return self._zones[index]
        return None

    def find_add_zone(self, index: int) -> IUSequenceZone:
        """Look for and create if required a zone"""
        result = self.get_zone(index)
        if result is None:
            result = self.add_zone(IUSequenceZone(self._controller, self, index))
        return result

    def zone_list(self) -> list[IUZone]:
        """Generator to return all referenced zones"""
        result: set[IUZone] = set()
        for sequence_zone in self._zones:
            result.update(sequence_zone.zones)
        for zone in result:
            yield zone

    def load(self, config: OrderedDict) -> "IUSequence":
        """Load sequence data from the configuration"""
        self.clear()
        self._name = config.get(CONF_NAME, f"Run {self.index + 1}")
        self._delay = wash_td(config.get(CONF_DELAY))
        self._duration = wash_td(config.get(CONF_DURATION))
        self._repeat = config.get(CONF_REPEAT, 1)
        self._enabled = config.get(CONF_ENABLED, self._enabled)
        zidx: int = 0
        for zidx, zone_config in enumerate(config[CONF_ZONES]):
            self.find_add_zone(zidx).load(zone_config)
        while zidx < len(self._zones) - 1:
            self._zones.pop()
        if CONF_SCHEDULES in config:
            for sidx, schedule_config in enumerate(config[CONF_SCHEDULES]):
                self.find_add_schedule(sidx).load(schedule_config)
        self._dirty = True
        return self

    def as_dict(self, sqr: "IUSequenceRun" = None) -> OrderedDict:
        """Return this sequence as a dict"""
        total_delay = self.total_delay(sqr)
        total_duration = self.total_duration(sqr)
        total_duration_adjusted = self.total_duration_adjusted(total_duration, sqr)
        duration_factor = self.duration_factor(
            total_duration_adjusted + total_delay, sqr
        )
        result = OrderedDict()
        result[CONF_INDEX] = self._index
        result[CONF_NAME] = self._name
        result[CONF_STATE] = STATE_ON if self.is_on else STATE_OFF
        result[CONF_ENABLED] = self._enabled
        result[ATTR_SUSPENDED] = self.suspended
        result[ATTR_ICON] = self.icon
        result[ATTR_STATUS] = self.status
        result[ATTR_DEFAULT_DURATION] = self._duration
        result[ATTR_DEFAULT_DELAY] = self._delay
        result[ATTR_DURATION_FACTOR] = duration_factor
        result[ATTR_TOTAL_DELAY] = total_delay
        result[ATTR_TOTAL_DURATION] = total_duration
        result[ATTR_ADJUSTED_DURATION] = total_duration_adjusted
        result[ATTR_CURRENT_DURATION] = self.runs.current_duration
        result[ATTR_ADJUSTMENT] = str(self._adjustment)
        result[CONF_SCHEDULES] = [sch.as_dict() for sch in self._schedules]
        result[CONF_SEQUENCE_ZONES] = [
            szn.as_dict(duration_factor) for szn in self._zones
        ]
        return result

    def muster(self, stime: datetime) -> IURQStatus:
        """Muster this sequence"""
        status = IURQStatus(0)

        if self._dirty:
            self._run_queue.clear_all()
            status |= IURQStatus.CLEARED

        if self._suspend_until is not None and stime >= self._suspend_until:
            self._suspend_until = None
            status |= IURQStatus.CHANGED

        for sequence_zone in self._zones:
            status |= sequence_zone.muster(stime)

        self._dirty = False
        return status

    def check_run(self, stime: datetime, parent_enabled: bool) -> bool:
        """Update the run status"""
        # pylint: disable=unused-argument
        is_running = parent_enabled and (
            self.is_enabled
            and self._run_queue.current_run is not None
            and self._run_queue.current_run.running
        )

        state_changed = is_running ^ self._is_on
        if state_changed:
            self._is_on = not self._is_on
            self.request_update()

        is_paused = is_running and self._run_queue.current_run.active_zone is None
        if is_paused ^ self._is_paused:
            self._is_paused = not self._is_paused
            self.request_update()

        return state_changed

    def request_update(self) -> None:
        """Flag the sensor needs an update"""
        self._sensor_update_required = True

    def update_sensor(self, stime: datetime, do_on: bool) -> bool:
        """Lazy sensor updater"""
        updated: bool = False
        do_update: bool = False

        if self._sequence_sensor is not None:
            if do_on is False:
                do_update = not self.is_on and self._sensor_update_required
            else:
                if self.is_on:
                    # If we are running then update sensor according to refresh_interval
                    do_update = (
                        self._sensor_last_update is None
                        or stime - self._sensor_last_update
                        >= self._coordinator.refresh_interval
                    )
                    do_update |= self._sensor_update_required
        else:
            do_update = False

        if do_update:
            self._sequence_sensor.schedule_update_ha_state()
            self._sensor_update_required = False
            self._sensor_last_update = stime
            updated = True

        return updated

    def next_awakening(self) -> datetime:
        """Return the next event time"""
        dates: list[datetime] = [utc_eot()]
        dates.append(self._suspend_until)
        dates.extend(sqz.next_awakening() for sqz in self._zones)
        return min(d for d in dates if d is not None)

    def finalise(self) -> None:
        """Shutdown the sequence"""
        if not self._finalised:
            self._finalised = True


class IUController(IUBase):
    """Irrigation Unlimited Controller (Master) class"""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods
    def __init__(
        self, hass: HomeAssistant, coordinator: "IUCoordinator", controller_index: int
    ) -> None:
        # Passed parameters
        super().__init__(controller_index)
        self._hass = hass
        self._coordinator = coordinator  # Parent
        # Config parameters
        self._enabled: bool = True
        self._name: str = None
        self._controller_id: str = None
        self._preamble: timedelta = None
        self._postamble: timedelta = None
        self._queue_manual: bool = False
        # Private variables
        self._initialised: bool = False
        self._finalised: bool = False
        self._zones: list[IUZone] = []
        self._sequences: list[IUSequence] = []
        self._run_queue = IUZoneQueue()
        self._switch = IUSwitch(hass, coordinator, self, None)
        self._master_sensor: Entity = None
        self._is_on: bool = False
        self._sensor_update_required: bool = False
        self._sensor_last_update: datetime = None
        self._suspend_until: datetime = None
        self._volume = IUVolume(hass, coordinator)
        self._user = IUUser()
        self._dirty: bool = True

    @property
    def controller_id(self) -> str:
        """Return the controller_id for the controller entity"""
        return self._controller_id

    @property
    def unique_id(self) -> str:
        """Return the HA unique_id for the controller entity"""
        return f"c{self.index + 1}_m"

    @property
    def entity_base(self) -> str:
        """Return the base entity_id"""
        if self._coordinator.rename_entities:
            return self._controller_id
        return self.unique_id

    @property
    def entity_id(self) -> str:
        """Return the HA entity_id for the controller entity"""
        return f"{BINARY_SENSOR}.{DOMAIN}_{self.entity_base}"

    @property
    def zones(self) -> "list[IUZone]":
        """Return a list of children zones"""
        return self._zones

    @property
    def sequences(self) -> "list[IUSequence]":
        """Return a list of children sequences"""
        return self._sequences

    @property
    def runs(self) -> IUZoneQueue:
        """Return the master run queue"""
        return self._run_queue

    @property
    def name(self) -> str:
        """Return the friendly name for the controller"""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return if the controller is on or off"""
        return self._is_on

    @property
    def is_setup(self) -> bool:
        """Indicate if the controller is setup and ready to go"""
        return self._is_setup()

    @property
    def is_enabled(self) -> bool:
        """Return true if this controller is enabled and not suspended"""
        return self._enabled and self._suspend_until is None

    @property
    def enabled(self) -> bool:
        """Return true is this controller is enabled"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable/disable this controller"""
        if value != self._enabled:
            self._enabled = value
            self._dirty = True
            self.request_update(True)

    @property
    def suspended(self) -> datetime:
        """Return the suspend date"""
        return self._suspend_until

    @suspended.setter
    def suspended(self, value: datetime) -> None:
        """Set the suspend date for this controller"""
        if value != self._suspend_until:
            self._suspend_until = value
            self._dirty = True
            self.request_update(True)

    @property
    def master_sensor(self) -> Entity:
        """Return the associated HA entity"""
        return self._master_sensor

    @master_sensor.setter
    def master_sensor(self, value: Entity) -> None:
        self._master_sensor = value

    @property
    def preamble(self) -> timedelta:
        """Return the preamble time for the controller"""
        return self._preamble

    @property
    def queue_manual(self) -> bool:
        """Return if manual runs should be queue"""
        return self._queue_manual

    @property
    def status(self) -> str:
        """Return the state of the controller"""
        return self._status()

    @property
    def is_paused(self) -> bool:
        """Returns True if the controller is running a sequence. The
        controller may be off because of a delay between sequence zones"""
        return self._run_queue.in_sequence

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self.enabled:
            if self.suspended is None:
                if self.is_on:
                    return ICON_CONTROLLER_ON
                if self.is_paused:
                    return ICON_CONTROLLER_PAUSED
                return ICON_CONTROLLER_OFF
            return ICON_SUSPENDED
        return ICON_DISABLED

    @property
    def user(self) -> dict:
        """Return the arbitrary user information"""
        return self._user

    @property
    def volume(self) -> IUVolume:
        """Return the volume for this zone"""
        return self._volume

    def _status(self) -> str:
        """Return status of the controller"""
        if self._initialised:
            if self.enabled:
                if self.suspended is None:
                    if self._is_on:
                        return STATE_ON
                    if self._run_queue.in_sequence:
                        return STATUS_PAUSED
                    return STATE_OFF
                return STATUS_SUSPENDED
            return STATUS_DISABLED
        return STATUS_INITIALISING

    def _is_setup(self) -> bool:
        self._initialised = self._master_sensor is not None

        if self._initialised:
            for zone in self._zones:
                self._initialised = self._initialised and zone.is_setup
            for sequence in self._sequences:
                self._initialised = self._initialised and sequence.is_setup
        return self._initialised

    def add_zone(self, zone: IUZone) -> IUZone:
        """Add a new zone to the controller"""
        self._zones.append(zone)
        return zone

    def get_zone(self, index: int) -> IUZone:
        """Return the zone by index"""
        if index is not None and index >= 0 and index < len(self._zones):
            return self._zones[index]
        return None

    def find_add_zone(
        self, coordinator: "IUCoordinator", controller: "IUController", index: int
    ) -> IUZone:
        """Locate and create if required the zone object"""
        if index >= len(self._zones):
            return self.add_zone(IUZone(self._hass, coordinator, controller, index))
        return self._zones[index]

    def add_sequence(self, sequence: IUSequence) -> IUSequence:
        """Add a new sequence to the controller"""
        self._sequences.append(sequence)
        return sequence

    def get_sequence(self, index: int) -> IUSequence:
        """Locate the sequence by index"""
        if index is not None and index >= 0 and index < len(self._sequences):
            return self._sequences[index]
        return None

    def find_add_sequence(self, index: int) -> IUSequence:
        """Locate and create if required a sequence"""
        if index >= len(self._sequences):
            return self.add_sequence(
                IUSequence(self._hass, self._coordinator, self, index)
            )
        return self._sequences[index]

    def find_zone_by_zone_id(self, zone_id: str) -> IUZone:
        """Find the real zone from a zone_id"""
        for zone in self._zones:
            if zone.zone_id == zone_id:
                return zone
        return None

    def clear(self) -> None:
        """Clear out the controller"""
        # Don't clear zones
        # self._zones.clear()
        self._run_queue.clear_all()

    def clear_zone_runs(self, zone: IUZone) -> None:
        """Clear out zone run queues"""
        zone.runs.clear_runs()
        for sequence in self._sequences:
            if zone in sequence.zone_list():
                sequence.runs.clear_runs()

    def load(self, config: OrderedDict) -> "IUController":
        """Load config data for the controller"""
        self.clear()
        self._enabled = config.get(CONF_ENABLED, self._enabled)
        self._name = config.get(CONF_NAME, f"Controller {self.index + 1}")
        self._controller_id = config.get(CONF_CONTROLLER_ID, str(self.index + 1))
        self._preamble = wash_td(config.get(CONF_PREAMBLE))
        self._postamble = wash_td(config.get(CONF_POSTAMBLE))
        self._queue_manual = config.get(CONF_QUEUE_MANUAL, self._queue_manual)
        all_zones = config.get(CONF_ALL_ZONES_CONFIG)
        zidx: int = 0
        for zidx, zone_config in enumerate(config[CONF_ZONES]):
            self.find_add_zone(self._coordinator, self, zidx).load(
                zone_config, all_zones
            )
        while zidx < len(self._zones) - 1:
            self._zones.pop().finalise(True)

        if CONF_SEQUENCES in config:
            qidx: int = 0
            for qidx, sequence_config in enumerate(config[CONF_SEQUENCES]):
                self.find_add_sequence(qidx).load(sequence_config)
            while qidx < len(self._sequences) - 1:
                self._sequences.pop()
        else:
            self._sequences.clear()

        self._switch.load(config, None)
        self._volume.load(config, None)
        self._user.load(config, None)
        self._dirty = True
        return self

    def finalise(self, turn_off: bool) -> None:
        """Shutdown this controller"""
        if not self._finalised:
            for zone in self._zones:
                zone.finalise(turn_off)
            if turn_off and self._is_on:
                self.call_switch(False)
            self.clear()
            self._finalised = True

    def as_dict(self) -> OrderedDict:
        """Return this controller as a dict"""
        result = OrderedDict()
        result[CONF_INDEX] = self._index
        result[CONF_NAME] = self._name
        result[CONF_CONTROLLER_ID] = self._controller_id
        result[CONF_ENTITY_BASE] = self.entity_base
        result[CONF_STATE] = STATE_ON if self.is_on else STATE_OFF
        result[CONF_ENABLED] = self._enabled
        result[ATTR_SUSPENDED] = self.suspended
        result[CONF_ICON] = self.icon
        result[ATTR_STATUS] = self.status
        result[CONF_ZONES] = [zone.as_dict() for zone in self._zones]
        result[CONF_SEQUENCES] = [seq.as_dict() for seq in self._sequences]
        return result

    def sequence_runs(self) -> list[IUSequenceRun]:
        """Gather all the sequence runs"""
        result: list[IUSequenceRun] = []
        for sequence in self._sequences:
            for run in sequence.runs:
                result.append(run)
        return result

    def up_next(self) -> dict[IUSequence, IUSequenceRun]:
        """Return a list of sequences and their next start times filtered"""
        sequences: dict[IUSequence, IUSequenceRun] = {}
        for run in self.sequence_runs():
            if not run.expired:
                sample = sequences.get(run.sequence)
                if sample is None or run.start_time < sample.start_time:
                    sequences[run.sequence] = run
        return sequences

    def sequence_status(self, include_expired=False) -> list[dict]:
        """Return the sequence status or run information"""
        result: list[dict] = []
        runs = self.up_next()
        for sequence in self._sequences:
            run = runs.get(sequence)
            if run is not None:
                result.append(run.as_dict(include_expired))
            else:
                result.append(IUSequenceRun.skeleton(sequence))
        return result

    def muster_sequence(
        self,
        stime: datetime,
        sequence: IUSequence,
        schedule: IUSchedule,
        total_time: timedelta = None,
    ) -> IURQStatus:
        # pylint: disable=too-many-locals, too-many-statements
        """Muster the sequences for the controller"""

        def init_run_time(
            stime: datetime,
            sequence: IUSequence,
            schedule: IUSchedule,
            zone: IUZone,
            total_duration: timedelta,
        ) -> datetime:
            def is_running(sequence: IUSequence, schedule: IUSchedule) -> bool:
                """Return True is this sequence & schedule is currently running"""
                for srn in sequence.runs:
                    if srn.schedule == schedule and srn.running:
                        return True
                return False

            def find_last_run(sequence: IUSequence, schedule: IUSchedule) -> IURun:
                result: IUSequenceRun = None
                next_time: datetime = None
                for sqr in sequence.runs:
                    if sqr.schedule == schedule:
                        for run in sqr.runs:
                            if next_time is None or run.end_time > next_time:
                                next_time = run.start_time
                                result = run
                return result

            if schedule is not None:
                last_run = find_last_run(sequence, schedule)
                if last_run is not None:
                    next_time = last_run.sequence_run.end_time
                else:
                    next_time = stime
                next_run = schedule.get_next_run(
                    next_time,
                    zone.runs.last_time(stime),
                    total_duration,
                    is_running(sequence, schedule),
                )
            else:
                next_run = stime
            return next_run

        status = IURQStatus(0)
        sequence_run = IUSequenceRun(self._coordinator, self, sequence, schedule)
        total_time = sequence_run.calc_total_time(total_time)
        duration_factor = sequence.duration_factor(total_time, sequence_run)

        total_time = sequence_run.build(duration_factor)
        if total_time > timedelta(0):
            start_time = init_run_time(
                stime, sequence, schedule, sequence_run.first_zone(), total_time
            )
            if start_time is not None:
                sequence_run.allocate_runs(stime, start_time)
                sequence.runs.add(sequence_run)
                status |= IURQStatus.EXTENDED
        return status

    def muster(self, stime: datetime, force: bool) -> IURQStatus:
        """Calculate run times for this controller. This is where most of the hard yakka
        is done."""
        # pylint: disable=too-many-branches
        status = IURQStatus(0)

        if self._dirty or force:
            self._run_queue.clear_all()
            for sequence in self._sequences:
                sequence.runs.clear_all()
            for zone in self._zones:
                zone.clear_run_queue()
            status |= IURQStatus.CLEARED
        else:
            for zone in self._zones:
                zone.runs.update_run_status(stime)
            self._run_queue.update_run_status(stime)

        if self._suspend_until is not None and stime >= self._suspend_until:
            self._suspend_until = None
            status |= IURQStatus.CHANGED

        self._switch.muster(stime)

        zone_status = IURQStatus(0)

        # Handle initialisation
        for zone in self._zones:
            zone_status |= zone.muster(stime)

        for sequence in self._sequences:
            sms = sequence.muster(stime)
            if not sms.is_empty():
                sequence.runs.clear_runs()
                zone_status |= sms

        if not self._coordinator.tester.enabled or self._coordinator.tester.is_testing:
            # pylint: disable=too-many-nested-blocks
            # Process sequence schedules
            for sequence in self._sequences:
                if sequence.is_enabled:
                    for schedule in sequence.schedules:
                        if not schedule.enabled:
                            continue
                        next_time = stime
                        while True:
                            if self.muster_sequence(
                                next_time, sequence, schedule, None
                            ).is_empty():
                                break
                            zone_status |= IURQStatus.EXTENDED

            # Process zone schedules
            for zone in self._zones:
                if zone.is_enabled:
                    zone_status |= zone.muster_schedules(stime)

        # Post processing
        for sequence in self._sequences:
            zone_status |= sequence.runs.update_queue()

        for zone in self._zones:
            zts = zone.runs.update_queue()
            if IURQStatus.CANCELED in zts:
                zone.request_update()
            zone_status |= zts

        if zone_status.has_any(
            IURQStatus.CLEARED
            | IURQStatus.EXTENDED
            | IURQStatus.SORTED
            | IURQStatus.CANCELED
            | IURQStatus.CHANGED
        ):
            clear_all = zone_status.has_any(IURQStatus.CLEARED | IURQStatus.CANCELED)
            status |= self._run_queue.rebuild_schedule(
                stime, self._zones, self._preamble, self._postamble, clear_all
            )
        status |= self._run_queue.update_queue()

        # Purge expired runs
        for sequence in self._sequences:
            if sequence.runs.remove_expired(stime, self._postamble):
                zone_status |= IURQStatus.REDUCED
        for zone in self._zones:
            if zone.runs.remove_expired(stime, self._postamble):
                status |= IURQStatus.REDUCED
        if self._run_queue.remove_expired(stime, None):
            status |= IURQStatus.REDUCED

        if not status.is_empty():
            self.request_update(False)

        self._dirty = False
        return status | zone_status

    def check_run(self, stime: datetime) -> bool:
        """Check the run status and update sensors. Return flag
        if anything has changed."""

        for sequence in self._sequences:
            sequence.check_run(stime, self.is_enabled)

        zones_changed: list[int] = []

        run = self._run_queue.current_run
        is_enabled = self.is_enabled or (run is not None and run.is_manual())
        is_running = is_enabled and run is not None
        state_changed = is_running ^ self._is_on

        # Gather zones that have changed status
        for zone in self._zones:
            if zone.check_run(is_enabled):
                zones_changed.append(zone.index)

        # Handle off zones before master
        for zone in (self._zones[i] for i in zones_changed):
            if not zone.is_on:
                zone.call_switch(zone.is_on, stime)
                zone.volume.end_record(stime)

        # Check if master has changed and update
        if state_changed:
            self._is_on = not self._is_on
            self.request_update(False)
            self.call_switch(self._is_on, stime)
            if self._is_on:
                self._volume.start_record(stime)
            else:
                self._volume.end_record(stime)

        # Handle on zones after master
        for zone in (self._zones[i] for i in zones_changed):
            if zone.is_on:
                zone.call_switch(zone.is_on, stime)
                zone.volume.start_record(stime)

        return state_changed

    def check_links(self) -> bool:
        """Check inter object links"""

        result = True
        zone_ids = set()
        for zone in self._zones:
            if zone.zone_id in zone_ids:
                self._coordinator.logger.log_duplicate_id(self, zone, None)
                result = False
            else:
                zone_ids.add(zone.zone_id)

        for sequence in self._sequences:
            for sequence_zone in sequence.zones:
                for zone_id in sequence_zone.zone_ids:
                    if zone_id not in zone_ids:
                        self._coordinator.logger.log_orphan_id(
                            self, sequence, sequence_zone, zone_id
                        )
                        result = False
        return result

    def request_update(self, deep: bool) -> None:
        """Flag the sensor needs an update. The actual update is done
        in update_sensor"""
        self._sensor_update_required = True
        if deep:
            for zone in self._zones:
                zone.request_update()

            for sequence in self._sequences:
                sequence.request_update()

    def update_sensor(self, stime: datetime) -> None:
        """Lazy sensor updater."""
        self._run_queue.update_sensor(stime)

        for zone in self._zones:
            zone.update_sensor(stime, False)

        for sequence in self._sequences:
            sequence.update_sensor(stime, False)

        if self._master_sensor is not None:
            do_update: bool = self._sensor_update_required

            # If we are running then update sensor according to refresh_interval
            if self._run_queue.current_run is not None:
                do_update = (
                    do_update
                    or self._sensor_last_update is None
                    or stime - self._sensor_last_update
                    >= self._coordinator.refresh_interval
                )

            if do_update:
                self._master_sensor.schedule_update_ha_state()
                self._sensor_update_required = False
                self._sensor_last_update = stime

        for zone in self._zones:
            zone.update_sensor(stime, True)

        for sequence in self._sequences:
            sequence.update_sensor(stime, True)

    def next_awakening(self) -> datetime:
        """Return the next event time"""
        dates: list[datetime] = [
            self._run_queue.next_event(),
            self._switch.next_event(),
            self._suspend_until,
        ]
        dates.extend(zone.next_awakening() for zone in self._zones)
        dates.extend(seq.next_awakening() for seq in self._sequences)
        if self._is_on and self._sensor_last_update is not None:
            dates.append(self._sensor_last_update + self._coordinator.refresh_interval)
        return min(d for d in dates if d is not None)

    def check_switch(self, resync: bool, stime: datetime) -> list[str]:
        """Check the linked entity is in sync"""
        result = self._switch.check_switch(stime, resync, True)
        for zone in self._zones:
            result.extend(zone.check_switch(resync, stime))

        return result

    def call_switch(self, state: bool, stime: datetime = None) -> None:
        """Update the linked entity if enabled"""
        self._switch.call_switch(state, stime)
        self._coordinator.status_changed(stime, self, None, state)

    def check_item(self, index: int, items: list[int] | None) -> bool:
        """If items is None or contains only a 0 (match all) then
        return True. Otherwise check if index + 1 is in the list"""
        return (
            items is None or (items is not None and items == [0]) or index + 1 in items
        )

    def decode_sequence_id(
        self, stime: datetime, sequence_id: int | None
    ) -> list[int] | None:
        """Convert supplied 1's based id into a list of sequence
        indexes and validate"""
        if sequence_id is None:
            return None
        sequence_list: list[int] = []
        if sequence_id == 0:
            sequence_list.extend(sequence.index for sequence in self._sequences)
        else:
            if self.get_sequence(sequence_id - 1) is not None:
                sequence_list.append(sequence_id - 1)
            else:
                self._coordinator.logger.log_invalid_sequence(stime, self, sequence_id)
        return sequence_list

    def manual_run_start(
        self, stime: datetime, delay: timedelta, queue: bool
    ) -> datetime:
        """Determine the next available start time for a manual run"""
        nst = wash_dt(stime)
        if not self._is_on:
            nst += granularity_time()
        if (
            self.preamble is not None
            and self.preamble > timedelta(0)
            and not self.is_on
        ):
            nst += self.preamble
        if queue:
            end_times: list[datetime] = []
            for zone in self._zones:
                end_times.extend(run.end_time for run in zone.runs if run.is_manual())
            if len(end_times) > 0:
                nst = max(end_times) + delay
        return nst

    def suspend_until_date(
        self,
        data: MappingProxyType,
        stime: datetime,
    ) -> datetime:
        """Determine the suspend date and time"""
        if CONF_UNTIL in data:
            suspend_time = dt.as_utc(data[CONF_UNTIL])
        elif CONF_FOR in data:
            suspend_time = stime + data[CONF_FOR]
        else:
            suspend_time = None
        return wash_dt(suspend_time)

    def service_call(
        self, data: MappingProxyType, stime: datetime, service: str
    ) -> bool:
        """Handler for enable/disable/toggle service call"""
        # pylint: disable=too-many-branches, too-many-nested-blocks

        def s2b(test: bool, service: str) -> bool:
            """Convert the service code to bool"""
            if service == SERVICE_ENABLE:
                return True
            if service == SERVICE_DISABLE:
                return False
            return not test  # Must be SERVICE_TOGGLE

        result = False
        zone_list: list[int] = data.get(CONF_ZONES)
        sequence_list = self.decode_sequence_id(stime, data.get(CONF_SEQUENCE_ID))
        if sequence_list is None:
            new_state = s2b(self.enabled, service)
            if self.enabled != new_state:
                self.enabled = new_state
                result = True
        else:
            sequences_changed = False
            for sequence in (self.get_sequence(sqid) for sqid in sequence_list):
                changed = False
                if zone_list is None:
                    new_state = s2b(sequence.enabled, service)
                    if sequence.enabled != new_state:
                        sequence.enabled = new_state
                        changed = True
                else:
                    for sequence_zone in sequence.zones:
                        if self.check_item(sequence_zone.index, zone_list):
                            new_state = s2b(sequence_zone.enabled, service)
                            if sequence_zone.enabled != new_state:
                                sequence_zone.enabled = new_state
                                changed = True
                if changed:
                    sequence.runs.clear_runs()
                    sequences_changed = True
            if sequences_changed:
                self._run_queue.clear_runs()
                self.request_update(True)
                result = True
        return result

    def service_suspend(self, data: MappingProxyType, stime: datetime) -> bool:
        """Handler for the suspend service call"""
        # pylint: disable=too-many-nested-blocks
        result = False
        suspend_time = self.suspend_until_date(data, stime)
        sequence_list = self.decode_sequence_id(stime, data.get(CONF_SEQUENCE_ID))
        if sequence_list is None:
            if suspend_time != self._suspend_until:
                self.suspended = suspend_time
                result = True
        else:
            zone_list: list[int] = data.get(CONF_ZONES)
            sequences_changed = False
            for sequence in (self.get_sequence(sqid) for sqid in sequence_list):
                changed = False
                if zone_list is None:
                    if sequence.suspended != suspend_time:
                        sequence.suspended = suspend_time
                        changed = True
                else:
                    for sequence_zone in sequence.zones:
                        if self.check_item(sequence_zone.index, zone_list):
                            if sequence_zone.suspended != suspend_time:
                                sequence_zone.suspended = suspend_time
                                changed = True
                if changed:
                    sequence.runs.clear_runs()
                    sequences_changed = True
            if sequences_changed:
                self._run_queue.clear_runs()
                self.request_update(True)
                result = True
        return result

    def service_adjust_time(self, data: MappingProxyType, stime: datetime) -> bool:
        """Handler for the adjust_time service call"""
        # pylint: disable=too-many-nested-blocks
        result = False
        zone_list: list[int] = data.get(CONF_ZONES)
        sequence_list = self.decode_sequence_id(stime, data.get(CONF_SEQUENCE_ID))
        if sequence_list is None:
            for zone in self._zones:
                if self.check_item(zone.index, zone_list):
                    if zone.service_adjust_time(data, stime):
                        self.clear_zone_runs(zone)
                        result = True
        else:
            sequences_changed = False
            for sequence in (self.get_sequence(sqid) for sqid in sequence_list):
                changed = False
                if zone_list is None:
                    changed = sequence.adjustment.load(data)
                else:
                    for sequence_zone in sequence.zones:
                        if self.check_item(sequence_zone.index, zone_list):
                            changed |= sequence_zone.adjustment.load(data)
                if changed:
                    sequence.runs.clear_runs()
                    sequences_changed = True
            if sequences_changed:
                self._run_queue.clear_runs()
                self.request_update(True)
                result = True
        return result

    def service_manual_run(self, data: MappingProxyType, stime: datetime) -> None:
        """Handler for the manual_run service call"""
        sequence_id = data.get(CONF_SEQUENCE_ID, None)
        if sequence_id is None:
            zone_list: list[int] = data.get(CONF_ZONES, None)
            for zone in self._zones:
                if zone_list is None or zone.index + 1 in zone_list:
                    zone.service_manual_run(data, stime)
        else:
            sequence = self.get_sequence(sequence_id - 1)
            if sequence is not None:
                duration = wash_td(data.get(CONF_TIME))
                delay = wash_td(data.get(CONF_DELAY, timedelta(0)))
                queue = data.get(CONF_QUEUE, self._queue_manual)
                if duration is not None and duration == timedelta(0):
                    duration = None
                self.muster_sequence(
                    self.manual_run_start(stime, delay, queue), sequence, None, duration
                )
            else:
                self._coordinator.logger.log_invalid_sequence(stime, self, sequence_id)

    def service_cancel(self, data: MappingProxyType, stime: datetime) -> None:
        """Handler for the cancel service call"""
        zone_list: list[int] = data.get(CONF_ZONES, None)
        for zone in self._zones:
            if zone_list is None or zone.index + 1 in zone_list:
                zone.service_cancel(data, stime)


class IUEvent:
    """This class represents a single event"""

    def __init__(self) -> None:
        # Private variables
        self._time: datetime = None
        self._controller: int = None
        self._zone: int = None
        self._state: bool = None
        self._crumbs: str = None

    def __eq__(self, other: "IUEvent") -> bool:
        return (
            self._time == other._time
            and self._controller == other.controller
            and self._zone == other.zone
            and self._state == other.state
        )

    def __str__(self) -> str:
        return (
            f"{{t: '{dt2lstr(self._time)}', "
            f"c: {self._controller}, "
            f"z: {self._zone}, "
            f"s: {str(int(self._state))}}}"
        )

    @property
    def time(self) -> datetime:
        """Return the time property"""
        return self._time

    @property
    def controller(self) -> int:
        """Return the controller property"""
        return self._controller

    @property
    def zone(self) -> int:
        """Return the zone property"""
        return self._zone

    @property
    def state(self) -> bool:
        """Return the state property"""
        return self._state

    @property
    def crumbs(self) -> str:
        """Return the tracking information"""
        return self._crumbs

    def load(self, config: OrderedDict) -> "IUEvent":
        """Initialise from a config"""
        self._time: datetime = wash_dt(dt.as_utc(config["t"]))
        self._controller: int = config["c"]
        self._zone: int = config["z"]
        self._state: bool = config["s"]
        return self

    def load2(
        self, stime: datetime, controller: int, zone: int, state: bool, crumbs: str
    ) -> "IUEvent":
        """Initialise from individual components"""
        # pylint: disable=too-many-arguments
        self._time = stime
        self._controller = controller
        self._zone = zone
        self._state = state
        self._crumbs = crumbs
        return self


class IUTest(IUBase):
    """This class represents a single test. Contains a list of
    expected results."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, test_index: int, speed: float) -> None:
        # Passed parameters
        super().__init__(test_index)
        self._speed = speed
        # Config parameters
        self._name: str = None
        self._start: datetime = None
        self._end: datetime = None
        self._results: list[IUEvent] = []
        # Private variables
        self._current_result: int = 0
        self._events: int = 0
        self._checks: int = 0
        self._errors: int = 0
        self._perf_mon: int = 0
        self._delta: timedelta = None
        self._test_time: float = 0

    @property
    def name(self) -> str:
        """Return the friendly name for this test"""
        return self._name

    @property
    def start(self) -> datetime:
        """Return the start time for this test"""
        return self._start

    @property
    def end(self) -> datetime:
        """Return the end time for this test"""
        return self._end

    @property
    def events(self) -> int:
        """Return the number of events received"""
        return self._events

    @property
    def checks(self) -> int:
        """Return the number of checks performed"""
        return self._checks

    @property
    def errors(self) -> int:
        """Return the number of errors identified"""
        return self._errors

    @property
    def test_time(self) -> float:
        """Return the test run time"""
        return self._test_time

    @property
    def virtual_duration(self) -> timedelta:
        """Return the real duration"""
        return (self._end - self._start) / self._speed

    @property
    def total_results(self) -> int:
        """Return the number of expected results from the test"""
        return len(self._results)

    def is_finished(self, atime) -> bool:
        """Indicate if this test has finished"""
        return self.virtual_time(atime) >= self._end

    def next_result(self) -> IUEvent:
        """Return the next result"""
        if self._current_result < len(self._results):
            result = self._results[self._current_result]
            self._current_result += 1
            return result
        return None

    def check_result(self, result: IUEvent, event: IUEvent) -> bool:
        """Compare the expected result and the event"""
        self._events += 1
        if result is not None:
            self._checks += 1
            if result != event:
                self._errors += 1
                return False
        else:
            return False
        return True

    def clear(self) -> None:
        """Remove all the results"""
        self._results.clear()

    def load(self, config: OrderedDict):
        """Load the configuration"""
        self.clear()
        self._start = wash_dt(dt.as_utc(config[CONF_START]))
        self._end = wash_dt(dt.as_utc(config[CONF_END]))
        self._name = config.get(CONF_NAME, None)
        if CONF_RESULTS in config:
            for result in config[CONF_RESULTS]:
                self._results.append(IUEvent().load(result))
        return self

    def begin_test(self, atime: datetime) -> None:
        """Start test"""
        self._delta = atime - self._start
        self._perf_mon = tm.perf_counter()
        self._current_result = 0
        self._events = 0
        self._checks = 0
        self._errors = 0
        self._test_time = 0

    def end_test(self) -> None:
        """Finalise test"""
        self._test_time = tm.perf_counter() - self._perf_mon

    def virtual_time(self, atime: datetime) -> datetime:
        """Return the virtual clock. For testing we can speed
        up time. This routine will return a virtual time based
        on the real time and the duration from start. It is in
        effect a test warp speed"""
        virtual_start: datetime = atime - self._delta
        actual_duration: float = (virtual_start - self._start).total_seconds()
        virtual_duration: float = actual_duration * self._speed
        vtime = self._start + timedelta(seconds=virtual_duration)
        # The conversion may not be exact due to the internal precision
        # of the compiler particularly at high speed values. Compensate
        # by rounding if the value is very close to an internal boundary
        vtime_rounded = round_dt(vtime)
        if abs(vtime - vtime_rounded) < timedelta(microseconds=100000):
            return vtime_rounded
        return vtime

    def actual_time(self, stime: datetime) -> datetime:
        """Return the actual time from the virtual time"""
        virtual_duration = (stime - self._start).total_seconds()
        actual_duration = virtual_duration / self._speed
        return self._start + self._delta + timedelta(seconds=actual_duration)


class IUTester:
    """Irrigation Unlimited testing class"""

    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    def __init__(self, coordinator: "IUCoordinator") -> None:
        # Passed parameters
        self._coordinator = coordinator
        # Config parameters
        self._enabled: bool = False
        self._speed: float = None
        self._output_events: bool = None
        self._show_log: bool = None
        self._autoplay: bool = None
        # Private variables
        self._tests: list[IUTest] = []
        self._test_initialised = False
        self._running_test: int = None
        self._last_test: int = None
        self._autoplay_initialised: bool = False
        self._ticker: datetime = None
        self._tests_completed: set[int] = set()
        self.load(None)

    @property
    def enabled(self) -> bool:
        """Return the enabled property"""
        return self._enabled

    @property
    def speed(self) -> float:
        """Return the test speed"""
        return self._speed

    @property
    def is_testing(self) -> bool:
        """Indicate if this test is running"""
        return self._is_testing()

    @property
    def tests(self) -> "list[IUTest]":
        """Return the list of tests to perform"""
        return self._tests

    @property
    def current_test(self) -> IUTest:
        """Returns the current test"""
        if self._running_test is not None and self._running_test < len(self._tests):
            return self._tests[self._running_test]
        return None

    @property
    def last_test(self) -> IUTest:
        """Returns the last test that was run"""
        if self._last_test is not None and self._last_test < len(self._tests):
            return self._tests[self._last_test]
        return None

    @property
    def total_events(self) -> int:
        """Returns the total number of events received"""
        result: int = 0
        for test in self._tests:
            result += test.events
        return result

    @property
    def total_checks(self) -> int:
        """Returns the total number of checks performed"""
        result: int = 0
        for test in self._tests:
            result += test.checks
        return result

    @property
    def total_errors(self) -> int:
        """Returns the number of errors detected"""
        result: int = 0
        for test in self._tests:
            result += test.errors
        return result

    @property
    def total_time(self) -> float:
        """Returns the total amount of time to run tests"""
        result: float = 0
        for test in self._tests:
            result += test.test_time
        return result

    @property
    def total_tests(self) -> int:
        """Returns the number of tests to run"""
        return len(self._tests)

    @property
    def total_virtual_duration(self) -> timedelta:
        """Returns the real time duration of the tests"""
        result = timedelta(0)
        for test in self._tests:
            result += test.virtual_duration
        return result

    @property
    def total_results(self) -> int:
        """Returns the total number of results expected"""
        result: int = 0
        for test in self._tests:
            result += test.total_results
        return result

    @property
    def tests_completed(self) -> int:
        """Return the number of tests completed"""
        return len(self._tests_completed)

    @property
    def ticker(self) -> datetime:
        """Return the tester clock"""
        return self._ticker

    @ticker.setter
    def ticker(self, value: datetime) -> None:
        """Set the tester clock"""
        self._ticker = value

    def virtual_time(self, atime: datetime) -> datetime:
        """Convert actual time to virtual time"""
        if self.is_testing:
            return self.current_test.virtual_time(atime)
        return atime

    def actual_time(self, stime: datetime) -> datetime:
        """Convert virtual time to actual time"""
        if self.is_testing:
            return self.current_test.actual_time(stime)
        return stime

    def start_test(self, test_no: int, atime: datetime) -> IUTest:
        """Start the test"""
        self._ticker = atime
        if 0 < test_no <= len(self._tests):
            self._running_test = test_no - 1  # 0-based
            test = self._tests[self._running_test]
            test.begin_test(atime)
            if self._show_log:
                self._coordinator.logger.log_test_start(
                    test.virtual_time(atime), test, INFO
                )
            else:
                self._coordinator.logger.log_test_start(test.virtual_time(atime), test)
            self._test_initialised = False
        else:
            self._running_test = None
        return self.current_test

    def end_test(self, atime: datetime) -> None:
        """Finish the test"""
        test = self.current_test
        if test is not None:
            test.end_test()
            if self._show_log:
                self._coordinator.logger.log_test_end(
                    test.virtual_time(atime), test, INFO
                )
            else:
                self._coordinator.logger.log_test_end(test.virtual_time(atime), test)
            self._tests_completed.add(self._running_test)
        self._last_test = self._running_test
        self._running_test = None

    def next_test(self, atime: datetime) -> IUTest:
        """Run the next test"""
        current = self._running_test  # This is 0-based
        self.end_test(atime)
        return self.start_test(current + 2, atime)  # This takes 1-based

    def _is_testing(self) -> bool:
        return self._enabled and self._running_test is not None

    def clear(self) -> None:
        """Reset the tester"""
        # Private variables
        self._tests.clear()
        self._test_initialised = False
        self._running_test = None
        self._last_test = None
        self._autoplay_initialised = False
        self._ticker: datetime = None
        self._tests_completed.clear()

    def load(self, config: OrderedDict) -> "IUTester":
        """Load config data for the tester"""
        # Config parameters
        self.clear()
        if config is None:
            config = {}
        self._enabled: bool = config.get(CONF_ENABLED, False)
        self._speed: float = config.get(CONF_SPEED, DEFAULT_TEST_SPEED)
        self._output_events: bool = config.get(CONF_OUTPUT_EVENTS, False)
        self._show_log: bool = config.get(CONF_SHOW_LOG, True)
        self._autoplay: bool = config.get(CONF_AUTOPLAY, True)
        if CONF_TIMES in config:
            for tidx, test in enumerate(config[CONF_TIMES]):
                self._tests.append(IUTest(tidx, self._speed).load(test))
        return self

    def poll_test(self, atime: datetime, poll_func) -> None:
        """Polling is diverted here when testing is enabled. atime is the actual time
        but is converted to a virtual time for testing. The main polling function
        is then called with the modified time"""
        if self._autoplay and not self._autoplay_initialised:
            self.start_test(1, atime)
            self._autoplay_initialised = True

        test = self.current_test
        if test is not None:
            if not self._test_initialised:
                poll_func(test.start, True)
                self._test_initialised = True
            elif test.is_finished(atime):  # End of current test
                poll_func(test.end, False)
                if self._autoplay:
                    test = self.next_test(atime)
                    if test is not None:
                        poll_func(test.start, True)
                        self._test_initialised = True
                    else:  # All tests finished
                        if self._show_log:
                            self._coordinator.logger.log_test_completed(
                                self.total_checks, self.total_errors, INFO
                            )
                        else:
                            self._coordinator.logger.log_test_completed(
                                self.total_checks, self.total_errors
                            )
                        poll_func(atime, True)
                else:  # End single test
                    self.end_test(atime)
            else:  # Continue existing test
                poll_func(test.virtual_time(atime))
        else:  # Out of tests to run
            poll_func(atime)

    def entity_state_changed(self, event: IUEvent) -> None:
        """Called when an entity has changed state"""

        def check_state(event: IUEvent):
            """Check the event against the next result"""
            test = self.current_test
            if test is not None:
                result = test.next_result()
                if not test.check_result(result, event):
                    if not self._output_events:
                        if self._show_log:
                            self._coordinator.logger.log_test_error(
                                test, event, result, ERROR
                            )
                        else:
                            self._coordinator.logger.log_test_error(test, event, result)

        if not self._output_events:
            if self._show_log:
                self._coordinator.logger.log_event(event, INFO)
            else:
                self._coordinator.logger.log_event(event)
        else:
            print(str(event))
        check_state(event)


class IULogger:
    """Irrigation Unlimited logger class"""

    # pylint: disable=too-many-public-methods

    def __init__(self, logger: Logger) -> None:
        # Passed parameters
        self._logger = logger
        # Config parameters
        # Private variables

    def load(self, config: OrderedDict) -> "IULogger":
        """Load config data for the tester"""
        if config is None:
            config = {}
        return self

    def _output(self, level: int, msg: str) -> None:
        """Send out the message"""
        self._logger.log(level, msg)

    def _format(
        self, level, area: str, stime: datetime = None, data: str = None
    ) -> None:
        """Format and send out message"""
        msg = area
        if stime is not None:
            msg += f" [{dt2lstr(stime)}]"
        if data is not None:
            msg += " " + data
        self._output(level, msg)

    def log_start(self, stime: datetime) -> None:
        """Message for system clock starting"""
        self._format(DEBUG, "START", stime)

    def log_stop(self, stime: datetime) -> None:
        """Message for system clock stopping"""
        self._format(DEBUG, "STOP", stime)

    def log_load(self, data: OrderedDict) -> None:
        """Message that the config is loaded"""
        # pylint: disable=unused-argument
        self._format(DEBUG, "LOAD")

    def log_initialised(self) -> None:
        """Message that the system is initialised and ready to go"""
        self._format(DEBUG, "INITIALISED")

    def log_event(self, event: IUEvent, level=DEBUG) -> None:
        """Message that an event has occurred - controller or zone turning on or off"""
        if len(event.crumbs) != 0:
            result = (
                f"controller: {event.controller:d}, "
                f"zone: {event.zone:d}, "
                f"state: {str(int(event.state))}, "
                f"data: {event.crumbs}"
            )
        else:
            result = (
                f"controller: {event.controller:d}, "
                f"zone: {event.zone:d}, "
                f"state: {str(int(event.state))}"
            )
        self._format(level, "EVENT", event.time, result)

    def log_service_call(
        self,
        service: str,
        stime: datetime,
        controller: IUController,
        zone: IUZone,
        data: MappingProxyType,
        level=INFO,
    ) -> None:
        """Message that we have received a service call"""
        # pylint: disable=too-many-arguments
        idl = IUBase.idl([controller, zone], "0", 1)
        self._format(
            level,
            "CALL",
            stime,
            f"service: {service}, "
            f"controller: {idl[0]}, "
            f"zone: {idl[1]}, "
            f"data: {json.dumps(data, default=str)}",
        )

    def log_register_entity(
        # pylint: disable=too-many-arguments
        self,
        stime: datetime,
        controller: IUController,
        zone: IUZone,
        sequence: IUSequence,
        entity: Entity,
    ) -> None:
        """Message that HA has registered an entity"""
        idl = IUBase.idl([controller, zone, sequence], "0", 1)
        self._format(
            DEBUG,
            "REGISTER",
            stime,
            f"controller: {idl[0]}, "
            f"zone: {idl[1]}, "
            f"sequence: {idl[2]}, "
            f"entity: {entity.entity_id}",
        )

    def log_deregister_entity(
        # pylint: disable=too-many-arguments
        self,
        stime: datetime,
        controller: IUController,
        zone: IUZone,
        sequence: IUSequence,
        entity: Entity,
    ) -> None:
        """Message that HA is removing an entity"""
        idl = IUBase.idl([controller, zone, sequence], "0", 1)
        self._format(
            DEBUG,
            "DEREGISTER",
            stime,
            f"controller: {idl[0]}, "
            f"zone: {idl[1]}, "
            f"sequence: {idl[2]}, "
            f"entity: {entity.entity_id}",
        )

    def log_test_start(self, vtime: datetime, test: IUTest, level=DEBUG) -> None:
        """Message that a test is starting"""
        self._format(
            level,
            "TEST_START",
            vtime,
            f"test: {test.index + 1:d}, "
            f"start: {dt2lstr(test.start)}, "
            f"end: {dt2lstr(test.end)}",
        )

    def log_test_end(self, vtime: datetime, test: IUTest, level=DEBUG) -> None:
        """Message that a test has finished"""
        self._format(level, "TEST_END", vtime, f"test: {test.index + 1:d}")

    def log_test_error(
        self, test: IUTest, actual: IUEvent, expected: IUEvent, level=DEBUG
    ) -> None:
        """Message that an event did not meet expected result"""
        self._format(
            level,
            "TEST_ERROR",
            None,
            f"test: {test.index + 1:d}, "
            f"actual: {str(actual)}, "
            f"expected: {str(expected)}",
        )

    def log_test_completed(self, checks: int, errors: int, level=DEBUG) -> None:
        """Message that all tests have been completed"""
        self._format(
            level,
            "TEST_COMPLETED",
            None,
            f"(Idle): checks: {checks:d}, errors: {errors:d}",
        )

    def log_sequence_entity(self, vtime: datetime, level=WARNING) -> None:
        """Warn that a service call involved a sequence but was not directed
        at the controller"""
        self._format(level, "ENTITY", vtime, "Sequence specified but entity_id is zone")

    def log_invalid_sequence(
        self, vtime: datetime, controller: IUController, sequence_id: int, level=WARNING
    ) -> None:
        """Warn that a service call with a sequence_id is invalid"""
        self._format(
            level,
            "SEQUENCE_ID",
            vtime,
            f"Invalid sequence id: "
            f"controller: {IUBase.ids(controller, '0', 1)}, "
            f"sequence: {sequence_id}",
        )

    def log_invalid_restore_data(self, msg: str, data: str, level=WARNING) -> None:
        """Warn invalid restore data"""
        self._format(level, "RESTORE", None, f"Invalid data: msg: {msg}, data: {data}")

    def log_incomplete_cycle(
        self,
        controller: IUController,
        zone: IUZone,
        sequence: IUSequence,
        sequence_zone: IUSequenceZone,
        level=WARNING,
    ) -> None:
        """Warn that a cycle did not complete"""
        # pylint: disable=too-many-arguments
        idl = IUBase.idl([controller, zone, sequence, sequence_zone], "-", 1)
        self._format(
            level,
            "INCOMPLETE",
            None,
            f"Cycle did not complete: "
            f"controller: {idl[0]}, "
            f"zone: {idl[1]}, "
            f"sequence: {idl[2]}, "
            f"sequence_zone: {idl[3]}",
        )

    def log_sync_error(
        self, vtime: datetime, expected: str, switch_entity_id: str, level=WARNING
    ) -> None:
        """Warn that switch and entity are out of sync"""
        self._format(
            level,
            "SYNCHRONISATION",
            vtime,
            f"Switch does not match current state: "
            f"expected: {expected}, "
            f"switch: {switch_entity_id}",
        )

    def log_switch_error(
        self, vtime: datetime, expected: str, switch_entity_id: list[str], level=ERROR
    ) -> None:
        """Warn that switch(s) was unable to be set"""
        self._format(
            level,
            "SWITCH_ERROR",
            vtime,
            f"Unable to set switch state: "
            f"expected: {expected}, "
            f"switch: {','.join(switch_entity_id)}",
        )

    def log_duplicate_id(
        self,
        controller: IUController,
        zone: IUZone,
        schedule: IUSchedule,
        level=WARNING,
    ) -> None:
        """Warn a controller/zone/schedule has a duplicate id"""
        idl = IUBase.idl([controller, zone, schedule], "0", 1)
        if not zone and not schedule:
            self._format(
                level,
                "DUPLICATE_ID",
                None,
                f"Duplicate Controller ID: "
                f"controller: {idl[0]}, "
                f"controller_id: {controller.controller_id}",
            )
        elif zone and not schedule:
            self._format(
                level,
                "DUPLICATE_ID",
                None,
                f"Duplicate Zone ID: "
                f"controller: {idl[0]}, "
                f"controller_id: {controller.controller_id}, "
                f"zone: {idl[1]}, "
                f"zone_id: {zone.zone_id if zone else ''}",
            )
        elif zone and schedule:
            self._format(
                level,
                "DUPLICATE_ID",
                None,
                f"Duplicate Schedule ID (zone): "
                f"controller: {idl[0]}, "
                f"controller_id: {controller.controller_id}, "
                f"zone: {idl[1]}, "
                f"zone_id: {zone.zone_id if zone else ''}, "
                f"schedule: {idl[2]}, "
                f"schedule_id: {schedule.schedule_id if schedule else ''}",
            )
        else:  # not zone and schedule
            self._format(
                level,
                "DUPLICATE_ID",
                None,
                f"Duplicate Schedule ID (sequence): "
                f"controller: {idl[0]}, "
                f"controller_id: {controller.controller_id}, "
                f"schedule: {idl[2]}, "
                f"schedule_id: {schedule.schedule_id if schedule else ''}",
            )

    def log_orphan_id(
        self,
        controller: IUController,
        sequence: IUSequence,
        sequence_zone: IUSequenceZone,
        zone_id: str,
        level=WARNING,
    ) -> None:
        # pylint: disable=too-many-arguments
        """Warn a zone_id reference is orphaned"""
        idl = IUBase.idl([controller, sequence, sequence_zone], "0", 1)
        self._format(
            level,
            "ORPHAN_ID",
            None,
            f"Invalid reference ID: "
            f"controller: {idl[0]}, "
            f"sequence: {idl[1]}, "
            f"sequence_zone: {idl[2]}, "
            f"zone_id: {zone_id}",
        )

    def log_invalid_crontab(
        self,
        stime: datetime,
        schedule: IUSchedule,
        expression: str,
        msg: str,
        level=ERROR,
    ) -> None:
        # pylint: disable=too-many-arguments
        """Warn that a crontab expression in the schedule is invalid"""
        self._format(
            level,
            "CRON",
            stime,
            f"schedule: {schedule.name}, "
            f"expression: {expression}, "
            f"error: {msg}",
        )

    def log_invalid_meter_id(
        self, stime: datetime, entity_id: str, level=ERROR
    ) -> None:
        """Warn the volume meter is invalid"""
        self._format(level, "VOLUME_SENSOR", stime, f"entity_id: {entity_id}")

    def log_invalid_meter_value(self, stime: datetime, value: str, level=ERROR) -> None:
        """Warn the volume meter value is invalid"""
        self._format(level, "VOLUME_VALUE", stime, f"value: {value}")


class IUClock:
    """Irrigation Unlimited Clock class"""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: "IUCoordinator",
        action: Callable[[datetime], Awaitable[None]],
    ) -> None:
        # Pass parameters
        self._hass = hass
        self._coordinator = coordinator
        self._action = action
        # Private variables
        self._listener_job = HassJob(self._listener)
        self._remove_timer_listener: CALLBACK_TYPE = None
        self._tick_log = deque["datetime"](maxlen=DEFAULT_MAX_LOG_ENTRIES)
        self._next_tick: datetime = None
        self._fixed_clock = False
        self._show_log = False
        self._finalised = False

    @property
    def is_fixed(self) -> bool:
        """Return if the clock is fixed or variable"""
        return self._fixed_clock

    @property
    def next_tick(self) -> datetime:
        """Return the next anticipated scheduled tick. It
        may however be cancelled due to a service call"""
        return self._next_tick

    @property
    def tick_log(self) -> deque["datetime"]:
        """Return the tick history log"""
        return self._tick_log

    @property
    def show_log(self) -> bool:
        """Indicate if we should show the tick log"""
        return self._show_log

    def track_interval(self) -> timedelta:
        """Returns the system clock time interval"""
        track_time = SYSTEM_GRANULARITY / self._coordinator.tester.speed
        track_time *= 0.95  # Run clock slightly ahead of required to avoid skipping
        return min(timedelta(seconds=track_time), self._coordinator.refresh_interval)

    def start(self) -> None:
        """Start the system clock"""
        self.stop()
        now = dt.utcnow()
        self._schedule_next_poll(now)
        self._coordinator.logger.log_start(now)

    def stop(self) -> None:
        """Stop the system clock"""
        if self._remove_timer():
            self._coordinator.logger.log_stop(dt.utcnow())

    def next_awakening(self, atime: datetime) -> datetime:
        """Return the time for the next event"""
        if self._finalised:
            return utc_eot()
        if not self._coordinator.initialised:
            return atime + timedelta(seconds=5)
        if self._fixed_clock:
            return atime + self.track_interval()

        # Handle testing
        if self._coordinator.tester.is_testing:
            next_stime = self._coordinator.next_awakening()
            next_stime = min(next_stime, self._coordinator.tester.current_test.end)
            result = self._coordinator.tester.actual_time(next_stime)
        else:
            result = self._coordinator.next_awakening()

        # Midnight rollover
        if result == utc_eot() or (
            dt.as_local(self._coordinator.tester.virtual_time(atime)).toordinal()
            != dt.as_local(self._coordinator.tester.virtual_time(result)).toordinal()
        ):
            local_tomorrow = dt.as_local(
                self._coordinator.tester.virtual_time(atime)
            ) + timedelta(days=1)
            local_midnight = local_tomorrow.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            result = dt.as_utc(self._coordinator.tester.actual_time(local_midnight))

        # Sanity check
        if result < atime:
            result = atime + granularity_time()

        return result

    def _update_next_tick(self, atime: datetime) -> bool:
        """Update the next_tick variable"""
        if atime != self._next_tick:
            self._next_tick = atime
            if self._show_log:
                self._coordinator.request_update(False)
            return True
        return False

    def _add_to_log(self, atime: datetime) -> bool:
        """Add a time to the head of tick log"""
        if not self._fixed_clock and atime is not None:
            self._tick_log.appendleft(atime)
            if self._show_log:
                self._coordinator.request_update(False)
            return True
        return False

    def _remove_timer(self) -> None:
        """Remove the current timer. Return False if there is
        no timer currently active (clock is stopped)"""
        if self._remove_timer_listener is not None:
            self._remove_timer_listener()
            self._remove_timer_listener = None
            return True
        return False

    def _schedule_next_poll(self, atime: datetime) -> None:
        """Set the timer for the next update"""
        self._update_next_tick(self.next_awakening(atime))

        self._remove_timer_listener = async_track_point_in_utc_time(
            self._hass, self._listener_job, self._next_tick
        )

    async def _listener(self, atime: datetime) -> None:
        """Listener for the timer event"""
        self._add_to_log(atime)
        try:
            await self._action(atime)
        finally:
            self._schedule_next_poll(atime)
        if self._show_log:
            self._coordinator.update_sensor(atime, False)

    def test_ticker_update(self, atime: datetime) -> bool:
        """Interface for testing unit when starting tick"""
        if self._update_next_tick(atime) and self._show_log:
            self._coordinator.update_sensor(atime, False)
            return True
        return False

    def test_ticker_fired(self, atime: datetime) -> bool:
        """Interface for testing unit when finishing tick"""
        if self._add_to_log(atime) and self._show_log:
            self._coordinator.update_sensor(atime, False)
            return True
        return False

    def rearm(self, atime: datetime) -> None:
        """Rearm the timer"""
        if not self._fixed_clock and self._remove_timer():
            self._schedule_next_poll(atime)
            if self._show_log:
                self._coordinator.update_sensor(atime, False)

    def load(self, config: OrderedDict) -> "IUClock":
        """Load config data"""
        if config is not None and CONF_CLOCK in config:
            clock_conf: dict = config[CONF_CLOCK]
            self._fixed_clock = clock_conf[CONF_MODE] == CONF_FIXED
            self._show_log = clock_conf[CONF_SHOW_LOG]
            if (
                max_entries := clock_conf.get(CONF_MAX_LOG_ENTRIES)
            ) is not None and max_entries != self._tick_log.maxlen:
                self._tick_log = deque["datetime"](maxlen=max_entries)

        if not self._fixed_clock:
            global SYSTEM_GRANULARITY  # pylint: disable=global-statement
            SYSTEM_GRANULARITY = 1

        return self

    def finalise(self):
        """finalise this unit"""
        if not self._finalised:
            self._remove_timer()
            self._finalised = True


class IUCoordinator:
    """Irrigation Unlimited Coordinator class"""

    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    def __init__(self, hass: HomeAssistant) -> None:
        # Passed parameters
        self._hass = hass
        # Config parameters
        self._refresh_interval: timedelta = None
        # Private variables
        self._controllers: list[IUController] = []
        self._is_on: bool = False
        self._sensor_update_required: bool = False
        self._sensor_last_update: datetime = None
        self._dirty: bool = True
        self._component: Entity = None
        self._initialised: bool = False
        self._last_tick: datetime = None
        self._last_muster: datetime = None
        self._muster_required: bool = False
        self._remove_shutdown_listener: CALLBACK_TYPE = None
        self._logger = IULogger(_LOGGER)
        self._tester = IUTester(self)
        self._clock = IUClock(self._hass, self, self._async_timer)
        self._history = IUHistory(self._hass, self.service_history)
        self._restored_from_configuration: bool = False
        self._sync_switches: bool = True
        self._rename_entities = False
        self._finalised = False

    @property
    def entity_id(self) -> str:
        """Return the entity_id for the coordinator"""
        return f"{DOMAIN}.{COORDINATOR}"

    @property
    def controllers(self) -> "list[IUController]":
        """Return the list of controllers"""
        return self._controllers

    @property
    def clock(self) -> IUClock:
        """Return the clock object"""
        return self._clock

    @property
    def tester(self) -> IUTester:
        """Return the tester object"""
        return self._tester

    @property
    def logger(self) -> IULogger:
        """Return the logger object"""
        return self._logger

    @property
    def history(self) -> IUHistory:
        """Return the history object"""
        return self._history

    @property
    def is_setup(self) -> bool:
        """Indicate if system is setup"""
        return self._is_setup()

    @property
    def component(self) -> Entity:
        """Return the HA integration entity"""
        return self._component

    @property
    def refresh_interval(self) -> timedelta:
        """Returns the refresh_interval property"""
        return self._refresh_interval

    @property
    def initialised(self) -> bool:
        """Return True if we are initialised"""
        return self._initialised

    @property
    def finalised(self) -> bool:
        """Return True if we have been finalised"""
        return self._finalised

    @property
    def configuration(self) -> str:
        """Return the system configuration as JSON"""
        return json.dumps(self.as_dict(), cls=IUJSONEncoder)

    @property
    def restored_from_configuration(self) -> bool:
        """Return if the system has been restored from coordinator date"""
        return self._restored_from_configuration

    @restored_from_configuration.setter
    def restored_from_configuration(self, value: bool) -> None:
        """Flag the system has been restored from coordinator data"""
        self._restored_from_configuration = value

    @property
    def rename_entities(self) -> bool:
        """Indicate if entity renaming is allowed"""
        return self._rename_entities

    def _is_setup(self) -> bool:
        """Wait for sensors to be setup"""
        all_setup: bool = self._hass.is_running and self._component is not None
        for controller in self._controllers:
            all_setup = all_setup and controller.is_setup
        return all_setup

    def initialise(self) -> None:
        """Flag we need to re-initialise. Called by the testing unit when
        starting a new test"""
        self._initialised = False

    def add(self, controller: IUController) -> IUController:
        """Add a new controller to the system"""
        self._controllers.append(controller)
        return controller

    def get(self, index: int) -> IUController:
        """Return the controller by index"""
        if index is not None and index >= 0 and index < len(self._controllers):
            return self._controllers[index]
        return None

    def find_add(self, coordinator: "IUCoordinator", index: int) -> IUController:
        """Locate and create if required a controller"""
        if index >= len(self._controllers):
            return self.add(IUController(self._hass, coordinator, index))
        return self._controllers[index]

    def clear(self) -> None:
        """Reset the coordinator"""
        # Don't clear controllers
        # self._controllers.clear()
        self._is_on: bool = False

    def load(self, config: OrderedDict) -> "IUCoordinator":
        """Load config data for the system"""
        self.clear()

        global SYSTEM_GRANULARITY  # pylint: disable=global-statement
        SYSTEM_GRANULARITY = config.get(CONF_GRANULARITY, DEFAULT_GRANULARITY)
        self._clock.load(config)

        self._refresh_interval = timedelta(
            seconds=config.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL)
        )
        self._sync_switches = config.get(CONF_SYNC_SWITCHES, True)
        self._rename_entities = config.get(CONF_RENAME_ENTITIES, self._rename_entities)

        cidx: int = 0
        for cidx, controller_config in enumerate(config[CONF_CONTROLLERS]):
            self.find_add(self, cidx).load(controller_config)
        while cidx < len(self._controllers) - 1:
            self._controllers.pop().finalise(True)

        self._tester.load(config.get(CONF_TESTING))
        self._logger.load(config.get(CONF_LOGGING))

        self._dirty = True
        self._muster_required = True
        self.request_update(False)
        self._logger.log_load(config)
        self._history.load(config, self._clock.is_fixed)

        self.check_links()

        return self

    def as_dict(self) -> OrderedDict:
        """Returns the coordinator as a dict"""
        result = OrderedDict()
        result[CONF_VERSION] = "1.0.0"
        result[CONF_CONTROLLERS] = [ctr.as_dict() for ctr in self._controllers]
        return result

    def muster(self, stime: datetime, force: bool) -> IURQStatus:
        """Calculate run times for system"""
        status = IURQStatus(0)

        self._history.muster(stime, force)

        for controller in self._controllers:
            status |= controller.muster(stime, force)
        self._dirty = False

        return status

    def check_run(self, stime: datetime) -> bool:
        """Update run status. Return True if any entities in
        the tree have changed."""
        status_changed: bool = False

        for controller in self._controllers:
            status_changed |= controller.check_run(stime)

        return status_changed

    def check_links(self) -> bool:
        """Check inter object links"""
        # pylint: disable=too-many-branches
        result = True

        controller_ids = set()
        for controller in self._controllers:
            if controller.controller_id in controller_ids:
                self._logger.log_duplicate_id(controller, None, None)
                result = False
            else:
                controller_ids.add(controller.controller_id)
            if not controller.check_links():
                result = False

        schedule_ids = set()
        for controller in self._controllers:
            for zone in controller.zones:
                for schedule in zone.schedules:
                    if schedule.schedule_id is not None:
                        if schedule.schedule_id in schedule_ids:
                            self._logger.log_duplicate_id(controller, zone, schedule)
                            result = False
                        else:
                            schedule_ids.add(schedule.schedule_id)
            for sequence in controller.sequences:
                for schedule in sequence.schedules:
                    if schedule.schedule_id is not None:
                        if schedule.schedule_id in schedule_ids:
                            self._logger.log_duplicate_id(controller, None, schedule)
                            result = False
                        else:
                            schedule_ids.add(schedule.schedule_id)

        return result

    def request_update(self, deep: bool) -> None:
        """Flag the sensor needs an update. The actual update is done
        in update_sensor"""
        self._sensor_update_required = True
        if deep:
            for controller in self._controllers:
                controller.request_update(True)

    def update_sensor(self, stime: datetime, deep: bool = True) -> None:
        """Update home assistant sensors if required"""
        stime = wash_dt(stime, 1)
        if deep:
            for controller in self._controllers:
                controller.update_sensor(stime)

        if self._component is not None and self._sensor_update_required:
            self._component.schedule_update_ha_state()
            self._sensor_update_required = False
            self._sensor_last_update = stime

    def poll(self, vtime: datetime, force: bool = False) -> None:
        """Poll the system for changes, updates and refreshes.
        vtime is the virtual time if in testing mode, if not then
        it is the actual time"""
        wtime: datetime = wash_dt(vtime)
        if (wtime != self._last_muster) or self._muster_required or force:
            if not self.muster(wtime, force).is_empty():
                self.check_run(wtime)
            self._muster_required = False
            self._last_muster = wtime
        self.update_sensor(vtime)

    def poll_main(self, atime: datetime, force: bool = False) -> None:
        """Post initialisation worker. Divert to testing unit if
        enabled. atime (actual time) is the real world clock"""
        if self._tester.enabled:
            self._tester.poll_test(atime, self.poll)
        else:
            self.poll(atime, force)

    def timer(self, atime: datetime) -> None:
        """System clock entry point"""
        self._last_tick = atime
        if self._initialised:
            self.poll_main(atime)
        else:
            self._initialised = self.is_setup
            if self._initialised:
                self._logger.log_initialised()
                self.check_switches(self._sync_switches, atime)
                self.request_update(True)
                self.poll_main(atime)

    async def _async_timer(self, atime: datetime) -> None:
        """Timer callback"""
        self.timer(atime)

    def finalise(self, turn_off: bool) -> None:
        """Tear down the system and clean up"""
        if not self._finalised:
            for controller in self._controllers:
                controller.finalise(turn_off)
            self._clock.finalise()
            self._history.finalise()
            self._finalised = True

    async def _async_shutdown_listener(self, event: HAEvent) -> None:
        """Home Assistant is shutting down. Attempting to turn off any running
        valves is unlikely to work as the underlying libraries are also in a
        state of shutdown (zwave, zigbee, WiFi). Should this situation change
        then set the following to True."""
        # pylint: disable=unused-argument
        self.finalise(False)

    def listen(self) -> None:
        """Listen for events. This appears to be the earliest signal HA
        sends to tell us we are going down. It would be nice to have some sort
        of heads up while everything is still running. This would enable us to
        tidy up."""
        self._remove_shutdown_listener = self._hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, self._async_shutdown_listener
        )

    async def _async_replay_last_timer(self, atime: datetime) -> None:
        """Update after a service call"""
        self.request_update(False)
        self._muster_required = True
        if self._tester.is_testing:
            tick = self._tester.ticker
        elif self._last_tick is not None:
            tick = self._last_tick
        else:
            return
        self.timer(tick)
        self._clock.rearm(atime)

    def next_awakening(self) -> datetime:
        """Return the next event time"""
        dates: list[datetime] = [utc_eot()]
        dates.extend(ctr.next_awakening() for ctr in self._controllers)
        return min(d for d in dates if d is not None)

    def check_switches(self, resync: bool, stime: datetime) -> list[str]:
        """Check if entities match current status"""
        result: list[str] = []
        for controller in self._controllers:
            result.extend(controller.check_switch(resync, stime))
        return result

    def notify_sequence(
        self,
        event_type: str,
        controller: IUController,
        sequence: IUSequence,
        schedule: IUSchedule,
        sequence_run: IUSequenceRun,
    ) -> None:
        """Send out a notification for start/finish to a sequence"""
        # pylint: disable=too-many-arguments
        data = {
            CONF_CONTROLLER: {CONF_INDEX: controller.index, CONF_NAME: controller.name},
            CONF_SEQUENCE: {CONF_INDEX: sequence.index, CONF_NAME: sequence.name},
            CONF_RUN: {CONF_DURATION: round(sequence_run.total_time.total_seconds())},
        }
        if schedule is not None:
            data[CONF_SCHEDULE] = {CONF_INDEX: schedule.index, CONF_NAME: schedule.name}
        else:
            data[CONF_SCHEDULE] = {CONF_INDEX: None, CONF_NAME: RES_MANUAL}
        self._hass.bus.fire(f"{DOMAIN}_{event_type}", data)

    def notify_switch(
        self,
        event_type: str,
        expected: str,
        entities: list[str],
        controller: IUController,
        zone: IUZone,
    ) -> None:
        """Send out notification about switch resync event"""
        # pylint: disable=too-many-arguments
        data = {
            CONF_EXPECTED: expected,
            CONF_ENTITY_ID: ",".join(entities),
            CONF_CONTROLLER: {CONF_INDEX: controller.index, CONF_NAME: controller.name},
        }
        if zone is not None:
            data[CONF_ZONE] = {CONF_INDEX: zone.index, CONF_NAME: zone.name}
        else:
            data[CONF_ZONE] = {CONF_INDEX: None, CONF_NAME: None}
        self._hass.bus.fire(f"{DOMAIN}_{event_type}", data)

    def register_entity(
        self,
        controller: IUController,
        zone: IUZone,
        sequence: IUSequence,
        entity: Entity,
    ) -> None:
        """A HA entity has been registered"""
        stime = self.service_time()
        if sequence is not None:
            sequence.sequence_sensor = entity
        elif zone is not None:
            zone.zone_sensor = entity
        elif controller is not None:
            controller.master_sensor = entity
        else:
            self._component = entity
        self._logger.log_register_entity(stime, controller, zone, sequence, entity)

    def deregister_entity(
        self,
        controller: IUController,
        zone: IUZone,
        sequence: IUSequence,
        entity: Entity,
    ) -> None:
        """A HA entity has been removed"""
        stime = self.service_time()
        if sequence is not None:
            sequence.finalise()
            sequence.sequence_sensor = None
        elif zone is not None:
            zone.finalise(True)
            zone.zone_sensor = None
        elif controller is not None:
            controller.finalise(True)
            controller.master_sensor = None
        else:
            self.finalise(True)
            self._component = None
        self._logger.log_deregister_entity(stime, controller, zone, sequence, entity)

    def service_time(self) -> datetime:
        """Return a time midway between last and next future tick"""
        if self._tester.is_testing:
            result = self._tester.ticker
            result = self._tester.virtual_time(result)
        elif self._clock.is_fixed and self._last_tick is not None:
            result = self._last_tick + self._clock.track_interval() / 2
        else:
            result = dt.utcnow()
        return wash_dt(result)

    def service_load_schedule(self, data: MappingProxyType) -> None:
        """Handle the load_schedule service call"""
        # pylint: disable=too-many-nested-blocks
        for controller in self._controllers:
            for zone in controller.zones:
                for schedule in zone.schedules:
                    if schedule.schedule_id == data[CONF_SCHEDULE_ID]:
                        schedule.load(data, True)
                        runs: list[IURun] = []
                        for run in zone.runs:
                            if not run.is_sequence and run.schedule == schedule:
                                runs.append(run)
                        for run in runs:
                            zone.runs.remove_run(run)
                        return

            for sequence in controller.sequences:
                for schedule in sequence.schedules:
                    if schedule.schedule_id == data[CONF_SCHEDULE_ID]:
                        schedule.load(data, True)
                        sequence.runs.clear_runs()
                        return

    def service_call(
        self,
        service: str,
        controller: IUController,
        zone: IUZone,
        data: MappingProxyType,
    ) -> None:
        """Entry point for all service calls."""
        # pylint: disable=too-many-branches
        changed = True
        stime = self.service_time()

        self._logger.log_service_call(service, stime, controller, zone, data, DEBUG)

        data1 = dict(data)

        if service in [SERVICE_ENABLE, SERVICE_DISABLE, SERVICE_TOGGLE]:
            if zone is not None:
                if changed := zone.service_call(data1, stime, service):
                    controller.clear_zone_runs(zone)
            else:
                changed = controller.service_call(data1, stime, service)
        elif service == SERVICE_SUSPEND:
            render_positive_time_period(data1, CONF_FOR)
            if zone is not None:
                if changed := zone.service_suspend(data1, stime):
                    controller.clear_zone_runs(zone)
            else:
                changed = controller.service_suspend(data1, stime)

        elif service == SERVICE_CANCEL:
            if zone is not None:
                zone.service_cancel(data1, stime)
            else:
                controller.service_cancel(data1, stime)
        elif service == SERVICE_TIME_ADJUST:
            render_positive_time_period(data1, CONF_ACTUAL)
            render_positive_time_period(data1, CONF_INCREASE)
            render_positive_time_period(data1, CONF_DECREASE)
            render_positive_time_period(data1, CONF_MINIMUM)
            render_positive_time_period(data1, CONF_MAXIMUM)
            render_positive_float(self._hass, data1, CONF_PERCENTAGE)
            if zone is not None:
                if changed := zone.service_adjust_time(data1, stime):
                    controller.clear_zone_runs(zone)
            else:
                changed = controller.service_adjust_time(data1, stime)
        elif service == SERVICE_MANUAL_RUN:
            render_positive_time_period(data1, CONF_TIME)
            if zone is not None:
                zone.service_manual_run(data1, stime)
            else:
                controller.service_manual_run(data1, stime)
        elif service == SERVICE_LOAD_SCHEDULE:
            render_positive_time_period(data1, CONF_DURATION)
            self.service_load_schedule(data1)
        else:
            return

        if changed:
            self._last_tick = stime
            self._logger.log_service_call(service, stime, controller, zone, data1)
            async_call_later(self._hass, 0, self._async_replay_last_timer)
        else:
            self._logger.log_service_call(
                service, stime, controller, zone, data1, DEBUG
            )

    def service_history(self, entity_ids: set[str]) -> None:
        """History service call entry point. The history has changed
        and the sensors require an update"""
        for controller in self._controllers:
            if controller.entity_id in entity_ids:
                controller.request_update(False)
            for zone in controller.zones:
                if zone.entity_id in entity_ids:
                    zone.request_update()
        self.update_sensor(self.service_time())

    def start_test(self, test_no: int) -> datetime:
        """Main entry to start a test"""
        self._last_tick = None
        next_time = dt.utcnow()
        if self._tester.start_test(test_no, next_time) is not None:
            self.timer(next_time)
            return next_time
        return None

    def status_changed(
        self, stime: datetime, controller: IUController, zone: IUZone, state: bool
    ) -> None:
        """Collection point for entities that have changed state"""
        if stime is None:
            stime = self.service_time()
        crumbs: str = ""
        if zone is not None:
            zone_id = zone.index + 1
            if state is True:
                crumbs = zone.runs.current_run.crumbs
        else:
            zone_id = 0
        event = IUEvent().load2(stime, controller.index + 1, zone_id, state, crumbs)
        self._tester.entity_state_changed(event)
        self.request_update(False)
