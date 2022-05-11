"""Test irrigation_unlimited history."""
from unittest.mock import patch
from datetime import datetime, timedelta
from typing import OrderedDict, List, Any
import pytest
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_DISABLE,
)
from tests.iu_test_support import (
    IUExam,
)
from logging import WARNING, Logger, getLogger, INFO, DEBUG, ERROR

IUExam.quiet_mode()

# pylint: disable=unused-argument
# pylint: disable=too-many-arguments
def hist_data(
    hass,
    start_time: datetime,
    end_time: datetime,
    entity_ids: List[str],
    filters: Any = None,
    include_start_time_state: bool = True,
    significant_changes_only: bool = True,
    minimal_response: bool = False,
    no_attributes: bool = False,
) -> dict:
    """Return dummy history data"""

    def s2dt(adate: str) -> datetime:
        return datetime.fromisoformat(adate + "+00:00")

    _LOGGER: Logger = getLogger(__package__)
    _LOGGER.log(
        DEBUG, f"=========start_time: {start_time}, end_time: {end_time}=========="
    )

    result = {}
    idx = "binary_sensor.irrigation_unlimited_c1_z1"
    if idx in entity_ids:
        result[idx] = []
        if start_time >= s2dt("2020-12-28 00:00:00") and end_time <= s2dt(
            "2021-01-04 23:59:59"
        ):
            result[idx].append(ha.State(idx, "on", None, s2dt("2021-01-04T04:30:00")))
            result[idx].append(ha.State(idx, "off", None, s2dt("2021-01-04T04:32:00")))
            result[idx].append(ha.State(idx, "on", None, s2dt("2021-01-04T05:30:00")))
            result[idx].append(ha.State(idx, "off", None, s2dt("2021-01-04T05:32:00")))
    idx = "binary_sensor.irrigation_unlimited_c1_z2"
    if idx in entity_ids:
        result[idx] = []
        if start_time >= s2dt("2020-12-28 00:00:00") and end_time <= s2dt(
            "2021-01-04 23:59:59"
        ):
            result[idx].append(ha.State(idx, "on", None, s2dt("2021-01-04T04:35:00")))
            result[idx].append(ha.State(idx, "off", None, s2dt("2021-01-04T04:38:00")))
            result[idx].append(ha.State(idx, "on", None, s2dt("2021-01-04T05:35:00")))
            result[idx].append(ha.State(idx, "off", None, s2dt("2021-01-04T05:38:00")))
            result[idx].append(ha.State(idx, "on", None, s2dt("2021-01-04T05:40:00")))
            result[idx].append(ha.State(idx, "off", None, s2dt("2021-01-04T05:45:00")))
    return result


async def test_history(hass: ha.HomeAssistant):
    """Test out the history caching and timeline"""
    # pylint: disable=redefined-outer-name

    def mk_dt(date: str) -> datetime:
        return datetime.strptime(date + "+0000", "%Y-%m-%d %H:%M%z")

    async with IUExam(hass, "test_history.yaml") as exam:
        await exam.load_dependencies()

        with patch(
            "homeassistant.components.recorder.history.get_significant_states"
        ) as mock:
            mock.side_effect = hist_data

            await exam.begin_test(1)
            await exam.run_for(timedelta(seconds=60))

            state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
            assert state.attributes["today_total"] == 4.0
            timeline = [
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-06 06:05")),
                        ("end", mk_dt("2021-01-06 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-05 06:05")),
                        ("end", mk_dt("2021-01-05 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-04 06:05")),
                        ("end", mk_dt("2021-01-04 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-04 05:30")),
                        ("end", mk_dt("2021-01-04 05:32")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-04 04:30")),
                        ("end", mk_dt("2021-01-04 04:32")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
            ]
            assert state.attributes["timeline"] == timeline

            state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
            assert state.attributes["today_total"] == 11.0

            timeline = [
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-06 06:10")),
                        ("end", mk_dt("2021-01-06 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-05 06:10")),
                        ("end", mk_dt("2021-01-05 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-04 06:10")),
                        ("end", mk_dt("2021-01-04 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-04 05:40")),
                        ("end", mk_dt("2021-01-04 05:45")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-04 05:35")),
                        ("end", mk_dt("2021-01-04 05:38")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-04 04:35")),
                        ("end", mk_dt("2021-01-04 04:38")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
            ]
            assert state.attributes["timeline"] == timeline

            await exam.finish_test()

            # Midnight rollover
            await exam.begin_test(2)
            await exam.run_for(timedelta(seconds=60))

            state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
            assert state.attributes["today_total"] == 4.0

            timeline = [
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-07 06:05")),
                        ("end", mk_dt("2021-01-07 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-06 06:05")),
                        ("end", mk_dt("2021-01-06 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-05 06:05")),
                        ("end", mk_dt("2021-01-05 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-04 05:30")),
                        ("end", mk_dt("2021-01-04 05:32")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-04 04:30")),
                        ("end", mk_dt("2021-01-04 04:32")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
            ]
            assert state.attributes["timeline"] == timeline

            state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
            assert state.attributes["today_total"] == 11.0

            timeline = [
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-07 06:10")),
                        ("end", mk_dt("2021-01-07 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-06 06:10")),
                        ("end", mk_dt("2021-01-06 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-05 06:10")),
                        ("end", mk_dt("2021-01-05 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-04 05:40")),
                        ("end", mk_dt("2021-01-04 05:45")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-04 05:35")),
                        ("end", mk_dt("2021-01-04 05:38")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-04 04:35")),
                        ("end", mk_dt("2021-01-04 04:38")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
            ]
            assert state.attributes["timeline"] == timeline

            await exam.run_until(datetime.fromisoformat("2021-01-05T00:00:30+00:00"))

            state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
            assert state.attributes["today_total"] == 0.0

            timeline = [
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-07 06:05")),
                        ("end", mk_dt("2021-01-07 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-06 06:05")),
                        ("end", mk_dt("2021-01-06 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-05 06:05")),
                        ("end", mk_dt("2021-01-05 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
            ]
            assert state.attributes["timeline"] == timeline

            state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
            assert state.attributes["today_total"] == 0.0

            timeline = [
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-07 06:10")),
                        ("end", mk_dt("2021-01-07 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-06 06:10")),
                        ("end", mk_dt("2021-01-06 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_dt("2021-01-05 06:10")),
                        ("end", mk_dt("2021-01-05 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
            ]
            assert state.attributes["timeline"] == timeline

            await exam.finish_test()
            exam.check_summary()


async def test_history_disabled(hass: ha.HomeAssistant):
    """Test out the history caching and timeline when disabled"""
    # pylint: disable=redefined-outer-name
    # pylint: disable=protected-access

    async with IUExam(hass, "test_history_disabled.yaml") as exam:

        await exam.load_dependencies()

        with patch(
            "homeassistant.components.recorder.history.get_significant_states"
        ) as mock:
            mock.side_effect = hist_data

            # Check values read from config
            assert exam.coordinator.history._history_span == timedelta(days=5)
            assert exam.coordinator.history._refresh_interval == timedelta(seconds=60)

            await exam.begin_test(1)
            await exam.call(
                SERVICE_DISABLE,
                {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                },
            )
            await exam.run_for(timedelta(seconds=60))

            # Check there is no history
            state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
            assert state.attributes["today_total"] == 0.0
            assert state.attributes["timeline"] == []

            await exam.finish_test()
            exam.check_summary()
