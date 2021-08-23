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
import time as tm

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
    CONF_FINISH,
    CONF_INCREASE,
    CONF_INDEX,
    CONF_OUTPUT_EVENTS,
    CONF_PERCENTAGE,
    CONF_REFRESH_INTERVAL,
    CONF_RESET,
    CONF_RESULTS,
    CONF_SEQUENCES,
    CONF_SEQUENCE_ID,
    CONF_SHOW_LOG,
    CONF_AUTOPLAY,
    CONF_ANCHOR,
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


def reset_granularity() -> None:
    global SYSTEM_GRANULARITY
    SYSTEM_GRANULARITY = DEFAULT_GRANULATITY
    return


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
        return t.timetz()
    else:
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
    else:
        return None


class IUBase:
    """Irrigation Unlimited base class"""

    def __init__(self, index: int) -> None:
        # Private variables
        self._id: int = uuid.uuid4().int
        self._index: int = index
        return

    def __eq__(self, other) -> bool:
        if isinstance(other, IUBase):
            return self.id == other.id
        else:
            return False

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
        self.clear()
        return

    def __str__(self) -> str:
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

    @property
    def has_adjustment(self) -> bool:
        return self._method != None

    def clear(self) -> None:
        self._method: str = None
        self._time_adjustment = None
        self._minimum: timedelta = None
        self._maximum: timedelta = None
        return

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
            new_time = round_td(time * self._time_adjustment / 100)
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


class IUSchedule(IUBase):
    """Irrigation Unlimited Schedule class. Schedules are not actual
    points in time but describe a future event i.e. next Monday"""

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
    def duration(self) -> timedelta:
        """Return the duration"""
        return self._duration

    def clear(self) -> None:
        """Reset this schedule"""
        self._dirty = True
        return

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

    def get_next_run(
        self, atime: datetime, ftime: datetime, adjusted_duration: timedelta
    ) -> datetime:
        """
        Determine the next start time. Date processing in this routine
        is done in local time and returned as UTC
        """
        local_time = dt.as_local(atime)
        final_time = dt.as_local(ftime)

        next_run: datetime = None
        while True:

            if next_run is None:  # Initialise on first pass
                next_run = local_time
            else:
                next_run += timedelta(days=1)  # Advance to next day

            # Sanity check. Note: Astral events like sunrise might take months i.e. Antarctica winter
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

    def __init__(
        self,
        start_time: datetime,
        duration: timedelta,
        zone: "IUZone",
        schedule: "IUSchedule",
        sequence_run: "IUSequenceRun",
    ) -> None:
        super().__init__(None)
        # Passed parameters
        self._start_time: datetime = start_time
        self._duration: timedelta = duration
        self._zone = zone
        self._schedule = schedule
        self._sequence_run = sequence_run
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
    def zone(self) -> "IUSchedule":
        return self._zone

    @property
    def schedule(self) -> "IUSchedule":
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
    def is_sequence(self) -> bool:
        return self._sequence_run is not None

    @property
    def sequence_run(self) -> "IUSequenceRun":
        return self._sequence_run

    @property
    def sequence(self) -> "IUSequence":
        if self.is_sequence:
            return self._sequence_run.sequence
        else:
            return None

    @property
    def sequence_zone(self) -> "IUSequenceZone":
        if self.is_sequence:
            return self._sequence_run.sequence_zone(self)
        else:
            return None

    @property
    def sequence_id(self) -> int:
        if self.is_sequence:
            return self._sequence_run._id
        else:
            return None

    @property
    def sequence_running(self) -> bool:
        return self.is_sequence and self._sequence_run.running

    @sequence_running.setter
    def sequence_running(self, value: bool) -> None:
        """Flag sequence is now running"""
        if self.is_sequence:
            self.sequence_run.running = value
        return

    @property
    def crumbs(self) -> str:
        return self._crumbs()

    def _crumbs(self) -> str:
        def get_index(object: IUBase) -> int:
            if object is not None:
                return object.index + 1
            else:
                return 0

        if self.is_sequence:
            sidx = self.sequence_run.run_index(self) + 1
        else:
            sidx = 0
        return f"{get_index(self._zone)}.{get_index(self._schedule)}.{get_index(self.sequence)}.{get_index(self.sequence_zone)}.{sidx}"

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

    def sequence_start(self, time: datetime) -> bool:
        """Check if sequence is about to start but not yet flagged"""
        result = (
            self.is_sequence
            and self.is_running(time)
            and not self._sequence_run.running
        )
        if result:
            self._sequence_run.running = True
        return result

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
    RQ_STATUS_CHANGED: int = 0x40

    def __init__(self) -> None:
        # Private variables
        self._current_run: IURun = None
        self._next_run: IURun = None
        self._sorted: bool = False
        self._cancel_request: bool = False
        self._future_span = wash_td(timedelta(days=self.DAYS_SPAN))
        return

    @property
    def current_run(self) -> IURun:
        return self._current_run

    @property
    def next_run(self) -> IURun:
        return self._next_run

    @property
    def in_sequence(self) -> bool:
        return self._in_sequence()

    def _in_sequence(self) -> bool:
        for run in self:
            if run.sequence_running:
                return True
        return False

    def add(
        self,
        start_time: datetime,
        duration: timedelta,
        zone: "IUZone",
        schedule: "IUSchedule",
        sequence_run: "IUSequenceRun",
    ) -> IURun:
        run = IURun(start_time, duration, zone, schedule, sequence_run)
        self.append(run)
        self._sorted = False
        return run

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

    def clear_sequences(self, time: datetime) -> bool:
        """Clear out sequences that are not running"""
        modified: bool = False
        if len(self) > 0:
            i = len(self) - 1
            while i >= 0:
                item = self[i]
                if (
                    not (item.is_running(time) or item.is_manual())
                    and item.is_sequence
                    and not item.sequence_running
                ):
                    self.pop(i)
                    modified = True
                i -= 1
        return modified

    def clear(self, time: datetime) -> bool:
        """Clear out the queue except for manual or running schedules"""
        modified: bool = False
        if len(self) > 0:
            i = len(self) - 1
            while i >= 0:
                item: IURun = self[i]
                if not (
                    item.is_running(time) or item.is_manual() or item.sequence_running
                ):
                    self.pop(i)
                    modified = True
                i -= 1
            if modified:
                self._next_run = None
                self._sorted = True
        return modified

    def find_last_index(self, id: int) -> int:
        """Return the index of the run that finishes last in the queue.
        This routine does not require the list to be sorted."""
        result: int = None
        last_time: datetime = None
        for i, run in enumerate(self):
            if run.schedule is not None and run.schedule.id == id:
                if last_time is None or run.end_time > last_time:
                    last_time = run.end_time
                    result = i
        return result

    def find_last_run(self, id: int) -> IURun:
        i = self.find_last_index(id)
        if i is not None:
            return self[i]
        else:
            return None

    def find_last_date(self, id: int) -> datetime:
        """Find the last time in the queue for the supplied id"""
        run = self.find_last_run(id)
        if run is not None:
            return run.end_time
        else:
            return None

    def find_manual(self) -> IURun:
        for run in self:
            if run.is_manual():
                return run
        return None

    def last_time(self, time: datetime) -> datetime:
        return time + self._future_span

    def load(self, config: OrderedDict, all_zones: OrderedDict):
        if all_zones is not None:
            self._future_span = wash_td(
                all_zones.get(CONF_FUTURE_SPAN, self._future_span)
            )
        self._future_span = wash_td(config.get(CONF_FUTURE_SPAN, self._future_span))
        self._future_span = max(self._future_span, timedelta(hours=12))
        return self

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

        for run in self:
            if run.sequence_start(time):
                status |= self.RQ_STATUS_CHANGED

        return status

    def update_sensor(self, time: datetime) -> bool:
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

    def __init__(self) -> None:
        super().__init__()
        # Config variables
        self._minimum: timedelta = None
        self._maximum: timedelta = None
        return

    def constrain(self, duration: timedelta) -> timedelta:
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
        return super().add(
            start_time, self.constrain(duration), zone, schedule, sequence_run
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
            else:
                self.remove(run)

        self._current_run = None
        self._next_run = None
        duration = max(duration, granularity_time())
        return self.add(start_time, duration, zone, None, None)

    def merge_one(
        self,
        time: datetime,
        zone: "IUZone",
        schedule: IUSchedule,
        adjustment: IUAdjustment,
    ) -> bool:
        modified: bool = False

        # See if schedule already exists in run queue. If so get
        # the finish time of the last entry.
        next_time = self.find_last_date(schedule.id)
        if next_time is not None:
            next_time += granularity_time()
        else:
            next_time = time

        duration = self.constrain(adjustment.adjust(schedule.duration))
        next_run = schedule.get_next_run(next_time, self.last_time(time), duration)

        if next_run is not None:
            self.add(next_run, duration, zone, schedule, None)
            modified = True

        return modified

    def merge_fill(
        self,
        time: datetime,
        zone: "IUZone",
        schedule: IUSchedule,
        adjustment: IUAdjustment,
    ) -> bool:
        """Merge the schedule into the run queue. Add as many until the span is
        reached. Return True if the schedule was added."""
        modified: bool = False

        while self.merge_one(time, zone, schedule, adjustment):
            modified = True

        return modified

    def load(self, config: OrderedDict, all_zones: OrderedDict) -> "IUScheduleQueue":
        super().load(config, all_zones)
        if all_zones is not None:
            self._minimum = wash_td(all_zones.get(CONF_MINIMUM, self._minimum))
            self._maximum = wash_td(all_zones.get(CONF_MAXIMUM, self._maximum))
        self._minimum = wash_td(config.get(CONF_MINIMUM, self._minimum))
        self._maximum = wash_td(config.get(CONF_MAXIMUM, self._maximum))
        return self

    def update_queue(
        self,
        time: datetime,
    ) -> int:
        return super().update_queue(time)


class IUZone(IUBase):
    """Irrigation Unlimited Zone class"""

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
        self._schedules: list[IUSchedule] = []
        self._run_queue = IUScheduleQueue()
        self._adjustment = IUAdjustment()
        self._zone_sensor: Entity = None
        self._is_on: bool = False
        self._sensor_update_required: bool = False
        self._sensor_last_update: datetime = None
        self._dirty: bool = True
        return

    @property
    def schedules(self) -> "list[IUSchedule]":
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
        """Return true if this zone is enabled"""
        return self._is_enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
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
    def zone_sensor(self, value: Entity) -> None:
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

    def find_add(self, index: int) -> IUSchedule:
        if index >= len(self._schedules):
            return self.add(IUSchedule(self._hass, index))
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
        self._adjustment = IUAdjustment()
        self._is_on = False
        return

    def clear_sequence_runs(self, time: datetime) -> None:
        self._run_queue.clear_sequences(time)
        return

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
            for si, schedule_config in enumerate(config[CONF_SCHEDULES]):
                self.find_add(si).load(schedule_config)
        self._dirty = True
        return self

    def as_dict(self) -> OrderedDict:
        dict = OrderedDict()
        dict[CONF_INDEX] = self._index
        dict[CONF_NAME] = self.name
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
                    # Force a refresh at midnight for the total_today attribute
                    if (
                        self._sensor_last_update is not None
                        and dt.as_local(self._sensor_last_update).toordinal()
                        != dt.as_local(time).toordinal()
                    ):
                        do_update = True
                    do_update |= self._sensor_update_required
            else:
                if self._is_on:
                    # If we are running then update sensor according to refresh_interval
                    if self._run_queue.current_run is not None:
                        do_update = (
                            self._sensor_last_update is None
                            or time - self._sensor_last_update
                            >= self._coordinator.refresh_interval
                        )
                    do_update |= self._sensor_update_required
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

    def add_zone(
        self,
        start_time: datetime,
        duration: timedelta,
        zone: IUZone,
        schedule: IUSchedule,
        sequence_run: "IUSequenceRun",
        preamble: timedelta,
        postamble: timedelta,
    ) -> IURun:
        """Add a new master run to the queue"""
        if preamble is not None:
            start_time -= preamble
            duration += preamble
        if postamble is not None:
            duration += postamble
        run = self.find_run(start_time, duration, zone, schedule, sequence_run)
        if run is None:
            run = self.add(start_time, duration, zone, schedule, sequence_run)
        return run

    def find_run(
        self,
        start_time: datetime,
        duration: timedelta,
        zone: IUZone,
        schedule: IUSchedule,
        sequence_run: "IUSequenceRun",
    ) -> IURun:
        for run in self:
            if (
                start_time == run.start_time
                and zone == run.zone
                and run.schedule is not None
                and schedule is not None
                and run.schedule == schedule
            ):
                return run
        return None

    def rebuild_schedule(
        self,
        time: datetime,
        zones: "list[IUZone]",
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
            for run in zone.runs:
                self.add_zone(
                    run.start_time,
                    run.duration,
                    run.zone,
                    run.schedule,
                    run.sequence_run,
                    preamble,
                    postamble,
                )
        status |= IURunQueue.RQ_STATUS_EXTENDED | IURunQueue.RQ_STATUS_REDUCED
        status |= self.update_queue(time)
        return status


class IUSequenceZone(IUBase):
    """Irrigation Unlimited Sequence Zone class"""

    def __init__(
        self,
        zone_index: int,
    ) -> None:
        super().__init__(zone_index)
        # Passed parameters
        # Config parameters
        self._zone_ids: list[str] = None
        self._delay: timedelta = None
        self._duration: timedelta = None
        self._repeat: int = None
        # Private variables
        return

    @property
    def zone_ids(self) -> "list[str]":
        return self._zone_ids

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

    def load(self, config: OrderedDict) -> "IUSequenceZone":
        """Load sequence zone data from the configuration"""
        self.clear()
        self._zone_ids = config[CONF_ZONE_ID]
        self._delay = wash_td(config.get(CONF_DELAY))
        self._duration = wash_td(config.get(CONF_DURATION))
        self._repeat = config.get(CONF_REPEAT, 1)
        return self


class IUSequence(IUBase):
    """Irrigation Unlimited Sequence class"""

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
        # Private variables
        self._schedules: list[IUSchedule] = []
        self._zones: list[IUSequenceZone] = []
        self._adjustment = IUAdjustment()
        return

    @property
    def schedules(self) -> "list[IUSchedule]":
        return self._schedules

    @property
    def zones(self) -> "list[IUSequenceZone]":
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

    @property
    def adjustment(self) -> IUAdjustment:
        return self._adjustment

    @property
    def has_adjustment(self) -> bool:
        return self._adjustment.has_adjustment

    def zone_enabled(self, sequence_zone: IUSequenceZone) -> bool:
        """Return True if at least one real zone referenced by the
        sequence_zone is enabled"""
        for zone_id in sequence_zone.zone_ids:
            zone = self._controller.find_zone_by_zone_id(zone_id)
            if zone is not None and zone.enabled:
                return True
        return False

    def zone_duration(self, sequence_zone: IUSequenceZone) -> timedelta:
        """Return the duration for the specified zone"""
        if self.zone_enabled(sequence_zone):
            if sequence_zone.duration is not None:
                duration = sequence_zone.duration
            else:
                duration = self._duration
            if duration is None:
                duration = granularity_time()
            for zone_id in sequence_zone.zone_ids:
                zone = self._controller.find_zone_by_zone_id(zone_id)
                if zone is not None:
                    duration = zone.runs.constrain(duration)
            return duration
        else:
            return timedelta(0)

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
        else:
            return timedelta(0)

    def total_duration(self) -> timedelta:
        """Return the total duration for all the zones"""
        duration = timedelta(0)
        for zone in self._zones:
            duration += self.zone_duration(zone) * zone.repeat
        duration *= self._repeat
        return duration

    def total_delay(self) -> timedelta:
        """Return the total delay for all the zones"""
        delay = timedelta(0)
        for zone in self._zones:
            delay += self.zone_delay(zone) * zone.repeat
        delay *= self._repeat
        delay -= self.zone_delay(zone)
        return delay

    def total_time(self) -> timedelta:
        """Return the total time for the sequence"""
        return self.total_duration() + self.total_delay()

    def duration_multiplier(self, total_time: timedelta) -> float:
        """Given a new total run time, calculate how much to shrink or expand each
        zone duration. Final time will be approximate as the new durations must
        be rounded to internal boundaries"""
        total_duration = self.total_duration()
        if total_time is not None and total_duration != timedelta(0):
            return (total_time - self.total_delay()) / total_duration
        else:
            return 1.0

    def clear(self) -> None:
        """Reset this sequence"""
        self._schedules.clear()
        self._zones.clear()
        self._adjustment.clear()
        return

    def add_schedule(self, schedule: IUSchedule) -> IUSchedule:
        """Add a new schedule to the sequence"""
        self._schedules.append(schedule)
        return schedule

    def find_add_schedule(self, index: int) -> IUSchedule:
        if index >= len(self._schedules):
            return self.add_schedule(IUSchedule(self._hass, index))
        else:
            return self._schedules[index]

    def add_zone(self, zone: IUSequenceZone) -> IUSequenceZone:
        """Add a new zone to the sequence"""
        self._zones.append(zone)
        return zone

    def find_add_zone(self, index: int) -> IUSequenceZone:
        if index >= len(self._zones):
            return self.add_zone(IUSequenceZone(index))
        else:
            return self._zones[index]

    def zone_ids(self) -> str:
        for sequence_zone in self._zones:
            for zone_id in sequence_zone.zone_ids:
                yield zone_id

    def load(self, config: OrderedDict) -> "IUSequence":
        """Load sequence data from the configuration"""
        self.clear()
        self._name = config.get(CONF_NAME, f"Run {self.index + 1}")
        self._delay = wash_td(config.get(CONF_DELAY))
        self._duration = wash_td(config.get(CONF_DURATION))
        self._repeat = config.get(CONF_REPEAT, 1)
        for zi, zone_config in enumerate(config[CONF_ZONES]):
            self.find_add_zone(zi).load(zone_config)
        for si, schedule_config in enumerate(config[CONF_SCHEDULES]):
            self.find_add_schedule(si).load(schedule_config)
        return self

    def as_dict(self) -> OrderedDict:
        dict = OrderedDict()
        dict[CONF_INDEX] = self._index
        dict[CONF_NAME] = self._name
        return dict


class IUSequenceRun(IUBase):
    """Irrigation Unlimited sequence run manager class"""

    def __init__(self, sequence: IUSequence) -> None:
        super().__init__(None)
        # Passed parameters
        self._sequence = sequence
        # Private variables
        self._runs: OrderedDict = {}
        self._running = False
        return

    @property
    def sequence(self) -> IUSequence:
        return self._sequence

    @property
    def running(self) -> bool:
        return self._running

    @running.setter
    def running(self, value: bool) -> None:
        """Flag sequence is now running"""
        self._running = value
        return

    def add(self, run: IURun, sequence_zone: IUSequenceZone) -> None:
        self._runs[run.id] = sequence_zone
        return

    def run_index(self, run: IURun) -> int:
        return list(self._runs.keys()).index(run.id)

    def sequence_zone(self, run: IURun) -> IUSequenceZone:
        return self._runs.get(run.id, None)


class IUController(IUBase):
    """Irrigation Unlimited Controller (Master) class"""

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
        self._zones: list[IUZone] = []
        self._sequences: list[IUSequence] = []
        self._run_queue = IUZoneQueue()
        self._master_sensor: Entity = None
        self._is_on: bool = False
        self._sensor_update_required: bool = False
        self._sensor_last_update: datetime = None
        self._dirty: bool = True
        return

    @property
    def zones(self) -> "list[IUZone]":
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
            self.notify_children()
        return

    @property
    def master_sensor(self) -> Entity:
        return self._master_sensor

    @master_sensor.setter
    def master_sensor(self, value: Entity) -> None:
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

    def find_add_zone(
        self, coordinator: "IUCoordinator", controller: "IUController", index: int
    ) -> IUZone:
        if index >= len(self._zones):
            return self.add_zone(IUZone(self._hass, coordinator, controller, index))
        else:
            return self._zones[index]

    def add_sequence(self, sequence: IUSequence) -> IUSequence:
        """Add a new sequence to the controller"""
        self._sequences.append(sequence)
        return sequence

    def find_sequence(self, index: int) -> IUSequence:
        if index >= 0 and index < len(self._sequences):
            return self._sequences[index]
        else:
            return None

    def find_add_sequence(
        self, coordinator: "IUCoordinator", controller: "IUController", index: int
    ) -> IUSequence:
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
        self._sequences.clear()
        self._is_on = False
        return

    def clear_sequence_runs(self, time: datetime) -> None:
        for zone in self._zones:
            zone.clear_sequence_runs(time)
        return

    def notify_children(self) -> None:
        for zone in self._zones:
            zone.request_update()
        return

    def load(self, config: OrderedDict) -> "IUController":
        """Load config data for the controller"""
        self.clear()
        self._is_enabled = config.get(CONF_ENABLED, True)
        self._name = config.get(CONF_NAME, f"Controller {self.index + 1}")
        self._switch_entity_id = config.get(CONF_ENTITY_ID)
        self._preamble = wash_td(config.get(CONF_PREAMBLE))
        self._postamble = wash_td(config.get(CONF_POSTAMBLE))
        all_zones = config.get(CONF_ALL_ZONES_CONFIG)
        for zi, zone_config in enumerate(config[CONF_ZONES]):
            self.find_add_zone(self._coordinator, self, zi).load(zone_config, all_zones)
        if CONF_SEQUENCES in config:
            for qi, sequence_config in enumerate(config[CONF_SEQUENCES]):
                self.find_add_sequence(self._coordinator, self, qi).load(
                    sequence_config
                )

        self._dirty = True
        return self

    def as_dict(self) -> OrderedDict:
        dict = OrderedDict()
        dict[CONF_INDEX] = self._index
        dict[CONF_NAME] = self._name
        dict[CONF_ZONES] = []
        for zone in self._zones:
            dict[CONF_ZONES].append(zone.as_dict())
        dict[CONF_SEQUENCES] = []
        for sequence in self._sequences:
            dict[CONF_SEQUENCES].append(sequence.as_dict())
        return dict

    def muster_sequence(
        self,
        time: datetime,
        sequence: IUSequence,
        schedule: IUSchedule,
        total_duration: timedelta = None,
    ) -> int:
        def init_run_time(
            time: datetime,
            schedule: IUSchedule,
            zone: IUZone,
            total_duration: timedelta,
        ) -> datetime:
            if schedule is not None:
                next_time = zone.runs.find_last_date(schedule.id)
                if next_time is not None:
                    next_time += granularity_time()
                else:
                    next_time = time
                next_run = schedule.get_next_run(
                    next_time, zone.runs.last_time(time), total_duration
                )
            else:
                next_run = time + granularity_time()
            return next_run

        def calc_total_duration(
            total_duration: timedelta, sequence: IUSequence, schedule: IUSchedule
        ) -> timedelta:
            """Calculate the total duration of the sequence"""
            if total_duration is None:
                if schedule is not None and schedule.duration is not None:
                    total_duration = schedule.duration
                else:
                    total_duration = sequence.total_time()
            if schedule is not None and sequence.has_adjustment:
                total_delay = sequence.total_delay()
                total_duration = (
                    sequence.adjustment.adjust(total_duration - total_delay)
                    + total_delay
                )
                if total_duration < total_delay:
                    total_duration = total_delay  # Make run time 0
            return total_duration

        total_duration = calc_total_duration(total_duration, sequence, schedule)
        duration_multiplier = sequence.duration_multiplier(total_duration)
        status: int = 0
        next_run: datetime = None
        sequence_run: IUSequenceRun = None
        for i in range(sequence.repeat):  # pylint: disable=unused-variable
            for sequence_zone in sequence.zones:
                duration = round_td(
                    sequence.zone_duration(sequence_zone) * duration_multiplier
                )
                duration_max = timedelta(0)
                delay = sequence.zone_delay(sequence_zone)
                for zone in (
                    self.find_zone_by_zone_id(zone_id)
                    for zone_id in sequence_zone.zone_ids
                ):
                    if zone is not None and zone.enabled:
                        # Initialise on first pass
                        if next_run is None:
                            next_run = init_run_time(
                                time, schedule, zone, total_duration
                            )
                            if next_run is None:
                                return status  # Exit if queue is full
                            sequence_run = IUSequenceRun(sequence)

                        # Don't adjust manual run and no adjustment on adjustment
                        if schedule is not None and not sequence.has_adjustment:
                            duration_adjusted = zone.adjustment.adjust(duration)
                        else:
                            duration_adjusted = duration
                        duration_adjusted = zone.runs.constrain(duration_adjusted)

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
                    sequence_status = self.muster_sequence(
                        time, sequence, schedule, None
                    )
                    zone_status |= sequence_status
                    if sequence_status & IURunQueue.RQ_STATUS_EXTENDED == 0:
                        break

        # Process zone schedules
        for zone in self._zones:
            if zone.enabled:
                zone_status |= zone.muster_schedules(time)

        # Post processing
        for zone in self._zones:
            zone_status |= zone.runs.update_queue(time)

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
        zones_changed: list[int] = []
        is_running: bool = False
        state_changed: bool = False

        # Gather zones that have changed status
        for zone in self._zones:
            if zone.check_run(time, self._is_enabled):
                zones_changed.append(zone.index)

        # Handle off zones before master
        for zone in (self._zones[i] for i in zones_changed):
            if not zone.is_on:
                zone.call_switch(SERVICE_TURN_OFF)
                self._coordinator.status_changed(time, self, zone, zone.is_on)

        # Check if master has changed and update
        is_running = self._is_enabled and self._run_queue.current_run is not None
        state_changed = is_running ^ self._is_on
        if state_changed:
            self._is_on = not self._is_on
            self.request_update()
            self.call_switch(SERVICE_TURN_ON if self._is_on else SERVICE_TURN_OFF)
            self._coordinator.status_changed(time, self, None, self._is_on)

        # Handle on zones after master
        for zone in (self._zones[i] for i in zones_changed):
            if zone.is_on:
                zone.call_switch(SERVICE_TURN_ON)
                self._coordinator.status_changed(time, self, zone, zone.is_on)

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

    def service_adjust_time(self, data: MappingProxyType, time: datetime) -> None:
        sequence_id = data.get(CONF_SEQUENCE_ID, None)
        if sequence_id is None:
            zl: list[int] = data.get(CONF_ZONES, None)
            for zone in self._zones:
                if zl is None or zone.index + 1 in zl:
                    zone.service_adjust_time(data, time)
        else:
            sequence = self.find_sequence(sequence_id - 1)
            if sequence is not None:
                if sequence.adjustment.load(data):
                    for zone_id in sequence.zone_ids():
                        zone = self.find_zone_by_zone_id(zone_id)
                        if zone is not None:
                            zone.runs.clear(time)
        return

    def service_manual_run(self, data: MappingProxyType, time: datetime) -> None:
        sequence_id = data.get(CONF_SEQUENCE_ID, None)
        if sequence_id is None:
            zl: list[int] = data.get(CONF_ZONES, None)
            for zone in self._zones:
                if zl is None or zone.index + 1 in zl:
                    zone.service_manual_run(data, time)
        else:
            sequence = self.find_sequence(sequence_id - 1)
            if sequence is not None:
                self.muster_sequence(time, sequence, None, wash_td(data[CONF_TIME]))
        return

    def service_cancel(self, data: MappingProxyType, time: datetime) -> None:
        zl: list[int] = data.get(CONF_ZONES, None)
        for zone in self._zones:
            if zl is None or zone.index + 1 in zl:
                zone.service_cancel(data, time)
        return


class IUEvent:
    def __init__(self) -> None:
        # Private variables
        self._time: datetime = None
        self._controller: IUController = None
        self._zone: IUZone = None
        self._state: bool = None
        self._crumbs: str = None
        return

    def __eq__(self, other: "IUEvent") -> bool:
        return (
            self._time == other._time
            and self._controller == other.controller
            and self._zone == other.zone
            and self._state == other.state
        )

    @property
    def time(self) -> datetime:
        return self._time

    @property
    def controller(self) -> IUController:
        return self._controller

    @property
    def zone(self) -> IUZone:
        return self._zone

    @property
    def state(self) -> bool:
        return self._state

    @property
    def time_local(self) -> str:
        return self.dt2lstr()

    @property
    def zone_name(self) -> str:
        if self._zone == 0:
            return "Master"
        else:
            return f"Zone {self._zone}"

    def load(self, config: OrderedDict) -> "IUEvent":
        self._time: datetime = wash_dt(dt.as_utc(config["t"]))
        self._controller: int = config["c"]
        self._zone: int = config["z"]
        self._state: bool = config["s"]
        return self

    def load2(
        self, time: datetime, controller: int, zone: int, state: bool, crumbs: str
    ):
        self._time = time
        self._controller = controller
        self._zone = zone
        self._state = state
        self._crumbs = crumbs
        return self

    def dt2lstr(self) -> str:
        """Format the passed datetime into local time"""
        return datetime.strftime(dt.as_local(self._time), "%Y-%m-%d %H:%M:%S")

    def as_str(self) -> str:
        return f"{{t: '{self.time_local}', c: {self._controller}, z: {self._zone}, s: {1 if self._state else 0}}}"

    def as_dict(self):
        return {
            "t": self._time,
            "c": self._controller,
            "z": self._zone,
            "s": self._state,
        }

    def write_log(self) -> None:
        """Output the status of master or zone"""
        zm = f"{self.zone_name} is {STATE_ON if self._state else STATE_OFF}"
        if self._zone != 0 and self._state:
            zm = zm + f" [{self._crumbs}]"

        _LOGGER.debug(
            f"[{self.time_local}] Controller {self._controller} %s",
            zm,
        )
        return


class IUTest(IUBase):
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
        return

    @property
    def name(self) -> str:
        return self._name

    @property
    def start(self) -> datetime:
        return self._start

    @property
    def events(self) -> int:
        return self._events

    @property
    def checks(self) -> int:
        return self._checks

    @property
    def errors(self) -> int:
        return self._errors

    @property
    def test_time(self) -> float:
        return self._test_time

    @property
    def virtual_duration(self) -> timedelta:
        return (self._end - self._start) / self._speed

    @property
    def current_result(self) -> int:
        return self._current_result

    @property
    def total_results(self) -> int:
        return len(self._results)

    def is_finished(self, time) -> bool:
        return self.virtual_time(time) > self._end

    def next_result(self) -> IUEvent:
        if self._current_result < len(self._results):
            r = self._results[self._current_result]
            self._current_result += 1
            return r
        else:
            return None

    def check_result(self, result: IUEvent, event: IUEvent) -> bool:
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
        self._results.clear()
        return

    def load(self, config: OrderedDict):
        self.clear()
        self._start = wash_dt(dt.as_utc(config[CONF_START]))
        self._end = wash_dt(dt.as_utc(config[CONF_END]))
        self._name = config.get(CONF_NAME, None)
        if CONF_RESULTS in config:
            for r in config[CONF_RESULTS]:
                self._results.append(IUEvent().load(r))
        return self

    def begin(self, time: datetime) -> None:
        self._delta = time - self._start
        self._perf_mon = tm.perf_counter()
        self._current_result = 0
        self._events = 0
        self._checks = 0
        self._errors = 0
        self._test_time = 0
        return

    def end(self) -> None:
        self._test_time = tm.perf_counter() - self._perf_mon
        return

    def virtual_time(self, time: datetime) -> datetime:
        """Return the virtual clock. For testing we can speed
        up time. This routine will return a virtual time based
        on the real time and the duration from start. It is in
        effect a test warp speed"""
        vt: datetime = time - self._delta
        actual_duration: float = (vt - self._start).total_seconds()
        virtual_duration: float = actual_duration * self._speed
        return self._start + timedelta(seconds=virtual_duration)


class IUTester:
    """Irrigation Unlimited testing class"""

    def __init__(self) -> None:
        self._tests: list[IUTest] = []
        self.load(None)
        return

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def speed(self) -> float:
        return self._speed

    @property
    def is_testing(self) -> bool:
        return self._is_testing()

    @property
    def tests(self) -> "list[IUTest]":
        return self._tests

    @property
    def current_test(self) -> IUTest:
        if self._running_test is not None and self._running_test < len(self._tests):
            return self._tests[self._running_test]
        else:
            return None

    @property
    def last_test(self) -> IUTest:
        if self._last_test is not None and self._last_test < len(self._tests):
            return self._tests[self._last_test]
        else:
            return None

    @property
    def total_events(self) -> int:
        result: int = 0
        for test in self._tests:
            result += test.events
        return result

    @property
    def total_checks(self) -> int:
        result: int = 0
        for test in self._tests:
            result += test.checks
        return result

    @property
    def total_errors(self) -> int:
        result: int = 0
        for test in self._tests:
            result += test.errors
        return result

    @property
    def total_time(self) -> float:
        result: float = 0
        for test in self._tests:
            result += test.test_time
        return result

    @property
    def total_tests(self) -> int:
        return len(self._tests)

    @property
    def total_virtual_duration(self) -> timedelta:
        result = timedelta(0)
        for test in self._tests:
            result += test.virtual_duration
        return result

    @property
    def total_results(self) -> int:
        result: int = 0
        for test in self._tests:
            result += test.total_results
        return result

    def start_test(self, test_no: int, time: datetime) -> IUTest:
        if test_no > 0 and test_no <= len(self._tests):
            self._running_test = test_no - 1  # 0-based
            ct = self._tests[self._running_test]
            ct.begin(time)
            if self._show_log:
                _LOGGER.info(
                    "Running test %d from %s to %s",
                    self._running_test + 1,
                    dt.as_local(ct._start).strftime("%c"),
                    dt.as_local(ct._end).strftime("%c"),
                )
            self._test_initialised = False
        else:
            self._running_test = None
        return self.current_test

    def end_test(self, time: datetime) -> None:
        ct = self.current_test
        if ct is not None:
            ct.end()
            if self._show_log:
                _LOGGER.info("Test %d completed", self._running_test + 1)
        self._last_test = self._running_test
        self._running_test = None
        return

    def next_test(self, time: datetime) -> IUTest:
        current = self._running_test  # This is 0-based
        self.end_test(time)
        return self.start_test(current + 2, time)  # This takes 1-based

    def _is_testing(self) -> bool:
        return self._enabled and self._running_test is not None

    def clear(self) -> None:
        # Private variables
        self._tests.clear()
        self._test_initialised = False
        self._running_test: int = None
        self._last_test: int = None
        self._autoplay_initialised: bool = False
        return

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
            for ti, test in enumerate(config[CONF_TIMES]):
                self._tests.append(IUTest(ti, self._speed).load(test))
        return self

    def poll_test(self, time: datetime, poll_func) -> None:
        if self._autoplay and not self._autoplay_initialised:
            self.start_test(1, time)
            self._autoplay_initialised = True

        ct = self.current_test
        if ct is not None:
            if not self._test_initialised:
                poll_func(ct._start, True)
                self._test_initialised = True
            elif ct.is_finished(time):  # End of current test
                if self._autoplay:
                    ct = self.next_test(time)
                    if ct is not None:
                        poll_func(ct.start, True)
                    else:  # All tests finished
                        if self._show_log:
                            _LOGGER.info(
                                "All tests completed (Idle); checks: %d, errors: %d",
                                self.total_checks,
                                self.total_errors,
                            )
                        poll_func(time, True)
                else:  # End single test
                    self.end_test(time)
                    poll_func(time, True)
            else:  # Continue existing test
                poll_func(ct.virtual_time(time))
        else:  # Out of tests to run
            poll_func(time)
        return

    def entity_state_changed(self, event: IUEvent) -> None:
        """Called when an entity has changed state"""

        def check_state(event: IUEvent):
            """Check the event against the next result"""
            ct = self.current_test
            if ct is not None:
                r = ct.next_result()
                if not ct.check_result(r, event):
                    if self._show_log:
                        _LOGGER.error(
                            "(%d) Event <> result %s <> %s",
                            ct.current_result,
                            event.as_str(),
                            r.as_str() if r is not None else "None",
                        )

        if self._show_log:
            event.write_log()
        if self._is_testing():
            if self._output_events:
                print(event.as_str())
            check_state(event)
        return


class IUCoordinator:
    """Irrigation Unimited Coordinator class"""

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
        self._remove_listener: CALLBACK_TYPE = None
        self._tester = IUTester()
        return

    @property
    def controllers(self) -> "list[IUController]":
        return self._controllers

    @property
    def tester(self) -> IUTester:
        return self._tester

    @property
    def is_setup(self) -> bool:
        return self._is_setup()

    @property
    def component(self) -> Entity:
        return self._component

    @property
    def refresh_interval(self) -> timedelta:
        return self._refresh_interval

    def _is_setup(self) -> bool:
        """Wait for sensors to be setup"""
        all_setup: bool = self._hass.is_running and self._component is not None
        for controller in self._controllers:
            all_setup = all_setup and controller.is_setup
        return all_setup

    def add(self, controller: IUController) -> IUController:
        """Add a new controller to the system"""
        self._controllers.append(controller)
        return controller

    def find_add(self, coordinator: "IUCoordinator", index: int) -> IUController:
        if index >= len(self._controllers):
            return self.add(IUController(self._hass, coordinator, index))
        else:
            return self._controllers[index]

    def clear(self) -> None:
        # Don't clear controllers
        # self._controllers.clear()
        self._is_on: bool = False
        return

    def load(self, config: OrderedDict) -> "IUCoordinator":
        """Load config data for the system"""
        self.clear()

        global SYSTEM_GRANULARITY
        SYSTEM_GRANULARITY = config.get(CONF_GRANULARITY, DEFAULT_GRANULATITY)
        self._refresh_interval = timedelta(
            seconds=config.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL)
        )

        for ci, controller_config in enumerate(config[CONF_CONTROLLERS]):
            self.find_add(self, ci).load(controller_config)

        self._tester = IUTester().load(config.get(CONF_TESTING))

        self._dirty = True
        self._muster_required = True
        return self

    def as_dict(self) -> OrderedDict:
        dict = OrderedDict()
        dict[CONF_CONTROLLERS] = []
        for controller in self._controllers:
            dict[CONF_CONTROLLERS].append(controller.as_dict())
        return dict

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

    def request_update(self) -> None:
        """Flag the sensor needs an update. The actual update is done
        in update_sensor"""
        self._sensor_update_required = True
        return

    def update_sensor(self, time: datetime) -> None:
        """Update home assistant sensors if required"""
        for controller in self._controllers:
            controller.update_sensor(time)

        if self._component is not None and self._sensor_update_required:
            self._component.schedule_update_ha_state()
            self._sensor_update_required = False
            self._sensor_last_update = time
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

    def poll_main(self, time: datetime, force: bool = False) -> None:
        if self._tester.enabled:
            self._tester.poll_test(time, self.poll)
        else:
            self.poll(time, force)
        return

    def timer(self, time: datetime) -> None:
        self._last_tick = time
        if self._initialised:
            self.poll_main(time)
        else:
            self._initialised = self.is_setup
            if self._initialised:
                self.request_update()
                self.poll_main(time)
        return

    async def _async_timer(self, time: datetime) -> None:
        """Timer callback"""
        self.timer(time)
        return

    def track_interval(self) -> timedelta:
        track_time = SYSTEM_GRANULARITY / self._tester.speed
        track_time *= 0.95  # Run clock slightly ahead of required to avoid skipping
        return min(timedelta(seconds=track_time), self._refresh_interval)

    def start(self) -> None:
        """Start the system up"""
        self.stop()
        self._remove_listener = async_track_time_interval(
            self._hass, self._async_timer, self.track_interval()
        )
        return

    def stop(self) -> None:
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None
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

    def service_time(self) -> datetime:
        """Return a time midway between last and next future tick"""
        if self._last_tick is not None:
            time = self._last_tick + self.track_interval() / 2
        else:
            time = dt.utcnow()
        if self._tester.is_testing:
            time = self._tester.current_test.virtual_time(time)
        return wash_dt(time)

    def service_call(
        self,
        service: str,
        controller: IUController,
        zone: IUZone,
        data: MappingProxyType,
    ) -> None:
        """Entry point for all service calls."""
        time = self.service_time()

        if service == SERVICE_ENABLE:
            if zone is not None:
                zone.enabled = True
                controller.clear_sequence_runs(time)
            else:
                controller.enabled = True
        elif service == SERVICE_DISABLE:
            if zone is not None:
                zone.enabled = False
                controller.clear_sequence_runs(time)
            else:
                controller.enabled = False
        elif service == SERVICE_TOGGLE:
            if zone is not None:
                zone.enabled = not zone.enabled
                controller.clear_sequence_runs(time)
            else:
                controller.enabled = not controller.enabled
        elif service == SERVICE_CANCEL:
            if zone is not None:
                zone.service_cancel(data, time)
            else:
                controller.service_cancel(data, time)
        elif service == SERVICE_TIME_ADJUST:
            if zone is not None:
                zone.service_adjust_time(data, time)
            else:
                controller.service_adjust_time(data, time)
        elif service == SERVICE_MANUAL_RUN:
            if zone is not None:
                zone.service_manual_run(data, time)
            else:
                controller.service_manual_run(data, time)
        else:
            return
        self._muster_required = True
        return

    def start_test(self, test_no: int) -> datetime:
        self._last_tick = None
        next_time = dt.utcnow()
        self._tester.start_test(test_no, next_time)
        self.timer(next_time)
        return next_time

    def status_changed(
        self, time: datetime, controller: IUController, zone: IUZone, state: bool
    ) -> None:
        crumbs: str = ""
        if zone is not None:
            zone_id = zone.index + 1
            if state == True:
                crumbs = zone.runs.current_run.crumbs
        else:
            zone_id = 0
        e = IUEvent().load2(time, controller.index + 1, zone_id, state, crumbs)
        self._tester.entity_state_changed(e)
        return
