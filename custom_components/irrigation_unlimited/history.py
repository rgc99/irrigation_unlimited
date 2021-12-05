"""History access and caching"""
from datetime import datetime, timedelta
from typing import OrderedDict, List
import homeassistant.util.dt as dt
from homeassistant.components.recorder import history
from homeassistant.const import STATE_ON

from .const import (
    ATTR_CURRENT_ADJUSTMENT,
    ATTR_CURRENT_NAME,
    CONF_HISTORY_REFRESH,
    CONF_HISTORY_SPAN,
    TIMELINE_ADJUSTMENT,
    TIMELINE_SCHEDULE_NAME,
    TIMELINE_START,
    TIMELINE_END,
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
    return timedelta(seconds=round(duration.total_seconds()))


class IUHistory:
    """History access and caching"""

    def __init__(self, hass):
        self._hass = hass
        # Configuration variables
        self._history_span: timedelta = None
        self._history_refresh: timedelta = None
        # Private variables
        self._history_last: datetime = None
        self._cache = {}

    def _clear_cache(self) -> None:
        self._cache = {}

    def _today_duration(self, stime: datetime, data: list) -> timedelta:
        """Return the total on time"""
        # pylint: disable=no-self-use
        elapsed = timedelta(0)
        front_marker: dict = None
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

    def _run_history(self, stime: datetime, data: list) -> list:
        """Return the on/off series"""
        # pylint: disable=no-self-use

        def create_record(item: dict, end: datetime) -> dict:
            result = OrderedDict()
            result[TIMELINE_START] = round_seconds_dt(item.last_changed)
            result[TIMELINE_END] = round_seconds_dt(end)
            result[TIMELINE_SCHEDULE_NAME] = item.attributes.get(ATTR_CURRENT_NAME)
            result[TIMELINE_ADJUSTMENT] = item.attributes.get(ATTR_CURRENT_ADJUSTMENT)
            return result

        run_history = []
        front_marker: dict = None

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

    def load(self, config: OrderedDict) -> "IUHistory":
        """Load config data"""
        if config is None:
            config = {}
        self._history_span = timedelta(days=config.get(CONF_HISTORY_SPAN, 7))
        self._history_refresh = timedelta(seconds=config.get(CONF_HISTORY_REFRESH, 120))
        return self

    def muster(self, stime: datetime, entity_ids: List[str], force: bool) -> None:
        """Check and update history as required"""
        if not (
            force
            or self._history_last is None
            or stime - self._history_last >= self._history_refresh
            or dt.as_local(self._history_last).toordinal()
            != dt.as_local(stime).toordinal()
        ):
            return

        self._clear_cache()
        start = stime - self._history_span
        data = history.get_significant_states(
            self._hass,
            start_time=start,
            end_time=stime,
            entity_ids=entity_ids,
            significant_changes_only=False,
        )
        self._history_last = stime
        if data is None or len(data) == 0:
            return

        for entity_id in data:
            self._cache[entity_id] = {}
            self._cache[entity_id][TIMELINE] = self._run_history(stime, data[entity_id])
            self._cache[entity_id][TODAY_ON] = self._today_duration(
                stime, data[entity_id]
            )
        return

    def today_total(self, entity_id: str) -> timedelta:
        """Return the total on time for today"""
        if entity_id in self._cache:
            return self._cache[entity_id][TODAY_ON]
        return timedelta(0)

    def timeline(self, entity_id: str) -> list:
        """Return the timeline history"""
        if entity_id in self._cache:
            return self._cache[entity_id][TIMELINE].copy()
        return []
