"""Irrigation Unlimited Coordinator and sub classes"""
# pylint: disable=too-many-lines
import typing
from datetime import datetime, time, timedelta
from types import MappingProxyType
from typing import OrderedDict, List
from logging import WARNING, Logger, getLogger, INFO, DEBUG, ERROR
import uuid
import time as tm
import json
from homeassistant.core import HomeAssistant, CALLBACK_TYPE, DOMAIN as HADOMAIN
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval, Event as HAEvent
import homeassistant.helpers.sun as sun
import homeassistant.util.dt as dt

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
    CONF_ID,
    EVENT_HOMEASSISTANT_STOP,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    WEEKDAYS,
    ATTR_ENTITY_ID,
)

from .history import IUHistory

from .const import (
    ATTR_ADJUSTED_DURATION,
    ATTR_ADJUSTMENT,
    ATTR_BASE_DURATION,
    ATTR_CURRENT_DURATION,
    ATTR_DEFAULT_DELAY,
    ATTR_DEFAULT_DURATION,
    ATTR_DURATION_FACTOR,
    ATTR_FINAL_DURATION,
    ATTR_STATUS,
    ATTR_TOTAL_DELAY,
    ATTR_TOTAL_DURATION,
    BINARY_SENSOR,
    CONF_ACTUAL,
    CONF_ALL_ZONES_CONFIG,
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
    CONF_SEQUENCE_ZONES,
    CONF_SEQUENCES,
    CONF_SEQUENCE_ID,
    CONF_SHOW_LOG,
    CONF_AUTOPLAY,
    CONF_ANCHOR,
    COORDINATOR,
    DEFAULT_GRANULATITY,
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
    DOMAIN,
    ICON_BLOCKED,
    ICON_CONTROLLER_OFF,
    ICON_CONTROLLER_ON,
    ICON_CONTROLLER_PAUSED,
    ICON_DISABLED,
    ICON_SEQUENCE_ZONE_OFF,
    ICON_SEQUENCE_ZONE_ON,
    ICON_ZONE_OFF,
    ICON_ZONE_ON,
    ICON_SEQUENCE_OFF,
    ICON_SEQUENCE_ON,
    RES_MANUAL,
    RES_NONE,
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
    CONF_ZONE_ID,
    CONF_FUTURE_SPAN,
    SERVICE_CANCEL,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_TOGGLE,
    SERVICE_MANUAL_RUN,
    SERVICE_TIME_ADJUST,
    STATUS_BLOCKED,
    STATUS_PAUSED,
    STATUS_DISABLED,
    STATUS_INITIALISING,
    TIMELINE_STATUS,
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


# These routines truncate dates, times and deltas to the internal
# granularity. This should be no more than 1 minute and realisticly
# no less than 1 second i.e. 1 >= GRANULARITY <= 60
# The current boundaries are whole minutes (60 seconds).
SYSTEM_GRANULARITY: int = DEFAULT_GRANULATITY  # Granularity in seconds


def reset_granularity() -> None:
    """Restore the original granularity"""
    global SYSTEM_GRANULARITY  # pylint: disable=global-statement
    SYSTEM_GRANULARITY = DEFAULT_GRANULATITY


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


def wash_dt(date: datetime, granularity: int = None) -> datetime:
    """Truncate the supplied datetime to internal boundaries"""
    if date is not None:
        if granularity is None:
            granularity = SYSTEM_GRANULARITY
        rounded_seconds = int(date.second / granularity) * granularity
        return date.replace(second=rounded_seconds, microsecond=0)
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


class IUJSONEncoder(json.JSONEncoder):
    """JSON serialiser to handle ISO datetime output"""

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, timedelta):
            if o != timedelta(0):
                return str(round(o.total_seconds()))
            return ""
        return o.__str__()


class IUBase:
    """Irrigation Unlimited base class"""

    def __init__(self, index: int) -> None:
        # Private variables
        self._uid: int = uuid.uuid4().int
        self._index: int = index

    def __eq__(self, other) -> bool:
        return isinstance(other, IUBase) and self.uid == other.uid

    @property
    def uid(self) -> str:
        """Return our unique id"""
        return self._uid

    @property
    def index(self) -> int:
        """Return position within siblings"""
        return self._index


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

    def clear(self) -> None:
        """Reset the adjustment"""
        self._method = None
        self._time_adjustment = None
        self._minimum = None
        self._maximum = None

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


class IUSchedule(IUBase):
    """Irrigation Unlimited Schedule class. Schedules are not actual
    points in time but describe a future event i.e. next Monday at
    sunrise"""

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        hass: HomeAssistant,
        schedule_index: int,
    ) -> None:
        super().__init__(schedule_index)
        # Passed parameters
        self._hass = hass
        # Config parameters
        self._time = None
        self._duration: timedelta = None
        self._name: str = None
        self._weekdays: list[int] = None
        self._months: list[int] = None
        self._days = None
        self._anchor: str = None
        # Private variables
        self._dirty: bool = True

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

    def clear(self) -> None:
        """Reset this schedule"""
        self._dirty = True

    def load(self, config: OrderedDict) -> "IUSchedule":
        """Load schedule data from config"""
        self.clear()

        self._time = config[CONF_TIME]
        self._anchor = config[CONF_ANCHOR]
        self._duration = wash_td(config.get(CONF_DURATION, None))
        self._name = config.get(CONF_NAME, f"Schedule {self.index + 1}")

        if CONF_WEEKDAY in config:
            self._weekdays = []
            for i in config[CONF_WEEKDAY]:
                self._weekdays.append(WEEKDAYS.index(i))
        else:
            self._weekdays = None

        if CONF_MONTH in config:
            self._months = []
            for i in config[CONF_MONTH]:
                self._months.append(MONTHS.index(i) + 1)
        else:
            self._months = None

        self._days = config.get(CONF_DAY, None)

        return self

    def as_dict(self) -> OrderedDict:
        """Return the schedule as a dict"""
        result = OrderedDict()

        result[CONF_TIME] = self._time
        result[CONF_DURATION] = self._duration
        result[CONF_NAME] = self._name
        if self._weekdays is not None:
            result[CONF_WEEKDAY] = []
            for item in self._weekdays:
                result[CONF_WEEKDAY].append(WEEKDAYS[item])
        if self._months is not None:
            result[CONF_MONTH] = []
            for item in self._months:
                result[CONF_MONTH].append(MONTHS[item - 1])
        if self._days is not None:
            result[CONF_DAY] = self._days
        return result

    def get_next_run(
        self, stime: datetime, ftime: datetime, adjusted_duration: timedelta
    ) -> datetime:
        # pylint: disable=too-many-branches
        """
        Determine the next start time. Date processing in this routine
        is done in local time and returned as UTC. stime is the current time
        and ftime is the farthest time we are interested in. adjusted_duration
        is the total time this schedule will run for, used to work backwards when
        the anchor is finish
        """
        local_time = dt.as_local(stime)
        final_time = dt.as_local(ftime)

        next_run: datetime = None
        while True:

            if next_run is None:  # Initialise on first pass
                next_run = local_time
            else:
                next_run += timedelta(days=1)  # Advance to next day

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
                elif next_run.day not in self._days:
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
            else:  # Some weird error happened
                return None

            if self._anchor == CONF_FINISH:
                next_run -= adjusted_duration

            next_run = wash_dt(next_run)
            if next_run >= local_time:
                break

        return dt.as_utc(next_run)


class IURun(IUBase):
    """Irrigation Unlimited Run class. A run is an actual point
    in time. If schedule is None then it is a manual run.
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

    def __init__(
        self,
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

    @property
    def start_time(self) -> datetime:
        """Return the start time"""
        return self._start_time

    @property
    def duration(self) -> timedelta:
        """Return the duration"""
        return self._duration

    @property
    def zone(self) -> "IUSchedule":
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
            return RES_NONE
        if self.sequence_has_adjustment(True):
            return self.sequence_adjustment()
        return self._zone.adjustment.to_str()

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

        return "{}.{}.{}.{}.{}".format(
            get_index(self._zone),
            get_index(self._schedule),
            get_index(self.sequence),
            get_index(self.sequence_zone),
            sidx,
        )

    def sequence_has_adjustment(self, deep: bool) -> bool:
        """Return True if this run is a sequence and has an adjustment"""
        if self.is_sequence:
            return self.sequence.has_adjustment(deep)
        return False

    def sequence_adjustment(self) -> str:
        """Return the adjustment for the sequence"""
        if self.is_sequence:
            result = self._sequence_run.sequence.adjustment.to_str()
            sequence_zone = self._sequence_run.sequence_zone(self)
            if sequence_zone.has_adjustment:
                result = f"{result},{sequence_zone.adjustment.to_str()}"
            return result
        return None

    def is_manual(self) -> bool:
        """Check if this is a manual run"""
        return self._schedule is None

    def is_running(self, stime: datetime) -> bool:
        """Check if this schedule is running"""
        return self._start_time <= stime < self._end_time

    def is_expired(self, stime: datetime) -> bool:
        """Check if this schedule is expired"""
        return stime >= self._end_time

    def sequence_update(self, stime: datetime) -> bool:
        """Update the status of the sequence"""
        if self._zone_run is not None or not self.is_sequence:
            return False
        return self._sequence_run.update(stime, self)

    def update_time_remaining(self, stime: datetime) -> bool:
        """Update the count down timers"""
        if self.is_running(stime):
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


# class IURunQueue(list[IURun]): # python 3.9
class IURunQueue(typing.List[IURun]):
    """Irrigation Unlimited class to hold the upcomming runs"""

    # pylint: disable=too-many-public-methods

    DAYS_SPAN: int = 3

    RQ_STATUS_CLEARED: int = 0x01
    RQ_STATUS_EXTENDED: int = 0x02
    RQ_STATUS_REDUCED: int = 0x04
    RQ_STATUS_SORTED: int = 0x08
    RQ_STATUS_UPDATED: int = 0x10
    RQ_STATUS_CANCELED: int = 0x20
    RQ_STATUS_CHANGED: int = 0x40

    def __init__(self) -> None:
        super().__init__()
        # Private variables
        self._current_run: IURun = None
        self._next_run: IURun = None
        self._sorted: bool = False
        self._cancel_request: bool = False
        self._future_span = wash_td(timedelta(days=self.DAYS_SPAN))

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

    def is_sequence_running(self, sequence: "IUSequence") -> bool:
        """Check if the sequence is currently running"""
        for run in self:
            if run.sequence_running and run.sequence == sequence:
                return True
        return False

    def sequence_duration(self, sequence: "IUSequence") -> timedelta:
        """If sequence is running then return the duration"""
        for run in self:
            if run.sequence_running and run.sequence == sequence:
                return run.sequence_run.total_time
        return timedelta(0)

    def find_active_sequence_zone(self, sequence_zone: "IUSequenceZone") -> IURun:
        """Find the running sequence zone"""
        for run in self:
            if run.sequence_running and run.sequence_run.active_zone == sequence_zone:
                return run
        return None

    def is_sequence_zone_running(self, sequence_zone: "IUSequenceZone") -> bool:
        """Check if the sequence zone is running"""
        return self.find_active_sequence_zone(sequence_zone) is not None

    def sequence_zone_duration(self, sequence_zone: "IUSequenceZone") -> timedelta:
        """Return the duration of the running sequence zone"""
        run = self.find_active_sequence_zone(sequence_zone)
        if run is not None:
            return run.duration
        return timedelta(0)

    def add(
        self,
        start_time: datetime,
        duration: timedelta,
        zone: "IUZone",
        schedule: "IUSchedule",
        sequence_run: "IUSequenceRun",
        zone_run: IURun,
    ) -> IURun:
        # pylint: disable=too-many-arguments
        """Add a run to the queue"""
        run = IURun(start_time, duration, zone, schedule, sequence_run, zone_run)
        self.append(run)
        self._sorted = False
        return run

    def cancel(self) -> None:
        """Flag the current run to be cancelled"""
        self._cancel_request = True

    def clear_all(self) -> bool:
        """Clear out all runs"""
        modified: bool = False
        if len(self) > 0:
            self._current_run = None
            super().clear()
            modified = True
        return modified

    def clear(self, stime: datetime) -> bool:
        """Clear out the queue except for manual or running schedules"""
        modified: bool = False
        if len(self) > 0:
            i = len(self) - 1
            while i >= 0:
                item = self[i]
                if not (
                    item.is_running(stime) or item.is_manual() or item.sequence_running
                ):
                    self.pop(i)
                    modified = True
                i -= 1
            if modified:
                self._next_run = None
                self._sorted = True
        return modified

    def find_last_index(self, uid: int) -> int:
        """Return the index of the run that finishes last in the queue.
        This routine does not require the list to be sorted."""
        result: int = None
        last_time: datetime = None
        for i, run in enumerate(self):
            if run.schedule is not None and run.schedule.uid == uid:
                if last_time is None or run.end_time > last_time:
                    last_time = run.end_time
                    result = i
        return result

    def find_last_run(self, uid: int) -> IURun:
        """Find the last run for the matching uid"""
        i = self.find_last_index(uid)
        if i is not None:
            return self[i]
        return None

    def find_last_date(self, uid: int) -> datetime:
        """Find the last time in the queue for the supplied uid"""
        run = self.find_last_run(uid)
        if run is not None:
            return run.end_time
        return None

    def find_manual(self) -> IURun:
        """Find any manual run"""
        for run in self:
            if run.is_manual():
                return run
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
                return datetime.min.replace(
                    tzinfo=dt.UTC
                )  # Always put manual run at head
            return run.start_time

        modified: bool = False
        if not self._sorted:
            super().sort(key=sorter)
            self._current_run = None
            self._next_run = None
            self._sorted = True
            modified = True
        return modified

    def remove_expired(self, stime: datetime) -> bool:
        """Remove any expired runs from the queue"""
        modified: bool = False

        i = len(self) - 1
        while i >= 0:
            run: IURun = self[i]
            if run.is_expired(stime):
                self._current_run = None
                self._next_run = None
                self.pop(i)
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
                self.pop(0)
            self._current_run = None
            self._next_run = None
            modified = True
        return modified

    def update_queue(self, stime: datetime) -> int:
        """Update the run queue. Sort the queue, remove expired runs
        and set current and next runs. This is the final operation after
        all additions and deletions.

        Returns a bit field of changes to queue.
        """
        status: int = 0

        if self.sort():
            status |= self.RQ_STATUS_SORTED

        for run in self:
            if run.sequence_update(stime):
                status |= self.RQ_STATUS_CHANGED

        if self._cancel_request:
            if self.remove_current():
                status |= self.RQ_STATUS_CANCELED
            self._cancel_request = False

        if self.remove_expired(stime):
            status |= self.RQ_STATUS_REDUCED

        # Try to find a running schedule
        if self._current_run is None and len(self) > 0 and self[0].is_running(stime):
            self._current_run = self[0]
            self._next_run = None
            status |= self.RQ_STATUS_UPDATED

        # Try to find the next schedule
        if self._next_run is None:
            if self._current_run is None:
                if len(self) >= 1:
                    self._next_run = self[0]
                    status |= self.RQ_STATUS_UPDATED
            else:
                if len(self) >= 2:
                    self._next_run = self[1]
                    status |= self.RQ_STATUS_UPDATED

        return status

    def update_sensor(self, stime: datetime) -> bool:
        """Update the count down timers"""
        if self._current_run is None:
            return False
        return self._current_run.update_time_remaining(stime)

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

    def add(
        self,
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
            start_time, self.constrain(duration), zone, schedule, sequence_run, None
        )

    def add_manual(
        self, start_time: datetime, duration: timedelta, zone: "IUZone"
    ) -> IURun:
        """Add a manual run to the queue. Cancel any existing
        manual or running schedule"""

        if self._current_run is not None:
            self.pop(0)

        # Remove any existing manual schedules
        while True:
            run = self.find_manual()
            if run is None:
                break
            self.remove(run)

        self._current_run = None
        self._next_run = None
        duration = max(duration, granularity_time())
        return self.add(start_time, duration, zone, None, None)

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
        next_time = self.find_last_date(schedule.uid)
        if next_time is not None:
            next_time += granularity_time()
        else:
            next_time = stime

        duration = self.constrain(adjustment.adjust(schedule.duration))
        next_run = schedule.get_next_run(next_time, self.last_time(stime), duration)

        if next_run is not None:
            self.add(next_run, duration, zone, schedule, None)
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
        self._is_enabled: bool = True
        self._name: str = None
        self._switch_entity_id: str = None
        self._show_config: bool = False
        self._show_timeline: bool = False
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
        self._dirty: bool = True

    @property
    def unique_id(self) -> str:
        """Return the HA unique_id for the zone"""
        return f"c{self._controller.index + 1}_z{self.index + 1}"

    @property
    def entity_id(self) -> str:
        """Return the HA entity_id for the zone"""
        return f"{BINARY_SENSOR}.{DOMAIN}_{self.unique_id}"

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
    def enabled(self) -> bool:
        """Return true if this zone is enabled"""
        return self._is_enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable/disable zone"""
        if value != self._is_enabled:
            self._is_enabled = value
            self._dirty = True
            self.request_update()

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
        if self._controller.enabled:
            if self.enabled:
                if self.is_on:
                    return ICON_ZONE_ON
                return ICON_ZONE_OFF
            return ICON_DISABLED
        return ICON_BLOCKED

    @property
    def configuration(self) -> str:
        """Return this zone as JSON"""
        return json.dumps(self.as_dict(), cls=IUJSONEncoder)

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
            if self._controller.enabled:
                if self._is_enabled:
                    if self._is_on:
                        return STATE_ON
                    return STATE_OFF
                return STATUS_DISABLED
            return STATUS_BLOCKED
        return STATUS_INITIALISING

    def service_enable(
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

    def service_adjust_time(self, data: MappingProxyType, stime: datetime) -> bool:
        """Adjust the scheduled run times. Return true if adjustment changed"""
        sequence_id = data.get(CONF_SEQUENCE_ID)
        if sequence_id is not None:
            self._coordinator.logger.log_sequence_entity(stime)
        result = self._adjustment.load(data)
        if result:
            self._run_queue.clear(stime)
        return result

    def service_manual_run(self, data: MappingProxyType, stime: datetime) -> None:
        """Add a manual run."""
        if self._is_enabled and self._controller.enabled:
            nst = wash_dt(stime + granularity_time())
            if self._controller.preamble is not None:
                nst += self._controller.preamble
            self._run_queue.add_manual(nst, wash_td(data[CONF_TIME]), self)

    def service_cancel(self, data: MappingProxyType, stime: datetime) -> None:
        """Cancel the current running schedule"""
        # pylint: disable=unused-argument
        self._run_queue.cancel()

    def add(self, schedule: IUSchedule) -> IUSchedule:
        """Add a new schedule to the zone"""
        self._schedules.append(schedule)
        return schedule

    def find_add(self, index: int) -> IUSchedule:
        """Look for and add if necessary a new schedule"""
        if index >= len(self._schedules):
            return self.add(IUSchedule(self._hass, index))
        return self._schedules[index]

    def clear(self) -> None:
        """Reset this zone"""
        self._schedules.clear()
        self.clear_run_queue()
        self._adjustment = IUAdjustment()
        self._is_on = False

    def clear_runs(self, stime: datetime) -> None:
        """Clear out the run queue except for current or manual runs"""
        self._run_queue.clear(stime)

    def clear_run_queue(self) -> None:
        """Clear out the run queue completely"""
        self._run_queue.clear_all()

    def load(self, config: OrderedDict, all_zones: OrderedDict) -> "IUZone":
        """Load zone data from the configuration"""
        self.clear()
        self._zone_id = config.get(CONF_ID, str(self.index + 1))
        self._is_enabled = config.get(CONF_ENABLED, True)
        self._name = config.get(CONF_NAME, None)
        self._switch_entity_id = config.get(CONF_ENTITY_ID)
        self._run_queue.load(config, all_zones)
        if all_zones is not None and CONF_SHOW in all_zones:
            self._show_config = all_zones[CONF_SHOW].get(CONF_CONFIG, self._show_config)
            self._show_timeline = all_zones[CONF_SHOW].get(
                CONF_TIMELINE, self._show_timeline
            )
        if CONF_SHOW in config:
            self._show_config = config[CONF_SHOW].get(CONF_CONFIG, self._show_config)
            self._show_timeline = config[CONF_SHOW].get(
                CONF_TIMELINE, self._show_timeline
            )
        if CONF_SCHEDULES in config:
            for sidx, schedule_config in enumerate(config[CONF_SCHEDULES]):
                self.find_add(sidx).load(schedule_config)
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
        result[CONF_ICON] = self.icon
        result[CONF_ZONE_ID] = self._zone_id
        result[ATTR_STATUS] = self.status
        result[ATTR_ADJUSTMENT] = str(self._adjustment)
        result[ATTR_CURRENT_DURATION] = current_duration
        result[CONF_SCHEDULES] = []
        for schedule in self._schedules:
            result[CONF_SCHEDULES].append(schedule.as_dict())
        return result

    def timeline(self) -> list:
        """Return the on/off timeline. Merge history and future and add
        the status"""
        run_list = self._coordinator.history.timeline(self.entity_id)
        for run in run_list:
            run[TIMELINE_STATUS] = RES_TIMELINE_HISTORY

        stime = self._coordinator.service_time()
        for run in self._run_queue:
            dct = run.as_dict()
            if run.is_running(stime):
                dct[TIMELINE_STATUS] = RES_TIMELINE_RUNNING
            elif run == self._run_queue.next_run:
                dct[TIMELINE_STATUS] = RES_TIMELINE_NEXT
            else:
                dct[TIMELINE_STATUS] = RES_TIMELINE_SCHEDULED
            run_list.append(dct)
        run_list.reverse()
        return run_list

    def muster(self, stime: datetime) -> int:
        """Muster this zone"""
        # pylint: disable=unused-argument
        status: int = 0

        if self._dirty:
            self._run_queue.clear_all()
            status |= IURunQueue.RQ_STATUS_CLEARED

        self._dirty = False
        return status

    def muster_schedules(self, stime: datetime) -> int:
        """Calculate run times for this zone"""
        status: int = 0

        for schedule in self._schedules:
            if self._run_queue.merge_fill(stime, self, schedule, self._adjustment):
                status |= IURunQueue.RQ_STATUS_EXTENDED

        if status != 0:
            self.request_update()

        return status

    def check_run(self, stime: datetime, parent_enabled: bool) -> bool:
        """Update the run status"""
        is_running: bool = False
        state_changed: bool = False

        is_running = (
            parent_enabled
            and self._is_enabled
            and self._run_queue.current_run is not None
            and self._run_queue.current_run.is_running(stime)
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

    def call_switch(self, state: bool, stime: datetime = None) -> None:
        """Turn the HA entity on or off"""
        if self._switch_entity_id is not None:
            self._hass.async_create_task(
                self._hass.services.async_call(
                    HADOMAIN,
                    SERVICE_TURN_ON if state else SERVICE_TURN_OFF,
                    {ATTR_ENTITY_ID: self._switch_entity_id},
                )
            )
        self._coordinator.status_changed(stime, self._controller, self, state)


class IUZoneQueue(IURunQueue):
    """Class to hold the upcoming zones to run"""

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
        zone_run: IURun,
        preamble: timedelta,
        postamble: timedelta,
    ) -> IURun:
        """Add a new master run to the queue"""
        start_time = zone_run.start_time
        duration = zone_run.duration
        if preamble is not None:
            start_time -= preamble
            duration += preamble
        if postamble is not None:
            duration += postamble
        run = self.find_run(start_time, zone_run)
        if run is None:
            run = self.add(
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
        zones: "list[IUZone]",
        preamble: timedelta,
        postamble: timedelta,
        clear_all: bool,
    ) -> int:
        """Create a superset of all the zones."""
        # pylint: disable=too-many-arguments
        status: int = 0
        if clear_all:
            self.clear_all()
        else:
            self.clear(stime)
        for zone in zones:
            for run in zone.runs:
                self.add_zone(run, preamble, postamble)
        status |= IURunQueue.RQ_STATUS_EXTENDED | IURunQueue.RQ_STATUS_REDUCED
        status |= self.update_queue(stime)
        return status


class IUSequenceZone(IUBase):
    """Irrigation Unlimited Sequence Zone class"""

    # pylint: disable=too-many-instance-attributes

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
        self._delay: timedelta = None
        self._duration: timedelta = None
        self._repeat: int = None
        self._enabled: bool = True
        # Private variables
        self.clear()

    @property
    def zone_ids(self) -> "list[str]":
        """Returns a list of zone_id's"""
        return self._zone_ids

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
    def enabled(self) -> bool:
        """Return if this sequence zone is enabled"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set the enabled state"""
        self._enabled = value

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
        return self._controller.runs.is_sequence_zone_running(self)

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self._controller.enabled:
            if self._sequence.enabled:
                if self._sequence.zone_enabled(self):
                    if self.is_on:
                        return ICON_SEQUENCE_ZONE_ON
                    return ICON_SEQUENCE_ZONE_OFF
                return ICON_DISABLED
        return ICON_BLOCKED

    @property
    def status(self) -> str:
        """Return status of the sequence zone"""
        if self._controller.enabled:
            if self._sequence.enabled:
                if self._sequence.zone_enabled(self):
                    if self.is_on:
                        return STATE_ON
                    return STATE_OFF
                return STATUS_DISABLED
        return STATUS_BLOCKED

    def clear(self) -> None:
        """Reset this sequence zone"""
        self._adjustment = IUAdjustment()

    def load(self, config: OrderedDict) -> "IUSequenceZone":
        """Load sequence zone data from the configuration"""
        self.clear()
        self._zone_ids = config[CONF_ZONE_ID]
        self._delay = wash_td(config.get(CONF_DELAY))
        self._duration = wash_td(config.get(CONF_DURATION))
        self._repeat = config.get(CONF_REPEAT, 1)
        self._enabled = config.get(CONF_ENABLED, self._enabled)
        return self

    def zone_indexes(self) -> int:
        """Generator to list zone indexes"""
        for zone_id in self.zone_ids:
            zone = self._controller.find_zone_by_zone_id(zone_id)
            if zone is not None:
                yield zone.index

    def as_dict(self, duration_factor: float) -> dict:
        """Return this sequence zone as a dict"""
        result = OrderedDict()
        result[CONF_INDEX] = self._index
        result[CONF_STATE] = STATE_ON if self.is_on else STATE_OFF
        result[CONF_ENABLED] = self._enabled
        result[CONF_ICON] = self.icon
        result[ATTR_STATUS] = self.status
        result[CONF_DELAY] = self._sequence.zone_delay(self)
        result[ATTR_BASE_DURATION] = self._sequence.zone_duration_base(self)
        result[ATTR_ADJUSTED_DURATION] = self._sequence.zone_duration(self)
        result[ATTR_FINAL_DURATION] = self._sequence.zone_duration_final(
            self, duration_factor
        )
        result[CONF_ZONES] = ",".join(str(idx + 1) for idx in self.zone_indexes())
        result[ATTR_CURRENT_DURATION] = self._controller.runs.sequence_zone_duration(
            self
        )
        result[ATTR_ADJUSTMENT] = str(self._adjustment)
        return result


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
        self._schedules: list[IUSchedule] = []
        self._zones: list[IUSequenceZone] = []
        self._adjustment = IUAdjustment()

    @property
    def schedules(self) -> "list[IUSchedule]":
        """Return the list of schedules for this sequence"""
        return self._schedules

    @property
    def zones(self) -> "list[IUSequenceZone]":
        """Return the list of sequence zones"""
        return self._zones

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
    def enabled(self) -> bool:
        """Return if this sequence is enabled"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set the enabled state"""
        self._enabled = value

    @property
    def adjustment(self) -> IUAdjustment:
        """Returns the sequence adjustment"""
        return self._adjustment

    @property
    def is_on(self) -> bool:
        """Return if the sequence is on or off"""
        return self._controller.runs.is_sequence_running(self)

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self._controller.enabled:
            if self.enabled:
                if self.is_on:
                    return ICON_SEQUENCE_ON
                return ICON_SEQUENCE_OFF
            return ICON_DISABLED
        return ICON_BLOCKED

    @property
    def status(self) -> str:
        """Return status of the sequence"""
        if self._controller.enabled:
            if self._enabled:
                if self.is_on:
                    return STATE_ON
                return STATE_OFF
            return STATUS_DISABLED
        return STATUS_BLOCKED

    def has_adjustment(self, deep: bool) -> bool:
        """Indicates if this sequence has an active adjustment"""
        if self._adjustment.has_adjustment:
            return True
        if deep:
            for sequence_zone in self._zones:
                if sequence_zone.enabled and sequence_zone.adjustment.has_adjustment:
                    return True
        return False

    def zone_enabled(self, sequence_zone: IUSequenceZone) -> bool:
        """Return True if at least one real zone referenced by the
        sequence_zone is enabled"""
        if self._controller.enabled and self.enabled and sequence_zone.enabled:
            for zone_id in sequence_zone.zone_ids:
                zone = self._controller.find_zone_by_zone_id(zone_id)
                if zone is not None and zone.enabled:
                    return True
        return False

    def constrain(
        self, sequence_zone: IUSequenceZone, duration: timedelta
    ) -> timedelta:
        """Apply the zone entity constraints"""
        for zone_id in sequence_zone.zone_ids:
            zone = self._controller.find_zone_by_zone_id(zone_id)
            if zone is not None:
                duration = zone.runs.constrain(duration)
        return duration

    def zone_delay(self, sequence_zone: IUSequenceZone) -> timedelta:
        """Return the delay for the specified zone"""
        if self.zone_enabled(sequence_zone):
            if sequence_zone.delay is not None:
                delay = sequence_zone.delay
            else:
                delay = self._delay
            if delay is None:
                delay = timedelta(0)
            return delay
        return timedelta(0)

    def total_delay(self) -> timedelta:
        """Return the total delay for all the zones"""
        delay = timedelta(0)
        last_zone: IUSequenceZone = None
        if len(self._zones) > 0:
            for zone in self._zones:
                delay += self.zone_delay(zone) * zone.repeat
                last_zone = zone
            delay *= self._repeat
            if last_zone is not None:
                delay -= self.zone_delay(last_zone)
        return delay

    def zone_duration_base(self, sequence_zone: IUSequenceZone) -> timedelta:
        """Return the base duration for the specified zone"""
        if self.zone_enabled(sequence_zone):
            if sequence_zone.duration is not None:
                duration = sequence_zone.duration
            else:
                duration = self._duration
            if duration is None:
                duration = granularity_time()
            return duration
        return timedelta(0)

    def zone_duration(self, sequence_zone: IUSequenceZone) -> timedelta:
        """Return the duration for the specified zone including adjustments
        and constraints"""
        if self.zone_enabled(sequence_zone):
            duration = self.zone_duration_base(sequence_zone)
            duration = sequence_zone.adjustment.adjust(duration)
            return self.constrain(sequence_zone, duration)
        return timedelta(0)

    def zone_duration_final(
        self, sequence_zone: IUSequenceZone, duration_factor: float
    ) -> timedelta:
        """Return the final zone time after the factor has been applied"""
        duration = self.zone_duration(sequence_zone) * duration_factor
        duration = self.constrain(sequence_zone, duration)
        return round_td(duration)

    def total_duration(self) -> timedelta:
        """Return the total duration for all the zones"""
        duration = timedelta(0)
        for zone in self._zones:
            duration += self.zone_duration(zone) * zone.repeat
        duration *= self._repeat
        return duration

    def total_duration_adjusted(self, total_duration) -> timedelta:
        """Return the adjusted duration"""
        if total_duration is None:
            total_duration = self.total_duration()
        if self.has_adjustment(False):
            total_duration = self.adjustment.adjust(total_duration)
            total_duration = max(total_duration, timedelta(0))
        return total_duration

    def total_time_final(self, total_time: timedelta) -> timedelta:
        """Return the adjusted total time for the sequence"""
        if total_time is not None and self.has_adjustment(False):
            total_delay = self.total_delay()
            total_duration = self.total_duration_adjusted(total_time - total_delay)
            return total_duration + total_delay

        if total_time is None:
            return self.total_duration_adjusted(None) + self.total_delay()

        return total_time

    def duration_factor(self, total_time: timedelta) -> float:
        """Given a new total run time, calculate how much to shrink or expand each
        zone duration. Final time will be approximate as the new durations must
        be rounded to internal boundaries"""
        total_duration = self.total_duration()
        if total_time is not None and total_duration != timedelta(0):
            return (total_time - self.total_delay()) / total_duration
        return 1.0

    def clear(self) -> None:
        """Reset this sequence"""
        self._schedules.clear()
        self._zones.clear()
        self._adjustment.clear()

    def add_schedule(self, schedule: IUSchedule) -> IUSchedule:
        """Add a new schedule to the sequence"""
        self._schedules.append(schedule)
        return schedule

    def find_add_schedule(self, index: int) -> IUSchedule:
        """Look for and create if required a schedule"""
        if index >= len(self._schedules):
            return self.add_schedule(IUSchedule(self._hass, index))
        return self._schedules[index]

    def find_zone(self, index: int) -> IUSequenceZone:
        """Return the specified zone object"""
        if index >= 0 and index < len(self._zones):
            return self._zones[index]
        return None

    def add_zone(self, zone: IUSequenceZone) -> IUSequenceZone:
        """Add a new zone to the sequence"""
        self._zones.append(zone)
        return zone

    def find_add_zone(self, index: int) -> IUSequenceZone:
        """Look for and create if required a zone"""
        result = self.find_zone(index)
        if result is None:
            result = self.add_zone(IUSequenceZone(self._controller, self, index))
        return result

    def zone_ids(self) -> str:
        """Generator to return the zone_id's"""
        result = set()
        for sequence_zone in self._zones:
            for zone_id in sequence_zone.zone_ids:
                result.add(zone_id)
        for zone_id in result:
            yield zone_id

    def load(self, config: OrderedDict) -> "IUSequence":
        """Load sequence data from the configuration"""
        self.clear()
        self._name = config.get(CONF_NAME, f"Run {self.index + 1}")
        self._delay = wash_td(config.get(CONF_DELAY))
        self._duration = wash_td(config.get(CONF_DURATION))
        self._repeat = config.get(CONF_REPEAT, 1)
        self._enabled = config.get(CONF_ENABLED, self._enabled)
        for zidx, zone_config in enumerate(config[CONF_ZONES]):
            self.find_add_zone(zidx).load(zone_config)
        for sidx, schedule_config in enumerate(config[CONF_SCHEDULES]):
            self.find_add_schedule(sidx).load(schedule_config)
        return self

    def as_dict(self) -> OrderedDict:
        """Return this sequence as a dict"""
        total_delay = self.total_delay()
        total_duration = self.total_duration()
        total_duration_adjusted = self.total_duration_adjusted(total_duration)
        duration_factor = self.duration_factor(total_duration_adjusted + total_delay)
        result = OrderedDict()
        result[CONF_INDEX] = self._index
        result[CONF_NAME] = self._name
        result[CONF_STATE] = STATE_ON if self.is_on else STATE_OFF
        result[CONF_ENABLED] = self._enabled
        result[ATTR_ICON] = self.icon
        result[ATTR_STATUS] = self.status
        result[ATTR_DEFAULT_DURATION] = self._duration
        result[ATTR_DEFAULT_DELAY] = self._delay
        result[ATTR_DURATION_FACTOR] = duration_factor
        result[ATTR_TOTAL_DELAY] = total_delay
        result[ATTR_TOTAL_DURATION] = total_duration
        result[ATTR_ADJUSTED_DURATION] = total_duration_adjusted
        result[ATTR_CURRENT_DURATION] = self._controller.runs.sequence_duration(self)
        result[ATTR_ADJUSTMENT] = str(self._adjustment)
        result[CONF_SEQUENCE_ZONES] = []
        for sequence_zone in self._zones:
            result[CONF_SEQUENCE_ZONES].append(sequence_zone.as_dict(duration_factor))
        return result


class IUSequenceRun(IUBase):
    """Irrigation Unlimited sequence run manager class. Ties together the
    individual sequence zones"""

    def __init__(self, sequence: IUSequence, total_time: timedelta) -> None:
        super().__init__(None)
        # Passed parameters
        self._sequence = sequence
        self._total_time = total_time
        # Private variables
        self._runs: OrderedDict = {}
        self._active_zone: IUSequenceZone = None
        self._running = False

    @property
    def sequence(self) -> IUSequence:
        """Return the sequence associated with this run"""
        return self._sequence

    @property
    def total_time(self) -> timedelta:
        """Return the total run time for this sequence"""
        return self._total_time

    @property
    def running(self) -> bool:
        """Indicate if this sequence is running"""
        return self._running

    @property
    def active_zone(self) -> bool:
        """Return the active zone in the sequence"""
        return self._active_zone

    def add(self, run: IURun, sequence_zone: IUSequenceZone) -> None:
        """Adds a sequence zone to the group"""
        self._runs[run.uid] = sequence_zone

    def run_index(self, run: IURun) -> int:
        """Extract the index from the supplied run"""
        return list(self._runs.keys()).index(run.uid)

    def sequence_zone(self, run: IURun) -> IUSequenceZone:
        """Extract the sequence zone from the run"""
        return self._runs.get(run.uid, None)

    def update(self, stime: datetime, run: IURun) -> bool:
        """Update the status of the sequence"""
        is_running = run.is_running(stime)
        sequence_zone = self.sequence_zone(run)
        if is_running and not self._running:
            self._running = True
            self._active_zone = sequence_zone
            return True

        if is_running and sequence_zone != self._active_zone:
            self._active_zone = sequence_zone
            return True

        if not is_running and sequence_zone == self._active_zone:
            self._active_zone = None
            return True

        return False


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
        self._is_enabled: bool = True
        self._name: str = None
        self._switch_entity_id: str = None
        self._preamble: timedelta = None
        self._postamble: timedelta = None
        # Private variables
        self._initialised: bool = False
        self._finalised: bool = False
        self._zones: list[IUZone] = []
        self._sequences: list[IUSequence] = []
        self._run_queue = IUZoneQueue()
        self._master_sensor: Entity = None
        self._is_on: bool = False
        self._sensor_update_required: bool = False
        self._sensor_last_update: datetime = None
        self._dirty: bool = True

    @property
    def unique_id(self) -> str:
        """Return the HA unique_id for the controller entity"""
        return f"c{self.index + 1}_m"

    @property
    def entity_id(self) -> str:
        """Return the HA entity_id for the controller entity"""
        return f"{BINARY_SENSOR}.{DOMAIN}_{self.unique_id}"

    @property
    def zones(self) -> "list[IUZone]":
        """Return a list of childen zones"""
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
    def enabled(self) -> bool:
        """Return true is this controller is enabled"""
        return self._is_enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable/disable this controller"""
        if value != self._is_enabled:
            self._is_enabled = value
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
            if self.is_on:
                return ICON_CONTROLLER_ON
            if self.is_paused:
                return ICON_CONTROLLER_PAUSED
            return ICON_CONTROLLER_OFF
        return ICON_DISABLED

    @property
    def configuration(self) -> str:
        """Return this controller as JSON"""
        return json.dumps(self.as_dict(), cls=IUJSONEncoder)

    def _status(self) -> str:
        """Return status of the controller"""
        if self._initialised:
            if self._is_enabled:
                if self._is_on:
                    return STATE_ON
                if self._run_queue.in_sequence:
                    return STATUS_PAUSED
                return STATE_OFF
            return STATUS_DISABLED
        return STATUS_INITIALISING

    def _is_setup(self) -> bool:
        self._initialised = self._master_sensor is not None

        if self._initialised:
            for zone in self._zones:
                self._initialised = self._initialised and zone.is_setup
        return self._initialised

    def add_zone(self, zone: IUZone) -> IUZone:
        """Add a new zone to the controller"""
        self._zones.append(zone)
        return zone

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

    def find_sequence(self, index: int) -> IUSequence:
        """Locate the sequence"""
        if index >= 0 and index < len(self._sequences):
            return self._sequences[index]
        return None

    def find_add_sequence(
        self, coordinator: "IUCoordinator", controller: "IUController", index: int
    ) -> IUSequence:
        """Locate and create if required a sequence"""
        if index >= len(self._sequences):
            return self.add_sequence(
                IUSequence(self._hass, coordinator, controller, index)
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
        self._sequences.clear()
        self._is_on = False

    def clear_sequence_runs(
        self, stime: datetime, zone_ids: "list[str]" = None
    ) -> None:
        """Clear out zone run queue from supplied list or the lot if None"""
        if zone_ids is None:
            for zone in self._zones:
                zone.clear_runs(stime)
        else:
            for zone_id in zone_ids:
                zone = self.find_zone_by_zone_id(zone_id)
                if zone is not None:
                    zone.clear_runs(stime)

    def load(self, config: OrderedDict) -> "IUController":
        """Load config data for the controller"""
        self.clear()
        self._is_enabled = config.get(CONF_ENABLED, True)
        self._name = config.get(CONF_NAME, f"Controller {self.index + 1}")
        self._switch_entity_id = config.get(CONF_ENTITY_ID)
        self._preamble = wash_td(config.get(CONF_PREAMBLE))
        self._postamble = wash_td(config.get(CONF_POSTAMBLE))
        all_zones = config.get(CONF_ALL_ZONES_CONFIG)
        zidx: int = 0
        for zidx, zone_config in enumerate(config[CONF_ZONES]):
            self.find_add_zone(self._coordinator, self, zidx).load(
                zone_config, all_zones
            )
        while zidx < len(self._zones) - 1:
            self._zones.pop().finalise(True)

        if CONF_SEQUENCES in config:
            for qidx, sequence_config in enumerate(config[CONF_SEQUENCES]):
                self.find_add_sequence(self._coordinator, self, qidx).load(
                    sequence_config
                )

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
        result[CONF_STATE] = STATE_ON if self.is_on else STATE_OFF
        result[CONF_ENABLED] = self._is_enabled
        result[CONF_ICON] = self.icon
        result[ATTR_STATUS] = self.status
        result[CONF_ZONES] = []
        for zone in self._zones:
            result[CONF_ZONES].append(zone.as_dict())
        result[CONF_SEQUENCES] = []
        for sequence in self._sequences:
            result[CONF_SEQUENCES].append(sequence.as_dict())
        return result

    def muster_sequence(
        self,
        stime: datetime,
        sequence: IUSequence,
        schedule: IUSchedule,
        total_time: timedelta = None,
    ) -> int:
        # pylint: disable=too-many-locals
        """Muster the sequences for the controller"""

        def init_run_time(
            stime: datetime,
            schedule: IUSchedule,
            zone: IUZone,
            total_duration: timedelta,
        ) -> datetime:
            if schedule is not None:
                next_time = zone.runs.find_last_date(schedule.uid)
                if next_time is not None:
                    next_time += granularity_time()
                else:
                    next_time = stime
                next_run = schedule.get_next_run(
                    next_time, zone.runs.last_time(stime), total_duration
                )
            else:
                next_run = stime + granularity_time()
            return next_run

        def calc_total_time(
            total_time: timedelta, sequence: IUSequence, schedule: IUSchedule
        ) -> timedelta:
            """Calculate the total duration of the sequence"""

            if total_time is None:
                if schedule is not None and schedule.duration is not None:
                    return sequence.total_time_final(schedule.duration)
                return sequence.total_time_final(None)

            if schedule is not None:
                return sequence.total_time_final(total_time)
            return total_time

        total_time = calc_total_time(total_time, sequence, schedule)
        duration_factor = sequence.duration_factor(total_time)
        status: int = 0
        next_run: datetime = None
        sequence_run: IUSequenceRun = None
        # pylint: disable=too-many-nested-blocks
        for i in range(sequence.repeat):  # pylint: disable=unused-variable
            for sequence_zone in sequence.zones:
                if not sequence_zone.enabled:
                    continue
                duration = sequence.zone_duration_final(sequence_zone, duration_factor)
                duration_max = timedelta(0)
                delay = sequence.zone_delay(sequence_zone)
                for zone in (
                    self.find_zone_by_zone_id(zone_id)
                    for zone_id in sequence_zone.zone_ids
                ):
                    if zone is not None and zone.enabled:
                        # Initialise on first pass
                        if next_run is None:
                            next_run = init_run_time(stime, schedule, zone, total_time)
                            if next_run is None:
                                return status  # Exit if queue is full
                            sequence_run = IUSequenceRun(sequence, total_time)

                        # Don't adjust manual run and no adjustment on adjustment
                        # This code should not really be here. It would be a breaking
                        # change if removed.
                        if schedule is not None and not sequence.has_adjustment(True):
                            duration_adjusted = zone.adjustment.adjust(duration)
                            duration_adjusted = zone.runs.constrain(duration_adjusted)
                        else:
                            duration_adjusted = duration

                        zone_run_time = next_run
                        for j in range(  # pylint: disable=unused-variable
                            sequence_zone.repeat
                        ):
                            run = zone.runs.add(
                                zone_run_time,
                                duration_adjusted,
                                zone,
                                schedule,
                                sequence_run,
                            )
                            sequence_run.add(run, sequence_zone)
                            zone_run_time += run.duration + delay
                        zone.request_update()
                        duration_max = max(duration_max, zone_run_time - next_run)
                        status |= IURunQueue.RQ_STATUS_EXTENDED
                if next_run is not None:
                    next_run += duration_max
        return status

    def muster(self, stime: datetime, force: bool) -> int:
        """Calculate run times for this controller. This is where most of the hard yakka
        is done."""
        # pylint: disable=too-many-branches
        status: int = 0

        if self._dirty or force:
            self._run_queue.clear_all()
            for zone in self._zones:
                zone.clear_run_queue()
            status |= IURunQueue.RQ_STATUS_CLEARED

        zone_status: int = 0

        # Handle initialisation
        for zone in self._zones:
            zone_status |= zone.muster(stime)

        # Process sequence schedules
        for sequence in self._sequences:
            if sequence.enabled:
                for schedule in sequence.schedules:
                    while True:
                        sequence_status = self.muster_sequence(
                            stime, sequence, schedule, None
                        )
                        zone_status |= sequence_status
                        if sequence_status & IURunQueue.RQ_STATUS_EXTENDED == 0:
                            break

        # Process zone schedules
        for zone in self._zones:
            if zone.enabled:
                zone_status |= zone.muster_schedules(stime)

        # Post processing
        for zone in self._zones:
            zone_status |= zone.runs.update_queue(stime)

        if (
            zone_status
            & (
                IURunQueue.RQ_STATUS_CLEARED
                | IURunQueue.RQ_STATUS_EXTENDED
                | IURunQueue.RQ_STATUS_SORTED
                | IURunQueue.RQ_STATUS_CANCELED
                | IURunQueue.RQ_STATUS_CHANGED
            )
            != 0
        ):
            clear_all = bool(
                zone_status
                & (IURunQueue.RQ_STATUS_CLEARED | IURunQueue.RQ_STATUS_CANCELED)
            )
            status |= self._run_queue.rebuild_schedule(
                stime, self._zones, self._preamble, self._postamble, clear_all
            )
        else:
            status |= self._run_queue.update_queue(stime)

        if status != 0:
            self.request_update(False)

        self._dirty = False
        return status | zone_status

    def check_run(self, stime: datetime) -> bool:
        """Check the run status and update sensors. Return flag
        if anything has changed."""
        zones_changed: list[int] = []
        is_running: bool = False
        state_changed: bool = False

        # Gather zones that have changed status
        for zone in self._zones:
            if zone.check_run(stime, self._is_enabled):
                zones_changed.append(zone.index)

        # Handle off zones before master
        for zone in (self._zones[i] for i in zones_changed):
            if not zone.is_on:
                zone.call_switch(zone.is_on, stime)

        # Check if master has changed and update
        is_running = self._is_enabled and self._run_queue.current_run is not None
        state_changed = is_running ^ self._is_on
        if state_changed:
            self._is_on = not self._is_on
            self.request_update(False)
            self.call_switch(self._is_on, stime)

        # Handle on zones after master
        for zone in (self._zones[i] for i in zones_changed):
            if zone.is_on:
                zone.call_switch(zone.is_on, stime)

        return state_changed

    def request_update(self, deep: bool) -> None:
        """Flag the sensor needs an update. The actual update is done
        in update_sensor"""
        self._sensor_update_required = True
        if deep:
            for zone in self._zones:
                zone.request_update()

    def update_sensor(self, stime: datetime) -> None:
        """Lazy sensor updater."""
        self._run_queue.update_sensor(stime)

        for zone in self._zones:
            zone.update_sensor(stime, False)

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

    def call_switch(self, state: bool, stime: datetime = None) -> None:
        """Update the linked entity if enabled"""
        if self._switch_entity_id is not None:
            self._hass.async_create_task(
                self._hass.services.async_call(
                    HADOMAIN,
                    SERVICE_TURN_ON if state else SERVICE_TURN_OFF,
                    {ATTR_ENTITY_ID: self._switch_entity_id},
                )
            )
        self._coordinator.status_changed(stime, self, None, state)

    def check_item(self, index: int, items: "list[int]") -> bool:
        """If items is None or contains only a 0 (match all) then
        return True. Otherwise check if index + 1 is in the list"""
        # pylint: disable=no-self-use
        return (
            items is None or (items is not None and items == [0]) or index + 1 in items
        )

    def service_enable(
        self, data: MappingProxyType, stime: datetime, service: str
    ) -> bool:
        """Handler for enable/disable/toggle service call"""
        # pylint: disable=too-many-nested-blocks

        def s2b(test: bool, service: str) -> bool:
            """Convert the service code to bool"""
            if service == SERVICE_ENABLE:
                return True
            if service == SERVICE_DISABLE:
                return False
            return not test  # Must be SERVICE_TOGGLE

        result = False
        zone_list: list[int] = data.get(CONF_ZONES)
        sequence_id = data.get(CONF_SEQUENCE_ID)
        if sequence_id is None:
            new_state = s2b(self.enabled, service)
            if self.enabled != new_state:
                self.enabled = new_state
                result = True
        else:
            sequence = self.find_sequence(sequence_id - 1)
            if sequence is not None:
                if zone_list is None:
                    new_state = s2b(sequence.enabled, service)
                    if sequence.enabled != new_state:
                        sequence.enabled = new_state
                        result = True
                else:
                    for sequence_zone in sequence.zones:
                        if self.check_item(sequence_zone.index, zone_list):
                            new_state = s2b(sequence_zone.enabled, service)
                            if sequence_zone.enabled != new_state:
                                sequence_zone.enabled = new_state
                                result = True
                if result:
                    self.clear_sequence_runs(stime, sequence.zone_ids())
                    self._run_queue.clear(stime)
            else:
                self._coordinator.logger.log_invalid_sequence(stime, self, sequence_id)
        return result

    def service_adjust_time(self, data: MappingProxyType, stime: datetime) -> bool:
        """Handler for the adjust_time service call"""
        result = False
        zone_list: list[int] = data.get(CONF_ZONES)
        sequence_id = data.get(CONF_SEQUENCE_ID)
        if sequence_id is None:
            for zone in self._zones:
                if self.check_item(zone.index, zone_list):
                    result |= zone.service_adjust_time(data, stime)
        else:
            sequence = self.find_sequence(sequence_id - 1)
            if sequence is not None:
                if zone_list is None:
                    result = sequence.adjustment.load(data)
                else:
                    for sequence_zone in sequence.zones:
                        if self.check_item(sequence_zone.index, zone_list):
                            result |= sequence_zone.adjustment.load(data)
                if result:
                    self.clear_sequence_runs(stime, sequence.zone_ids())
            else:
                self._coordinator.logger.log_invalid_sequence(stime, self, sequence_id)
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
            sequence = self.find_sequence(sequence_id - 1)
            if sequence is not None:
                self.muster_sequence(stime, sequence, None, wash_td(data[CONF_TIME]))
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
        return "{{t: '{}', c: {}, z: {}, s: {}}}".format(
            dt2lstr(self._time), self._controller, self._zone, str(int(self._state))
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

    def as_dict(self) -> dict:
        """Return this object as a dict"""
        return {
            "t": self._time,
            "c": self._controller,
            "z": self._zone,
            "s": self._state,
        }


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
        """Return the number of events recieved"""
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
    def current_result(self) -> int:
        """Return the index of the next result to check"""
        return self._current_result

    @property
    def total_results(self) -> int:
        """Return the number of expected results from the test"""
        return len(self._results)

    def is_finished(self, stime) -> bool:
        """Indicate if this test has finished"""
        return self.virtual_time(stime) > self._end

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
        return self._start + timedelta(seconds=virtual_duration)


class IUTester:
    """Irrigation Unlimited testing class"""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, coordinator: "IUCoordinator") -> None:
        # Passed parameters
        self._coordinator = coordinator
        # Private variables
        self._tests: list[IUTest] = []
        self._test_initialised = False
        self._running_test: int = None
        self._last_test: int = None
        self._autoplay_initialised: bool = False
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

    def start_test(self, test_no: int, atime: datetime) -> IUTest:
        """Start the test"""
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
                if self._autoplay:
                    test = self.next_test(atime)
                    if test is not None:
                        poll_func(test.start, True)
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
                    # poll_func(atime, True)
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

    def _controller_index(self, controller: IUController) -> str:
        """Return the controller sibling index or 0 if none"""
        # pylint: disable=no-self-use
        if controller is not None:
            return str(controller.index + 1)
        return 0

    def _zone_index(self, zone: IUZone) -> str:
        """Return the zone sibling index or 0 if none"""
        # pylint: disable=no-self-use
        if zone is not None:
            return str(zone.index + 1)
        return "0"

    def _output(self, level: int, msg: str) -> None:
        """Send out the message"""
        self._logger.log(level, msg)

    def log_start(self) -> None:
        """Message for system clock starting"""
        self._output(DEBUG, "START")

    def log_stop(self) -> None:
        """Message for system clock stopping"""
        self._output(DEBUG, "STOP")

    def log_load(self, data: OrderedDict) -> None:
        """Message that the config is loaded"""
        # pylint: disable=unused-argument
        self._output(DEBUG, "LOAD")

    def log_initialised(self) -> None:
        """Message that the system is initialised and ready to go"""
        self._output(DEBUG, "INITIALISED")

    def log_event(self, event: IUEvent, level=DEBUG) -> None:
        """Message that an event has occured - controller or zone turning on or off"""
        if len(event.crumbs) != 0:
            result = "EVENT [{0}] controller: {1:d}, zone: {2:d}, state: {3}, data: {4}".format(
                dt2lstr(event.time),
                event.controller,
                event.zone,
                str(int(event.state)),
                event.crumbs,
            )
        else:
            result = "EVENT [{0}] controller: {1:d}, zone: {2:d}, state: {3}".format(
                dt2lstr(event.time),
                event.controller,
                event.zone,
                str(int(event.state)),
            )
        self._output(level, result)

    def log_service_call(
        self,
        service: str,
        stime: datetime,
        controller: IUController,
        zone: IUZone,
        data: MappingProxyType,
    ) -> None:
        """Message that we have received a service call"""
        # pylint: disable=too-many-arguments
        self._output(
            DEBUG,
            "CALL [{0}] service: {1}, controller: {2}, zone: {3}, data: {4}".format(
                dt2lstr(stime),
                service,
                self._controller_index(controller),
                self._zone_index(zone),
                json.dumps(data, default=str),
            ),
        )

    def log_register_entity(
        self, stime: datetime, controller: IUController, zone: IUZone, entity: Entity
    ) -> None:
        """Message that HA has registered an entity"""
        self._output(
            DEBUG,
            "REGISTER [{0}] controller: {1}, zone: {2}, entity: {3}".format(
                dt2lstr(stime),
                self._controller_index(controller),
                self._zone_index(zone),
                entity.entity_id,
            ),
        )

    def log_deregister_entity(
        self, stime: datetime, controller: IUController, zone: IUZone, entity: Entity
    ) -> None:
        """Message that HA is removing an entity"""
        self._output(
            DEBUG,
            "DEREGISTER [{0}] controller: {1}, zone: {2}, entity: {3}".format(
                dt2lstr(stime),
                self._controller_index(controller),
                self._zone_index(zone),
                entity.entity_id,
            ),
        )

    def log_test_start(self, vtime: datetime, test: IUTest, level=DEBUG) -> None:
        """Message that a test is starting"""
        self._output(
            level,
            "TEST_START [{0}] test: {1:d}, start: {2}, end: {3}".format(
                dt2lstr(vtime), test.index + 1, dt2lstr(test.start), dt2lstr(test.end)
            ),
        )

    def log_test_end(self, vtime: datetime, test: IUTest, level=DEBUG) -> None:
        """Message that a test has finished"""
        self._output(
            level, "TEST_END [{0}] test: {1:d}".format(dt2lstr(vtime), test.index + 1)
        )

    def log_test_error(
        self, test: IUTest, actual: IUEvent, expected: IUEvent, level=DEBUG
    ) -> None:
        """Message that an event did not meet expected result"""
        self._output(
            level,
            "TEST_ERROR test: {0:d}, actual: {1}, expected: {2}".format(
                test.index + 1, str(actual), str(expected)
            ),
        )

    def log_test_completed(self, checks: int, errors: int, level=DEBUG) -> None:
        """Message that all tests have been completed"""
        self._output(
            level,
            "TEST_COMPLETED (Idle): checks: {0:d}, errors: {1:d}".format(
                checks, errors
            ),
        )

    def log_sequence_entity(self, vtime: datetime, level=WARNING) -> None:
        """Warn that a service call involved a sequence but was not directed
        at the controller"""
        self._output(
            level,
            "ENTITY [{0}] Sequence specified but entity_id is zone".format(
                dt2lstr(vtime)
            ),
        )

    def log_invalid_sequence(
        self, vtime: datetime, controller: IUController, sequence_id: int, level=WARNING
    ) -> None:
        """Warn that a service call with a sequence_id is invalid"""
        self._output(
            level,
            "SEQUENCE_ID [{0}] Invalid sequence id: controller: {1}, sequence: {2}".format(
                dt2lstr(vtime),
                self._controller_index(controller),
                sequence_id,
            ),
        )

    def log_bad_config(self, msg: str, data: str, level=WARNING) -> None:
        """Warn invalid configuration data"""
        self._output(
            level, "CONFIG Invalid configuration: msg: {0}, data: {1}".format(msg, data)
        )


class IUCoordinator:
    """Irrigation Unimited Coordinator class"""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

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
        self._remove_timer_listener: CALLBACK_TYPE = None
        self._remove_shutdown_listener: CALLBACK_TYPE = None
        self._tester = IUTester(self)
        self._logger = IULogger(_LOGGER)
        self._history = IUHistory(self._hass)
        self._restored_from_configutation: bool = False

    @property
    def entity_id(self) -> str:
        """Return the entity_id for the coordinator"""
        return f"{DOMAIN}.{COORDINATOR}"

    @property
    def controllers(self) -> "list[IUController]":
        """Return the list of controllers"""
        return self._controllers

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
    def configuration(self) -> str:
        """Return the system configuration as JSON"""
        return json.dumps(self.as_dict(), cls=IUJSONEncoder)

    @property
    def restored_from_configuration(self) -> bool:
        """Return if the system has been restored from coordinator date"""
        return self._restored_from_configutation

    @restored_from_configuration.setter
    def restored_from_configuration(self, value: bool) -> None:
        """Flas the system has been restored from coordinator data"""
        self._restored_from_configutation = value

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
        SYSTEM_GRANULARITY = config.get(CONF_GRANULARITY, DEFAULT_GRANULATITY)
        self._refresh_interval = timedelta(
            seconds=config.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL)
        )

        cidx: int = 0
        for cidx, controller_config in enumerate(config[CONF_CONTROLLERS]):
            self.find_add(self, cidx).load(controller_config)
        while cidx < len(self._controllers) - 1:
            self._controllers.pop().finalise(True)

        self._tester = IUTester(self).load(config.get(CONF_TESTING))
        self._logger = IULogger(_LOGGER).load(config.get(CONF_LOGGING))

        self._dirty = True
        self._muster_required = True
        self._logger.log_load(config)
        self._history.load(config)
        return self

    def as_dict(self) -> OrderedDict:
        """Returns the coordinator as a dict"""
        result = OrderedDict()
        result[CONF_CONTROLLERS] = []
        for controller in self._controllers:
            result[CONF_CONTROLLERS].append(controller.as_dict())
        return result

    def muster(self, stime: datetime, force: bool) -> int:
        """Calculate run times for system"""
        status: int = 0

        entity_ids: List[str] = []
        for controller in self._controllers:
            for zone in controller.zones:
                entity_ids.append(zone.entity_id)
        self._history.muster(stime, entity_ids, force)

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

    def request_update(self, deep: bool) -> None:
        """Flag the sensor needs an update. The actual update is done
        in update_sensor"""
        self._sensor_update_required = True
        if deep:
            for controller in self._controllers:
                controller.request_update(True)

    def update_sensor(self, stime: datetime) -> None:
        """Update home assistant sensors if required"""
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
        if (wtime != self._last_muster) or self._muster_required:
            if self.muster(wtime, force) != 0:
                self.check_run(wtime)
            self._muster_required = False
            self._last_muster = wtime
        self.update_sensor(wash_dt(vtime, 1))

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
                self.request_update(True)
                self.poll_main(atime)

    async def _async_timer(self, atime: datetime) -> None:
        """Timer callback"""
        self.timer(atime)

    def track_interval(self) -> timedelta:
        """Returns the system clock time interval"""
        track_time = SYSTEM_GRANULARITY / self._tester.speed
        track_time *= 0.95  # Run clock slightly ahead of required to avoid skipping
        return min(timedelta(seconds=track_time), self._refresh_interval)

    def start(self) -> None:
        """Start the system clock"""
        self.stop()
        self._remove_timer_listener = async_track_time_interval(
            self._hass, self._async_timer, self.track_interval()
        )
        self._logger.log_start()

    def stop(self) -> None:
        """Stop the system clock"""
        if self._remove_timer_listener is not None:
            self._remove_timer_listener()
            self._remove_timer_listener = None
            self._logger.log_stop()

    def finalise(self, turn_off: bool) -> None:
        """Tear down the system and cleanup"""
        for controller in self._controllers:
            controller.finalise(turn_off)

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

    def register_entity(
        self, controller: IUController, zone: IUZone, entity: Entity
    ) -> None:
        """A HA entity has been registered"""
        stime = self.service_time()
        if controller is None:
            self._component = entity
        elif zone is None:
            controller.master_sensor = entity
        else:
            zone.zone_sensor = entity
        self._logger.log_register_entity(stime, controller, zone, entity)

    def deregister_entity(
        self, controller: IUController, zone: IUZone, entity: Entity
    ) -> None:
        """A HA entity has been removed"""
        stime = self.service_time()
        if controller is None:
            self.finalise(True)
            self._component = None
        elif zone is None:
            controller.finalise(True)
            controller.master_sensor = None
        else:
            zone.finalise(True)
            zone.zone_sensor = None
        self._logger.log_deregister_entity(stime, controller, zone, entity)

    def service_time(self) -> datetime:
        """Return a time midway between last and next future tick"""
        if self._last_tick is not None:
            result = self._last_tick + self.track_interval() / 2
        else:
            result = dt.utcnow()
        if self._tester.is_testing:
            result = self._tester.current_test.virtual_time(result)
        return wash_dt(result)

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

        if service in [SERVICE_ENABLE, SERVICE_DISABLE, SERVICE_TOGGLE]:
            if zone is not None:
                if changed := zone.service_enable(data, stime, service):
                    controller.clear_sequence_runs(stime)
            else:
                changed = controller.service_enable(data, stime, service)
        elif service == SERVICE_CANCEL:
            if zone is not None:
                zone.service_cancel(data, stime)
            else:
                controller.service_cancel(data, stime)
        elif service == SERVICE_TIME_ADJUST:
            if zone is not None:
                changed = zone.service_adjust_time(data, stime)
            else:
                changed = controller.service_adjust_time(data, stime)
        elif service == SERVICE_MANUAL_RUN:
            if zone is not None:
                zone.service_manual_run(data, stime)
            else:
                controller.service_manual_run(data, stime)
        if changed:
            self.request_update(False)
            self._muster_required = True
            self._logger.log_service_call(service, stime, controller, zone, data)

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
