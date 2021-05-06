"""Irrigation Unlimited Coordinator and sub classes"""

from datetime import datetime, time, timedelta
from types import MappingProxyType
from typing import OrderedDict
import homeassistant
from homeassistant.core import HomeAssistant, CALLBACK_TYPE
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
import homeassistant.helpers.sun as sun
import homeassistant.util.dt as dt
import logging
import uuid

from homeassistant.const import (
    CONF_AFTER,
    CONF_BEFORE,
    CONF_DELAY,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_REPEAT,
    CONF_WEEKDAY,
    CONF_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    WEEKDAYS,
    ATTR_ENTITY_ID,
)

from .const import (
    CONF_ACTUAL,
    CONF_ALL_ZONES_CONFIG,
    CONF_DAY,
    CONF_DECREASE,
    CONF_INCREASE,
    CONF_PERCENTAGE,
    CONF_REFRESH_INTERVAL,
    CONF_RESET,
    CONF_SEQUENCES,
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
    MONTHS,
    CONF_ODD,
    CONF_EVEN,
    CONF_SHOW,
    CONF_CONFIG,
    CONF_TIMELINE,
    CONF_ZONE_ID,
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
)

_LOGGER: logging.Logger = logging.getLogger(__package__)

# Useful time manipulation routine
def time_to_timedelta(offset: time) -> timedelta:
    """Create a timedelta from a time object"""
    return datetime.combine(datetime.min, offset) - datetime.min


# These routines truncate dates, times and deltas to the internal
# granularity. This should be no more than 1 minute and realisticly
# no less than 1 second i.e. 1 >= GRANULARITY <= 60
# The current boundaries are whole minutes (60 seconds).
SYSTEM_GRANULARITY: int = DEFAULT_GRANULATITY  # Granularity in seconds


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
    else:
        return None


def wash_dt(date: datetime, granularity: int = None) -> datetime:
    """Truncate the supplied datetime to internal boundaries"""
    if date is not None:
        if granularity is None:
            granularity = SYSTEM_GRANULARITY
        rounded_seconds = int(date.second / granularity) * granularity
        d = date.replace(second=rounded_seconds, microsecond=0)
        return d
    else:
        return None


def wash_t(time: time, granularity: int = None) -> time:
    """Truncate the supplied time to internal boundaries"""
    if time is not None:
        if granularity is None:
            granularity = SYSTEM_GRANULARITY
        utc = dt.utcnow()
        d = utc.combine(utc.date(), time)
        rounded_seconds = int(d.second / granularity) * granularity
        t = d.replace(second=rounded_seconds, microsecond=0)
        return t.time()
    else:
        return None


class IUBase:
    """Irrigation Unlimited base class"""

    def __init__(self, index: int) -> None:
        # Private variables
        self._id: int = uuid.uuid4().int
        self._index: int = index
        return

    @property
    def id(self) -> str:
        """Return our unique id"""
        return self._id

    @property
    def index(self) -> int:
        return self._index


class IUAdjustment:
    """Irrigation Unlimited class to handle run time adjustment"""

    def __init__(self) -> None:
        self._method: str = None
        self._time_adjustment = None
        self._minimum: timedelta = None
        self._maximum: timedelta = None
        return

    @property
    def as_string(self) -> str:
        """Return a string representation of the adjustment"""
        return self.to_string()

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

    def adjust(self, time: timedelta) -> timedelta:
        """Return the adjusted time"""
        new_time: timedelta

        if self._method is None:
            new_time = time
        elif self._method == CONF_ACTUAL:
            new_time = self._time_adjustment
        elif self._method == CONF_PERCENTAGE:
            new_time = wash_td(time * self._time_adjustment / 100)
        elif self._method == CONF_INCREASE:
            new_time = time + self._time_adjustment
        elif self._method == CONF_DECREASE:
            new_time = time - self._time_adjustment
        else:
            new_time = time

        if self._minimum is not None:
            new_time = max(new_time, self._minimum)

        if self._maximum is not None:
            new_time = min(new_time, self._maximum)

        return new_time

    def to_string(self) -> str:
        """Return the adjustment as a string notation"""
        if self._method is None:
            s = "None"
        elif self._method == CONF_ACTUAL:
            s = f"={self._time_adjustment}"
        elif self._method == CONF_PERCENTAGE:
            s = f"%{self._time_adjustment}"
        elif self._method == CONF_INCREASE:
            s = f"+{self._time_adjustment}"
        elif self._method == CONF_DECREASE:
            s = f"-{self._time_adjustment}"
        else:
            s = str(self._time_adjustment)
        return s


class IUSchedule(IUBase):
    """Irrigation Unlimited Schedule class. Schedules are not actual
    points in time but describe a future event i.e. next Monday"""

    def __init__(
        self,
        hass: HomeAssistant,
        schedule_index: int,
        object: IUBase,
    ) -> None:
        super().__init__(schedule_index)
        # Passed parameters
        self._hass = hass
        self._object: IUBase = object
        # Config parameters
        self._time = None
        self._duration: timedelta = None
        self._name: str = None
        self._weekdays: list[int] = None
        self._months: list[int] = None
        # Private variables
        self._dirty: bool = True
        return

    @property
    def name(self) -> str:
        """Return the friendly name of this schedule"""
        return self._name

    @property
    def is_setup(self) -> bool:
        """Return true is this schedule is setup"""
        return True

    @property
    def run_time(self) -> timedelta:
        """Return the duration"""
        return self._duration

    def clear(self) -> None:
        """Reset this schedule"""
        self._dirty = True
        return

    def load(self, config: OrderedDict):
        """Load schedule data from config"""
        self.clear()

        self._time = config[CONF_TIME]
        self._duration = wash_td(config.get(CONF_DURATION), None)
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
        dict = OrderedDict()

        dict[CONF_TIME] = self._time
        dict[CONF_DURATION] = self._duration
        dict[CONF_NAME] = self._name
        if self._weekdays is not None:
            dict[CONF_WEEKDAY] = []
            for item in self._weekdays:
                dict[CONF_WEEKDAY].append(WEEKDAYS[item])
        if self._months is not None:
            dict[CONF_MONTH] = []
            for item in self._months:
                dict[CONF_MONTH].append(MONTHS[item - 1])
        if self._days is not None:
            dict[CONF_DAY] = self._days
        return dict

    def get_next_run(self, atime: datetime) -> datetime:
        """
        Determine the next start time. Date processing in this routine
        is done in local time and returned as UTC
        """
        local_time = dt.as_local(atime)

        next_run: datetime = None
        while True:

            if next_run is None:
                next_run = local_time  # Initialise on first pass
            else:
                next_run += timedelta(days=1)  # Advance to next day

            # Sanity check. Note: Astral events like sunrise might take months i.e. Antarctica winter
            if next_run > local_time + timedelta(days=365):
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

            if isinstance(self._time, time):
                next_run = datetime.combine(
                    next_run.date(), self._time, next_run.tzinfo
                )
            elif isinstance(self._time, dict) and CONF_SUN in self._time:
                se = sun.get_astral_event_date(
                    self._hass, self._time[CONF_SUN], next_run
                )
                if se is None:
                    continue  # Astral event did not occur today

                next_run = dt.as_local(se)
                if CONF_AFTER in self._time:
                    next_run += self._time[CONF_AFTER]
                if CONF_BEFORE in self._time:
                    next_run -= self._time[CONF_BEFORE]
            else:  # Some weird error happened
                return None

            next_run = wash_dt(next_run)
            if next_run >= local_time:
                break

        return dt.as_utc(next_run)


class IURun:
    """Irrigation Unlimited Run class. A run is an actual point
    in time. If schedule is None then it is a manual run.
    """

    def __init__(
        self,
        start_time: datetime,
        duration: timedelta,
        zone: IUBase,
        schedule: IUBase,
        sid: int,
        sidx: int,
        sequence,
        sequence_zone,
    ) -> None:
        # Passed parameters
        self._start_time: datetime = start_time
        self._duration: timedelta = duration
        self._zone = zone
        self._schedule = schedule
        self._sid: int = sid
        self._sidx: int = sidx
        self._sequence = sequence
        self._sequence_zone = sequence_zone
        # Private variables
        self._end_time: datetime = self._start_time + self._duration
        self._remaining_time: timedelta = self._end_time - self._start_time
        self._percent_complete: int = 0
        return

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @property
    def duration(self) -> timedelta:
        return self._duration

    @property
    def zone(self) -> IUBase:
        return self._zone

    @property
    def schedule(self) -> IUBase:
        """Return the schedule"""
        return self._schedule

    @property
    def end_time(self) -> datetime:
        return self._end_time

    @property
    def time_remaining(self) -> timedelta:
        return self._remaining_time

    @property
    def percent_complete(self) -> float:
        return self._percent_complete

    @property
    def sid(self) -> int:
        return self._sid

    @property
    def sidx(self) -> int:
        return self._sidx

    @property
    def sequence(self):
        return self._sequence

    @property
    def sequence_zone(self):
        return self._sequence_zone

    def is_manual(self) -> bool:
        """Check if this is a manual run"""
        return self._schedule is None

    def is_running(self, time: datetime) -> bool:
        """Check if this schedule is running"""
        return (time >= self._start_time) and (time < self._end_time)

    def is_expired(self, time: datetime) -> bool:
        """Check if this schedule is expired"""
        return time >= self._end_time

    def is_future(self, time: datetime) -> bool:
        """Check schedule is in the future"""
        return self._start_time > time

    def is_valid(self, time: datetime) -> bool:
        """Return true if run is valid. Should be
        running or in the future.
        """
        return self.is_running(time) and not self.is_future(time)

    def update_time_remaining(self, time: datetime) -> bool:
        if self.is_running(time):
            self._remaining_time = self._end_time - time
            total_duration: timedelta = self._end_time - self._start_time
            time_elapsed: timedelta = time - self._start_time
            self._percent_complete = int((time_elapsed / total_duration) * 100)
            return True
        else:
            return False

    def as_dict(self) -> OrderedDict:
        dict = OrderedDict()
        dict["start"] = self._start_time
        dict["end"] = self._end_time
        return dict


class IURunQueue(list):
    DAYS_SPAN: int = 3

    RQ_STATUS_CLEARED: int = 0x01
    RQ_STATUS_EXTENDED: int = 0x02
    RQ_STATUS_REDUCED: int = 0x04
    RQ_STATUS_SORTED: int = 0x08
    RQ_STATUS_UPDATED: int = 0x10
    RQ_STATUS_CANCELED: int = 0x20

    def __init__(self) -> None:
        # Private variables
        self._current_run: IURun = None
        self._next_run: IURun = None
        self._sorted: bool = False
        self._cancel_request: bool = False
        return

    @property
    def current_run(self) -> IURun:
        return self._current_run

    @property
    def next_run(self) -> IURun:
        return self._next_run

    def add(
        self,
        start_time: datetime,
        duration: timedelta,
        zone: IUBase,
        schedule: IUBase,
        sid: int,
        sidx: int,
        sequence,
        sequence_zone,
    ):
        run = IURun(
            start_time, duration, zone, schedule, sid, sidx, sequence, sequence_zone
        )
        self.append(run)
        self._sorted = False
        return self

    def cancel(self) -> None:
        """Flag the current run to be cancelled"""
        self._cancel_request = True
        return

    def clear_all(self) -> bool:
        modified: bool = False
        if len(self) > 0:
            self._current_run = None
            super().clear()
            modified = True
        return modified

    def clear(self, time: datetime) -> bool:
        """Clear out the queue except for manual or running schedules"""
        modified: bool = False
        if len(self) > 0:
            i = len(self) - 1
            while i >= 0:
                if not (self[i].is_running(time) or self[i].is_manual()):
                    self.pop(i)
                    modified = True
                i -= 1
            if modified:
                self._next_run = None
                self._sorted = True
        return modified

    def find_last_by_id(self, id: int) -> IURun:
        """Return the run that finishes last in the queue. This routine
        does not require the list to be sorted."""
        last_time: datetime = None
        last_index: int = None
        for i, run in enumerate(self):
            if run.schedule is not None and run.schedule.id == id:
                if last_time is None or run.end_time > last_time:
                    last_time = run.end_time
                    last_index = i
        if last_index is not None:
            return self[last_index]
        else:
            return None

    def find_last_date(self, id: int) -> datetime:
        """Find the last time in the queue for the supplied id"""
        last_time: datetime = None
        for run in self:
            if run.schedule is not None and run.schedule.id == id:
                if last_time is None or run.end_time > last_time:
                    last_time = run.end_time
        return last_time

    def find_manual(self) -> IURun:
        for run in self:
            if run.is_manual():
                return run
        return None

    def last_time(self, time: datetime) -> datetime:
        return time + timedelta(days=self.DAYS_SPAN)

    def sorter(self, run: IURun) -> datetime:
        """Sort call back routine. Items are sorted
        by start_time."""
        if run.is_manual():
            return datetime.min.replace(tzinfo=dt.UTC)  # Always put manual run at head
        else:
            return run.start_time

    def sort(self) -> bool:
        """Sort the run queue."""
        modified: bool = False
        if not self._sorted:
            super().sort(key=self.sorter)
            self._current_run = None
            self._next_run = None
            self._sorted = True
            modified = True
        return modified

    def remove_expired(self, time: datetime) -> bool:
        """Remove any expired runs from the queue"""
        modified: bool = False

        i = len(self) - 1
        while i >= 0:
            run: IURun = self[i]
            if run.is_expired(time):
                self._current_run = None
                self._next_run = None
                self.pop(i)
                modified = True
            i -= 1
        return modified

    def remove_current(self) -> bool:
        """Remove the current run"""
        modified: bool = False
        if self._current_run is not None:
            if len(self) > 0:
                self.pop(0)
            self._current_run = None
            modified = True
        return modified

    def update_queue(self, time: datetime) -> int:
        """Update the run queue. Sort the queue, remove expired runs
        and set current and next runs.

        Returns a bit field of changes to queue.
        """
        status: int = 0

        if self.sort():
            status |= self.RQ_STATUS_SORTED

        if self._cancel_request:
            if self.remove_current():
                status |= self.RQ_STATUS_CANCELED
            self._cancel_request = False

        if self.remove_expired(time):
            status |= self.RQ_STATUS_REDUCED

        # Try to find a running schedule
        if self._current_run is None and len(self) > 0 and self[0].is_running(time):
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

    def update_sensor(self, time) -> bool:
        if self._current_run is not None:
            return self._current_run.update_time_remaining(time)
        else:
            return False

    def as_list(self) -> list:
        l = []
        for run in self:
            l.append(run.as_dict())
        return l


class IUScheduleQueue(IURunQueue):
    """Class to hold the upcoming schedules to run"""

    def add_schedule(
        self,
        zone: IUBase,
        schedule: IUSchedule,
        start_time: datetime,
        adjustment: IUAdjustment,
    ):
        """Add a new schedule run to the queue"""
        duration = schedule.run_time
        if adjustment is not None:
            duration = adjustment.adjust(duration)
        self.add(start_time, duration, zone, schedule, None, None, None, None)
        return self

    def add_manual(self, start_time: datetime, duration: timedelta, zone: IUBase):
        """Add a manual run to the queue. Cancel any existing
        manual or running schedule"""

        if self._current_run is not None:
            self.pop(0)

        # Remove any existing manual schedules
        while True:
            run = self.find_manual()
            if run is None:
                break
            else:
                self.remove(run)

        duration = max(duration, granularity_time())
        self.add(start_time, duration, zone, None, None, None, None, None)
        self._current_run = None
        self._next_run = None
        return self

    def merge_one(
        self,
        time: datetime,
        zone,
        schedule,
        adjustment: IUAdjustment,
    ) -> bool:
        modified: bool = False

        last_date = self.last_time(time)
        # See if schedule already exists in run queue. If so get
        # the finish time of the last entry.
        next_time = self.find_last_date(schedule.id)
        if next_time is not None:
            next_time += granularity_time()
        else:
            next_time = time

        if next_time < last_date:
            next_run = schedule.get_next_run(next_time)
        else:
            next_run = None

        if next_run is not None and next_run < last_date:
            self.add_schedule(zone, schedule, next_run, adjustment)
            modified = True

        return modified

    def merge_fill(
        self,
        time: datetime,
        zone,
        schedule,
        adjustment: IUAdjustment,
    ) -> bool:
        """Merge the schedule into the run queue. Add as many until the span is
        reached. Return True if the schedule was added."""
        modified: bool = False

        while self.merge_one(time, zone, schedule, adjustment):
            modified = True

        return modified

    def update_queue(
        self,
        time: datetime,
    ) -> int:
        return super().update_queue(time)


class IUZone(IUBase):
    """Irrigation Unlimited Zone class"""

    def __init__(
        self, hass: HomeAssistant, coordinator, controller, zone_index: int
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
        self._schedules: list(IUSchedule) = []
        self._run_queue = IUScheduleQueue()
        self._adjustment = IUAdjustment()
        self._zone_sensor: Entity = None
        self._is_on: bool = False
        self._sensor_update_required: bool = False
        self._sensor_last_update: datetime = None
        self._dirty: bool = True
        return

    @property
    def schedules(self) -> list:
        return self._schedules

    @property
    def runs(self) -> IUScheduleQueue:
        return self._run_queue

    @property
    def adjustment(self) -> IUAdjustment:
        return self._adjustment

    @property
    def zone_id(self) -> str:
        return self._zone_id

    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name
        else:
            return f"Zone {self._index + 1}"

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def is_setup(self) -> bool:
        return self._is_setup()

    @property
    def enabled(self) -> bool:
        """Return true if this zone is on"""
        return self._is_enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable/disable zone"""
        if value != self._is_enabled:
            self._is_enabled = value
            self._dirty = True
            self.request_update()
        return

    @property
    def zone_sensor(self) -> Entity:
        return self._zone_sensor

    @zone_sensor.setter
    def zone_sensor(self, value: Entity):
        self._zone_sensor = value
        return

    @property
    def status(self) -> str:
        return self._status()

    @property
    def show_config(self) -> bool:
        return self._show_config

    @property
    def show_timeline(self) -> bool:
        return self._show_timeline

    def _is_setup(self) -> bool:
        """Check if this object is setup"""
        if not self._initialised:
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
                    else:
                        return STATE_OFF
                else:
                    return STATUS_DISABLED
            else:
                return STATUS_BLOCKED
        else:
            return STATUS_INITIALISING

    def service_adjust_time(self, data: MappingProxyType, time: datetime) -> bool:
        """Adjust the scheduled run times. Return true if adjustment changed"""
        result = self._adjustment.load(data)
        if result:
            self._run_queue.clear(time)
        return result

    def service_manual_run(self, data: MappingProxyType, time: datetime) -> None:
        """Add a manual run."""
        if self._is_enabled and self._controller.enabled:
            ns = wash_dt(time + granularity_time())
            if self._controller.preamble is not None:
                ns = ns + self._controller.preamble
            self._run_queue.add_manual(ns, wash_td(data[CONF_TIME]), self)
        return

    def service_cancel(self, data: MappingProxyType, time: datetime) -> None:
        """Cancel the current running schedule"""
        self._run_queue.cancel()
        return

    def add(self, schedule: IUSchedule) -> IUSchedule:
        """Add a new schedule to the zone"""
        self._schedules.append(schedule)
        return schedule

    def find_add(self, coordinator, controller, index: int) -> IUSchedule:
        if index >= len(self._schedules):
            return self.add(IUSchedule(self._hass, index, self))
        else:
            return self._schedules[index]

    def clear_run_queue(self) -> None:
        """Clear out the run queue"""
        self._run_queue.clear_all()
        return

    def clear(self) -> None:
        """Reset this zone"""
        self._schedules.clear()
        self.clear_run_queue()
        self._is_on = False
        return

    def load(self, config: OrderedDict, all_zones: OrderedDict):
        """ Load zone data from the configuration"""
        self.clear()
        self._zone_id = config.get(CONF_ID, str(self.index + 1))
        self._is_enabled = config.get(CONF_ENABLED, True)
        self._name = config.get(CONF_NAME, None)
        self._switch_entity_id = config.get(CONF_ENTITY_ID)
        self._adjustment.load(config)
        if all_zones is not None and CONF_SHOW in all_zones:
            self._show_config = all_zones[CONF_SHOW].get(CONF_CONFIG, False)
            self._show_timeline = all_zones[CONF_SHOW].get(CONF_TIMELINE, False)
        if CONF_SHOW in config:
            self._show_config = config[CONF_SHOW].get(CONF_CONFIG, False)
            self._show_timeline = config[CONF_SHOW].get(CONF_TIMELINE, False)
        if CONF_SCHEDULES in config:
            for si, schedule_config in enumerate(config[CONF_SCHEDULES]):
                self.find_add(self._coordinator, self._controller, si).load(
                    schedule_config
                )
        self._dirty = True
        return self

    def as_dict(self) -> OrderedDict:
        dict = OrderedDict()
        dict[CONF_ENABLED] = self._is_enabled
        if self._name is not None:
            dict[CONF_NAME] = self._name
        if self._switch_entity_id is not None:
            dict[CONF_ENTITY_ID] = self._switch_entity_id
        dict[CONF_SCHEDULES] = []
        for schedule in self._schedules:
            dict[CONF_SCHEDULES].append(schedule.as_dict())
        return dict

    def muster(self, time: datetime) -> int:
        status: int = 0

        if self._dirty:
            self._run_queue.clear_all()
            status |= IURunQueue.RQ_STATUS_CLEARED

        self._dirty = False
        return status

    def muster_schedules(self, time: datetime) -> int:
        """Calculate run times for this zone"""
        status: int = 0

        for schedule in self._schedules:
            if self._run_queue.merge_fill(time, self, schedule, self._adjustment):
                status |= IURunQueue.RQ_STATUS_EXTENDED

        if status != 0:
            self.request_update()

        return status

    def check_run(self, time: datetime, parent_enabled: bool) -> bool:
        """Update the run status"""
        is_running: bool = False
        state_changed: bool = False

        is_running = (
            parent_enabled
            and self._is_enabled
            and self._run_queue.current_run is not None
            and self._run_queue.current_run.is_running(time)
        )

        state_changed = is_running ^ self._is_on
        if state_changed:
            self._is_on = not self._is_on
            self.request_update()

        return state_changed

    def request_update(self) -> None:
        """Flag the sensor needs an update"""
        self._sensor_update_required = True
        return

    def update_sensor(self, time: datetime, do_on: bool) -> bool:
        """Lazy sensor updater"""
        updated: bool = False
        do_update: bool = False

        if self._zone_sensor is not None:
            if do_on == False:
                updated |= self._run_queue.update_sensor(time)
                if not self._is_on:
                    do_update = self._sensor_update_required
            else:
                if self._is_on:
                    # If we are running then update sensor according to refresh_interval
                    if self._run_queue.current_run is not None:
                        do_update = (
                            self._sensor_last_update is None
                            or time - self._sensor_last_update
                            >= self._coordinator.refresh_interval
                        )
                    do_update = do_update or self._sensor_update_required
        else:
            do_update = False

        if do_update:
            self._zone_sensor.schedule_update_ha_state()
            self._sensor_update_required = False
            self._sensor_last_update = time
            updated = True

        return updated

    def call_switch(self, service_type: str) -> None:
        if self._switch_entity_id is not None:
            self._hass.async_create_task(
                self._hass.services.async_call(
                    homeassistant.core.DOMAIN,
                    service_type,
                    {ATTR_ENTITY_ID: self._switch_entity_id},
                )
            )
        return


class IUZoneQueue(IURunQueue):
    """Class to hold the upcoming zones to run"""

    @property
    def in_sequence(self) -> bool:
        return self._in_sequence()

    def _in_sequence(self) -> bool:
        return (
            self._next_run is not None
            and self._next_run.sidx is not None
            and self._next_run.sidx != 0
        )

    def add_zone(
        self,
        start_time: datetime,
        duration: timedelta,
        zone: IUZone,
        schedule: IUSchedule,
        sid: int,
        sidx: int,
        sequence,
        sequence_zone,
        preamble: timedelta,
        postamble: timedelta,
    ):
        """Add a new master run to the queue"""
        if preamble is not None:
            start_time -= preamble
            duration += preamble
        if postamble is not None:
            duration += postamble
        self.add(
            start_time, duration, zone, schedule, sid, sidx, sequence, sequence_zone
        )
        return self

    def rebuild_schedule(
        self,
        time: datetime,
        zones,
        preamble: timedelta,
        postamble: timedelta,
        all: bool,
    ) -> int:
        """Create a superset of all the zones."""
        status: int = 0
        if all:
            self.clear_all()
        else:
            self.clear(time)
        for zone in zones:
            for run in zone._run_queue:
                self.add_zone(
                    run.start_time,
                    run.duration,
                    run.zone,
                    run.schedule,
                    run.sid,
                    run.sidx,
                    run.sequence,
                    run.sequence_zone,
                    preamble,
                    postamble,
                )
        status |= IURunQueue.RQ_STATUS_EXTENDED | IURunQueue.RQ_STATUS_REDUCED
        status |= self.update_queue(time)
        return status


class IUSequenceZone(IUBase):
    """Irrigation Unlimited Sequence Zone class"""

    def __init__(
        self, hass: HomeAssistant, coordinator, controller, sequence, zone_index: int
    ) -> None:
        super().__init__(zone_index)
        # Passed parameters
        self._hass = hass
        self._coordinator = coordinator
        self._controller = controller
        self._sequence = sequence
        # Config parameters
        self._zone_id: str = None
        self._delay: timedelta = None
        self._duration: timedelta = None
        self._repeat: int = None
        # Private variables
        return

    @property
    def zone_id(self) -> str:
        return self._zone_id

    @property
    def duration(self) -> timedelta:
        return self._duration

    @property
    def delay(self) -> timedelta:
        return self._delay

    @property
    def repeat(self) -> int:
        return self._repeat

    def clear(self) -> None:
        """Reset this sequence zone"""
        return

    def load(self, config: OrderedDict):
        """ Load sequence zone data from the configuration"""
        self.clear()
        self._zone_id = str(config[CONF_ZONE_ID])
        self._delay = wash_td(config.get(CONF_DELAY))
        self._duration = wash_td(config.get(CONF_DURATION))
        self._repeat = config.get(CONF_REPEAT, 1)
        return self


class IUSequence(IUBase):
    """Irrigation Unlimited Sequence class"""

    def __init__(
        self, hass: HomeAssistant, coordinator, controller, sequence_index: int
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
        # Private variables
        self._schedules = []
        self._zones = []
        return

    @property
    def schedules(self) -> list:
        return self._schedules

    @property
    def zones(self) -> list:
        return self._zones

    @property
    def delay(self) -> timedelta:
        return self._delay

    @property
    def duration(self) -> timedelta:
        return self._duration

    @property
    def repeat(self) -> int:
        return self._repeat

    def clear(self) -> None:
        """Reset this sequence"""
        return

    def add_schedule(self, schedule: IUSchedule) -> IUSchedule:
        """Add a new schedule to the sequence"""
        self._schedules.append(schedule)
        return schedule

    def find_add_schedule(self, coordinator, controller, index: int) -> IUSchedule:
        if index >= len(self._schedules):
            return self.add_schedule(IUSchedule(self._hass, index, self))
        else:
            return self._schedules[index]

    def add_zone(self, zone: IUSequenceZone) -> IUSequenceZone:
        """Add a new zone to the sequence"""
        self._zones.append(zone)
        return zone

    def find_add_zone(self, coordinator, controller, index: int) -> IUSequenceZone:
        if index >= len(self._zones):
            return self.add_zone(
                IUSequenceZone(self._hass, coordinator, controller, self, index)
            )
        else:
            return self._zones[index]

    def load(self, config: OrderedDict):
        """ Load sequence data from the configuration"""
        self.clear()
        self._name = config.get(CONF_NAME, f"Run {self.index + 1}")
        self._delay = wash_td(config.get(CONF_DELAY))
        self._duration = wash_td(config.get(CONF_DURATION))
        self._repeat = config.get(CONF_REPEAT, 1)
        for si, schedule_config in enumerate(config[CONF_SCHEDULES]):
            self.find_add_schedule(self._coordinator, self._controller, si).load(
                schedule_config
            )
        for zi, zone_config in enumerate(config[CONF_ZONES]):
            self.find_add_zone(self._coordinator, self._controller, zi).load(
                zone_config
            )
        return self


class IUController(IUBase):
    """Irrigation Unlimited Controller (Master) class"""

    def __init__(self, hass: HomeAssistant, coordinator, controller_index: int) -> None:
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
        self._zones: list(IUZone) = []
        self._sequences: list(IUSequence) = []
        self._run_queue = IUZoneQueue()
        self._master_sensor: Entity = None
        self._is_on: bool = False
        self._sensor_update_required: bool = False
        self._sensor_last_update: datetime = None
        self._dirty: bool = True
        return

    @property
    def zones(self) -> list:
        return self._zones

    @property
    def runs(self) -> IUZoneQueue:
        return self._run_queue

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def is_setup(self) -> bool:
        return self._is_setup()

    @property
    def enabled(self) -> bool:
        """Return true is this zone is on"""
        return self._is_enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable/disable this controller"""
        if value != self._is_enabled:
            self._is_enabled = value
            self._dirty = True
            self.request_update()
        return

    @property
    def master_sensor(self) -> Entity:
        return self._master_sensor

    @master_sensor.setter
    def master_sensor(self, value: Entity):
        self._master_sensor = value
        return

    @property
    def preamble(self) -> timedelta:
        return self._preamble

    @property
    def status(self) -> str:
        return self._status()

    @property
    def is_paused(self) -> bool:
        return self._run_queue.in_sequence

    def _status(self) -> str:
        """Return status of the controller"""
        if self._initialised:
            if self._is_enabled:
                if self._is_on:
                    return STATE_ON
                else:
                    if self._run_queue.in_sequence:
                        return STATUS_PAUSED
                    else:
                        return STATE_OFF
            else:
                return STATUS_DISABLED
        else:
            return STATUS_INITIALISING

    def _is_setup(self) -> bool:
        if not self._initialised:
            self._initialised = self._master_sensor is not None

            if self._initialised:
                for zone in self._zones:
                    self._initialised = self._initialised and zone.is_setup
        return self._initialised

    def add_zone(self, zone: IUZone) -> IUZone:
        """Add a new zone to the controller"""
        self._zones.append(zone)
        return zone

    def find_add_zone(self, coordinator, controller, index: int) -> IUZone:
        if index >= len(self._zones):
            return self.add_zone(IUZone(self._hass, coordinator, controller, index))
        else:
            return self._zones[index]

    def add_sequence(self, sequence: IUSequence) -> IUSequence:
        """Add a new sequence to the controller"""
        self._sequences.append(sequence)
        return sequence

    def find_add_sequence(self, coordinator, controller, index: int) -> IUSequence:
        if index >= len(self._sequences):
            return self.add_sequence(
                IUSequence(self._hass, coordinator, controller, index)
            )
        else:
            return self._sequences[index]

    def find_zone_by_zone_id(self, zone_id: str) -> IUZone:
        for zone in self._zones:
            if zone.zone_id == zone_id:
                return zone
        return None

    def clear(self) -> None:
        # Don't clear zones
        # self._zones.clear()
        self._is_on = False
        return

    def load(self, config: OrderedDict):
        """Load config data for the controller"""
        self.clear()
        self._is_enabled = config.get(CONF_ENABLED, True)
        self._name = config.get(CONF_NAME, f"Controller {self.index + 1}")
        self._switch_entity_id = config.get(CONF_ENTITY_ID)
        self._preamble = wash_td(config.get(CONF_PREAMBLE))
        self._postamble = wash_td(config.get(CONF_POSTAMBLE))
        for zi, zone_config in enumerate(config[CONF_ZONES]):
            self.find_add_zone(self._coordinator, self, zi).load(
                zone_config, config.get(CONF_ALL_ZONES_CONFIG, None)
            )
        if CONF_SEQUENCES in config:
            for qi, sequence_config in enumerate(config[CONF_SEQUENCES]):
                self.find_add_sequence(self._coordinator, self, qi).load(
                    sequence_config
                )

        self._dirty = True
        return self

    def muster_sequence(
        self, time: datetime, sequence: IUSequence, schedule: IUSchedule
    ) -> int:
        status: int = 0

        sid = uuid.uuid4().int
        sidx: int = 0
        next_run: datetime = None
        for i in range(sequence.repeat):  # pylint: disable=unused-variable
            for sequence_zone in sequence.zones:
                zone: IUZone = self.find_zone_by_zone_id(sequence_zone.zone_id)
                if zone is not None:

                    # Initialise on first pass
                    if next_run is None:
                        last_time = zone.runs.last_time(time)
                        next_time = zone.runs.find_last_date(schedule.id)
                        if next_time is not None:
                            next_time += granularity_time()
                        else:
                            next_time = time
                        next_run = schedule.get_next_run(next_time)
                        if next_run > last_time:
                            return status  # Exit if queue is full

                    # Calculate duration
                    if sequence_zone.duration is not None:
                        duration = sequence_zone.duration
                    else:
                        duration = sequence.duration
                    if duration is None:
                        duration = granularity_time()
                    if zone.adjustment is not None:
                        duration = zone.adjustment.adjust(duration)

                    # Calculate delay
                    if sequence_zone.delay is not None:
                        delay = sequence_zone.delay
                    else:
                        delay = sequence.delay
                    if delay is None:
                        delay = timedelta(0)

                    for j in range(  # pylint: disable=unused-variable
                        sequence_zone.repeat
                    ):
                        zone.runs.add(
                            next_run,
                            duration,
                            zone,
                            schedule,
                            sid,
                            sidx,
                            sequence,
                            sequence_zone,
                        )
                        sidx += 1
                        next_run += duration + delay
                    zone.request_update()
                    status |= IURunQueue.RQ_STATUS_EXTENDED

        return status

    def muster(self, time: datetime, force: bool) -> int:
        """Calculate run times for this controller. This is where most of the hard yakka
        is done."""
        status: int = 0

        if self._dirty or force:
            self._run_queue.clear_all()
            for zone in self._zones:
                zone.clear_run_queue()
            status |= IURunQueue.RQ_STATUS_CLEARED

        zone_status: int = 0

        # Handle initialisation
        for zone in self._zones:
            zone_status |= zone.muster(time)

        # Process sequence schedules
        for sequence in self._sequences:
            for schedule in sequence.schedules:
                while True:
                    sequence_status = self.muster_sequence(time, sequence, schedule)
                    zone_status |= sequence_status
                    if sequence_status & IURunQueue.RQ_STATUS_EXTENDED == 0:
                        break

        # Process zone schedules
        for zone in self._zones:
            zone_status |= zone.muster_schedules(time)
            zone_status |= zone.runs.update_queue(time)

        if (
            zone_status
            & (
                IURunQueue.RQ_STATUS_CLEARED
                | IURunQueue.RQ_STATUS_EXTENDED
                | IURunQueue.RQ_STATUS_SORTED
                | IURunQueue.RQ_STATUS_CANCELED
            )
            != 0
        ):
            all = bool(
                zone_status
                & (IURunQueue.RQ_STATUS_CLEARED | IURunQueue.RQ_STATUS_CANCELED)
            )
            status |= self._run_queue.rebuild_schedule(
                time, self._zones, self._preamble, self._postamble, all
            )
        else:
            status |= self._run_queue.update_queue(time)

        if status != 0:
            self.request_update()

        self._dirty = False
        return status | zone_status

    def check_run(self, time: datetime) -> bool:
        """Check the run status and update sensors. Return flag
        if anything has changed."""
        zones_changed: list(int) = []
        is_running: bool = False
        state_changed: bool = False

        # Gather zones that have changed status
        for zone in self._zones:
            if zone.check_run(time, self._is_enabled):
                zones_changed.append(zone.index)

        # Handle off zones before master
        for index in zones_changed:
            z: IUZone = self._zones[index]
            if not z.is_on:
                z.call_switch(SERVICE_TURN_OFF)
                write_status_to_log(time, self, z)

        # Check if master has changed and update
        is_running = self._is_enabled and self._run_queue.current_run is not None
        state_changed = is_running ^ self._is_on
        if state_changed:
            self._is_on = not self._is_on
            self.request_update()
            self.call_switch(SERVICE_TURN_ON if self._is_on else SERVICE_TURN_OFF)
            write_status_to_log(time, self, None)

        # Handle on zones after master
        for index in zones_changed:
            z: IUZone = self._zones[index]
            if z.is_on:
                z.call_switch(SERVICE_TURN_ON)
                write_status_to_log(time, self, z)

        return state_changed

    def request_update(self) -> None:
        """Flag the sensor needs an update. The actual update is done
        in update_sensor"""
        self._sensor_update_required = True
        return

    def update_sensor(self, time: datetime) -> None:
        """Lazy sensor updater."""
        self._run_queue.update_sensor(time)

        for zone in self._zones:
            zone.update_sensor(time, False)

        if self._master_sensor is not None:
            do_update: bool = self._sensor_update_required

            # If we are running then update sensor according to refresh_interval
            if self._run_queue.current_run is not None:
                do_update = (
                    do_update
                    or self._sensor_last_update is None
                    or time - self._sensor_last_update
                    >= self._coordinator.refresh_interval
                )

            if do_update:
                self._master_sensor.schedule_update_ha_state()
                self._sensor_update_required = False
                self._sensor_last_update = time

        for zone in self._zones:
            zone.update_sensor(time, True)
        return

    def call_switch(self, service_type: str) -> None:
        """Update the linked entity if enabled"""
        if self._switch_entity_id is not None:
            self._hass.async_create_task(
                self._hass.services.async_call(
                    homeassistant.core.DOMAIN,
                    service_type,
                    {ATTR_ENTITY_ID: self._switch_entity_id},
                )
            )
        return


class IUCoordinator:
    """Irrigation Unimited Coordinator class"""

    def __init__(self, hass: HomeAssistant) -> None:
        # Passed parameters
        self._hass = hass
        # Config parameters
        self._testing: bool = False  # Flag we are in testing mode
        self._test_name: str = None
        self._test_speed: float = 1.0
        self._test_times = []
        self._refresh_interval: timedelta = None
        # Private variables
        self._controllers: list(IUController) = []
        self._is_on: bool = False
        self._dirty: bool = True
        # self._component_sensor_issetup: bool = False
        self._component = None
        self._initialised: bool = False
        self._last_muster: datetime = None
        self._muster_required: bool = False
        self._remove_listener: CALLBACK_TYPE = None
        # Testing variables
        self._testing: bool = False
        self._test_number: int = 0
        self._test_delta: timedelta = None
        self._test_start: datetime = None
        self._test_end: datetime = None
        return

    @property
    def is_setup(self) -> bool:
        return self._is_setup()

    @property
    def component(self):
        return self._component

    @component.setter
    def component(self, value) -> None:
        self._component = value
        return

    @property
    def refresh_interval(self) -> timedelta:
        return self._refresh_interval

    def _is_setup(self) -> bool:
        """Wait for sensors to be setup"""
        all_setup: bool = self._hass.is_running and self._component is not None
        for controller in self._controllers:
            all_setup = all_setup and controller.is_setup
        return all_setup

    def _is_testing(self) -> bool:
        return self._testing and self._test_end is not None

    def add(self, controller: IUController) -> IUController:
        """Add a new controller to the system"""
        self._controllers.append(controller)
        return controller

    def find_add(self, coordinator, index: int) -> IUController:
        if index >= len(self._controllers):
            return self.add(IUController(self._hass, coordinator, index))
        else:
            return self._controllers[index]

    def clear(self) -> None:
        # Don't clear controllers
        # self._controllers.clear()
        self._is_on: bool = False
        return

    def load(self, config: OrderedDict):
        """Load config data for the system"""
        self.clear()

        global SYSTEM_GRANULARITY
        SYSTEM_GRANULARITY = config.get(CONF_GRANULARITY, DEFAULT_GRANULATITY)
        self._refresh_interval = timedelta(
            seconds=config.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL)
        )
        if CONF_TESTING in config:
            test_config = config[CONF_TESTING]
            self._testing = test_config.get(CONF_ENABLED, False)
            self._test_speed = test_config.get(CONF_SPEED, DEFAULT_TEST_SPEED)
            for test in test_config[CONF_TIMES]:
                start = wash_dt(dt.as_utc(test[CONF_START]))
                end = wash_dt(dt.as_utc(test[CONF_END]))
                if CONF_NAME in test[CONF_NAME]:
                    name = test[CONF_NAME]
                else:
                    name = None
                self._test_times.append({"name": name, "start": start, "end": end})

        for ci, controller_config in enumerate(config[CONF_CONTROLLERS]):
            self.find_add(self, ci).load(controller_config)

        self._dirty = True
        self._muster_required = True
        return self

    def muster(self, time: datetime, force: bool) -> int:
        """Calculate run times for system"""
        status: int = 0

        for controller in self._controllers:
            status |= controller.muster(time, force)
        self._dirty = False

        return status

    def check_run(self, time: datetime) -> bool:
        """Update run status"""
        is_running: bool = False

        for controller in self._controllers:
            is_running = is_running or controller.check_run(time)

        return is_running

    def update_sensor(self, time: datetime) -> None:
        """Update home assistant sensors if required"""
        for controller in self._controllers:
            controller.update_sensor(time)
        return

    def poll(self, time: datetime, force: bool = False) -> None:
        """Poll the system for changes, updates and refreshes"""
        wtime: datetime = wash_dt(time)
        if (wtime != self._last_muster) or self._muster_required:
            if self.muster(wtime, force) != 0:
                self.check_run(wtime)
            self._muster_required = False
            self._last_muster = wtime
        self.update_sensor(wash_dt(time, 1))
        return

    def virtual_time(self, time: datetime) -> datetime:
        """Return the virtual clock. For testing we can speed
        up time. This routine will return a virtual time based
        on the real time and the duration from start. It is in
        effect a test warp speed"""
        virtual_time: datetime = time - self._test_delta
        actual_duration: float = (virtual_time - self._test_start).total_seconds()
        virtual_duration: float = actual_duration * self._test_speed
        test_time: datetime = self._test_start + timedelta(seconds=virtual_duration)
        return test_time

    def poll_test(self, time: datetime) -> None:
        if self._test_start is None:  # Start a new test
            if self._test_number < len(self._test_times):
                d = self._test_times[self._test_number]
                self._test_start = d["start"]
                self._test_end = d["end"]
                self._test_delta = time - self._test_start
                _LOGGER.info(
                    "Running test %d from %s to %s",
                    self._test_number + 1,
                    dt.as_local(self._test_start).strftime("%c"),
                    dt.as_local(self._test_end).strftime("%c"),
                )
                self.poll(self._test_start, True)
            elif self._test_end is not None:  # End of test regime
                self._test_end = None  # Flag all tests run
                _LOGGER.info("All tests completed (Idle)")
                return
            else:  # Out of tests to run
                self.poll(time)
                return
        elif self.virtual_time(time) > self._test_end:  # End of current test
            _LOGGER.info("Test %d completed", self._test_number + 1)
            self._test_start = None  # Flag new test
            self._test_number += 1
        else:  # Continue existing test
            self.poll(self.virtual_time(time))
        return

    def start(self) -> None:
        """Start the system up"""
        track_time = SYSTEM_GRANULARITY / self._test_speed
        track_time = min(1, track_time)  # Run no slower than 1 second for response
        track_time *= 0.95  # Run clock slightly ahead of required to avoid skipping

        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None
        self._remove_listener = async_track_time_interval(
            self._hass, self._async_timer, timedelta(seconds=track_time)
        )
        return

    async def _async_timer(self, time: datetime) -> None:
        """Timer callback"""
        if self._initialised:
            if self._testing:
                self.poll_test(time)
            else:
                self.poll(time)
        else:
            self._initialised = self.is_setup
        return

    def register_entity(
        self, controller: IUController, zone: IUZone, entity: Entity
    ) -> None:
        if controller is None:
            self._component = entity
        elif zone is None:
            controller.master_sensor = entity
        else:
            zone.zone_sensor = entity
        return

    def deregister_entity(
        self, controller: IUController, zone: IUZone, entity: Entity
    ) -> None:
        if controller is None:
            self._component = None
        elif zone is None:
            controller.master_sensor = None
        else:
            zone.zone_sensor = None
        return

    def service_call(
        self,
        service: str,
        controller: IUController,
        zone: IUZone,
        data: MappingProxyType,
    ) -> None:
        """Entry point for all service calls."""
        time: datetime = dt.utcnow()
        if self._is_testing():
            time = self.virtual_time(time)

        def adjust_time_all(
            controller: IUController, data: MappingProxyType, time: datetime
        ) -> None:
            zl = data.get(CONF_ZONES, None)
            for zone in controller.zones:
                if zl is None or zone.zone_index + 1 in zl:
                    zone.service_adjust_time(data, time)
            return

        def manual_run_all(
            controller: IUController, data: MappingProxyType, time: datetime
        ) -> None:
            zl = data.get(CONF_ZONES, None)
            for zone in controller.zones:
                if zl is None or zone.zone_index + 1 in zl:
                    zone.service_manual_run(data, time)
            return

        def cancel_all(
            controller: IUController, data: MappingProxyType, time: datetime
        ) -> None:
            zl = data.get(CONF_ZONES, None)
            for zone in controller.zones:
                if zl is None or zone.zone_index + 1 in zl:
                    zone.service_cancel(data, time)
            return

        def notify_children(controller: IUController) -> None:
            for zone in controller.zones:
                zone.request_update()
            return

        if service == SERVICE_ENABLE:
            if zone is not None:
                zone.enabled = True
            else:
                controller.enabled = True
                notify_children(controller)
        elif service == SERVICE_DISABLE:
            if zone is not None:
                zone.enabled = False
            else:
                controller.enabled = False
                notify_children(controller)
        elif service == SERVICE_TOGGLE:
            if zone is not None:
                zone.enabled = not zone.enabled
            else:
                controller.enabled = not controller.enabled
                notify_children(controller)
        elif service == SERVICE_CANCEL:
            if zone is not None:
                zone.service_cancel(data, time)
            else:
                cancel_all(controller, data, time)
        elif service == SERVICE_TIME_ADJUST:
            if zone is not None:
                zone.service_adjust_time(data, time)
            else:
                adjust_time_all(controller, data, time)
        elif service == SERVICE_MANUAL_RUN:
            if zone is not None:
                zone.service_manual_run(data, time)
            else:
                manual_run_all(controller, data, time)
        else:
            return
        self._muster_required = True
        return


def write_status_to_log(time: datetime, controller: IUController, zone: IUZone) -> None:
    """Output the status of master or zone"""
    if zone is not None:
        zm = f"Zone {zone.index + 1}"
        status = f"{STATE_ON if zone._is_on else STATE_OFF}"
    else:
        zm = "Master"
        status = f"{STATE_ON if controller._is_on else STATE_OFF}"
    _LOGGER.debug(
        "[%s] Controller %d %s is %s",
        datetime.strftime(dt.as_local(time), "%Y-%m-%d %H:%M:%S"),
        controller.index + 1,
        zm,
        status,
    )
    return
