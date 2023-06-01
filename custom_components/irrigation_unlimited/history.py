"""History access and caching. This module runs asynchronously collecting
and caching history data"""
from datetime import datetime, timedelta
from typing import Callable, OrderedDict, Any
from homeassistant.core import HomeAssistant, State, CALLBACK_TYPE
from homeassistant.util import dt
from homeassistant.components.recorder.const import DATA_INSTANCE as RECORDER_INSTANCE
from homeassistant.components.recorder import get_instance
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
)
from homeassistant.components.recorder import history
from homeassistant.const import STATE_ON

from .const import (
    ATTR_CURRENT_ADJUSTMENT,
    ATTR_CURRENT_NAME,
    CONF_ENABLED,
    CONF_HISTORY,
    CONF_HISTORY_REFRESH,
    CONF_HISTORY_SPAN,
    CONF_REFRESH_INTERVAL,
    CONF_SPAN,
    TIMELINE_ADJUSTMENT,
    TIMELINE_SCHEDULE_NAME,
    TIMELINE_START,
    TIMELINE_END,
    DOMAIN,
    BINARY_SENSOR,
)

TIMELINE = "timeline"
TODAY_ON = "today_on"


def midnight(utc: datetime) -> datetime:
    """Accept a UTC time and return midnight for that day"""
    return dt.as_utc(
        dt.as_local(utc).replace(hour=0, minute=0, second=0, microsecond=0)
    )


def round_seconds_dt(atime: datetime) -> datetime:
    """Round the time to the nearest second"""
    return (atime + timedelta(seconds=0.5)).replace(microsecond=0)


def round_seconds_td(duration: timedelta) -> timedelta:
    """Round the timedelta to the nearest second"""
    return timedelta(seconds=int(duration.total_seconds() + 0.5))


class IUHistory:
    """History access and caching"""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, hass: HomeAssistant, callback: Callable[[set[str]], None]):
        self._hass = hass
        self._callback = callback
        # Configuration variables
        self._history_span = timedelta(days=7)
        self._refresh_interval = timedelta(seconds=120)
        self._enabled = True
        # Private variables
        self._history_last: datetime = None
        self._cache: dict[str, Any] = {}
        self._entity_ids: list[str] = []
        self._refresh_remove: CALLBACK_TYPE = None
        self._stime: datetime = None
        self._initialised = False
        self._fixed_clock = True

    def __del__(self):
        self._remove_refresh()

    def _remove_refresh(self) -> None:
        """Remove the scheduled refresh"""
        if self._refresh_remove is not None:
            self._refresh_remove()
            self._refresh_remove = None

    def _get_next_refresh_event(self, utc_time: datetime, force: bool) -> datetime:
        """Calculate the next event time."""
        if self._history_last is None or force or not self._fixed_clock:
            return utc_time
        return utc_time + self._refresh_interval

    def _schedule_refresh(self, force: bool) -> None:
        """Set up a listener for the next history refresh."""
        self._remove_refresh()
        self._history_last = self._get_next_refresh_event(dt.utcnow(), force)
        self._refresh_remove = async_track_point_in_utc_time(
            self._hass,
            self._async_handle_refresh_event,
            self._history_last,
        )

    async def _async_handle_refresh_event(self, utc_time: datetime) -> None:
        """Handle history event."""
        # pylint: disable=unused-argument
        self._refresh_remove = None
        if self._fixed_clock:
            self._schedule_refresh(False)
        await self._async_update_history(self._stime)

    def _initialise(self) -> bool:
        """Initialise this unit"""
        if self._initialised:
            return False

        self._remove_refresh()
        self._history_last = None
        self._stime = None
        self._clear_cache()
        self._entity_ids.clear()
        for entity_id in self._hass.states.async_entity_ids():
            if entity_id.startswith(f"{BINARY_SENSOR}.{DOMAIN}_"):
                self._entity_ids.append(entity_id)
        self._initialised = True
        return True

    def finalise(self):
        """Finalise this unit"""
        self._remove_refresh()

    def _clear_cache(self) -> None:
        self._cache = {}

    def _today_duration(self, stime: datetime, data: list[State]) -> timedelta:
        """Return the total on time"""
        # pylint: disable=no-self-use

        elapsed = timedelta(0)
        front_marker: State = None
        start = midnight(stime)

        for item in data:
            # Filter data
            if item.last_changed < start:
                continue
            if item.last_changed > stime:
                break

            # Look for an on state
            if front_marker is None:
                if item.state == STATE_ON:
                    front_marker = item
                continue

            # Now look for an off state
            if item.state != STATE_ON:
                elapsed += item.last_changed - front_marker.last_changed
                front_marker = None

        if front_marker is not None:
            elapsed += stime - front_marker.last_changed

        return timedelta(seconds=round(elapsed.total_seconds()))

    def _run_history(self, stime: datetime, data: list[State]) -> list:
        """Return the on/off series"""
        # pylint: disable=no-self-use

        def create_record(item: State, end: datetime) -> dict:
            result = OrderedDict()
            result[TIMELINE_START] = round_seconds_dt(item.last_changed)
            result[TIMELINE_END] = round_seconds_dt(end)
            result[TIMELINE_SCHEDULE_NAME] = item.attributes.get(ATTR_CURRENT_NAME)
            result[TIMELINE_ADJUSTMENT] = item.attributes.get(
                ATTR_CURRENT_ADJUSTMENT, ""
            )
            return result

        run_history = []
        front_marker: State = None

        for item in data:
            # Look for an on state
            if front_marker is None:
                if item.state == STATE_ON:
                    front_marker = item
                continue

            # Now look for an off state
            if item.state != STATE_ON:
                run_history.append(create_record(front_marker, item.last_changed))
                front_marker = None

        if front_marker is not None:
            run_history.append(create_record(front_marker, stime))

        return run_history

    async def _async_update_history(self, stime: datetime) -> None:
        if len(self._entity_ids) == 0:
            return

        start = self._stime - self._history_span
        if RECORDER_INSTANCE in self._hass.data:
            data = await get_instance(self._hass).async_add_executor_job(
                history.get_significant_states,
                self._hass,
                start,
                stime,
                self._entity_ids,
                None,
                True,
                False,
            )
        else:
            data = {}

        if data is None or len(data) == 0:
            return

        entity_ids: set[str] = set()
        for entity_id in data:
            new_run_history = self._run_history(stime, data[entity_id])
            new_today_on = self._today_duration(stime, data[entity_id])
            if entity_id not in self._cache:
                self._cache[entity_id] = {}
            elif (
                new_today_on == self._cache[entity_id][TODAY_ON]
                and new_run_history == self._cache[entity_id][TIMELINE]
            ):
                continue
            self._cache[entity_id][TIMELINE] = new_run_history
            self._cache[entity_id][TODAY_ON] = new_today_on
            entity_ids.add(entity_id)
        if len(entity_ids) > 0:
            self._callback(entity_ids)

    def load(self, config: OrderedDict, fixed_clock: bool) -> "IUHistory":
        """Load config data"""
        if config is None:
            config = {}
        self._fixed_clock = fixed_clock

        span_days: int = None
        refresh_seconds: int = None

        # deprecated
        span_days = config.get(CONF_HISTORY_SPAN)
        refresh_seconds = config.get(CONF_HISTORY_REFRESH)

        if CONF_HISTORY in config:
            hist_conf: dict = config[CONF_HISTORY]
            self._enabled = hist_conf.get(CONF_ENABLED, self._enabled)
            span_days = hist_conf.get(CONF_SPAN, span_days)
            refresh_seconds = hist_conf.get(CONF_REFRESH_INTERVAL, refresh_seconds)

        if span_days is not None:
            self._history_span = timedelta(days=span_days)
        if refresh_seconds is not None:
            self._refresh_interval = timedelta(seconds=refresh_seconds)

        self._initialised = False
        return self

    def muster(self, stime: datetime, force: bool) -> int:
        """Check and update history if required"""

        if force:
            self._initialised = False

        if not self._initialised:
            self._initialise()

        if self._enabled and (
            force
            or self._stime is None
            or dt.as_local(self._stime).toordinal() != dt.as_local(stime).toordinal()
            or not self._fixed_clock
        ):
            self._schedule_refresh(True)

        self._stime = stime
        return 0

    def today_total(self, entity_id: str) -> timedelta:
        """Return the total on time for today"""
        if entity_id in self._cache:
            return self._cache[entity_id][TODAY_ON]
        return timedelta(0)

    def timeline(self, entity_id: str) -> list[dict]:
        """Return the timeline history"""
        if entity_id in self._cache:
            return self._cache[entity_id][TIMELINE].copy()
        return []
