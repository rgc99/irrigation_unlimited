"""Test irrigation_unlimited history."""

from unittest.mock import patch
from datetime import datetime, timedelta
from collections import Counter
from typing import OrderedDict, List, Any, NamedTuple
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
)
import homeassistant.core as ha
from homeassistant.util import dt
from custom_components.irrigation_unlimited.const import (
    SERVICE_DISABLE,
    SERVICE_MANUAL_RUN,
)
from custom_components.irrigation_unlimited.history import (
    midnight,
    round_seconds_dt,
    round_seconds_td,
)
from tests.iu_test_support import (
    IUExam,
    mk_utc,
    mk_local,
)

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
) -> dict[str, list[ha.State]]:
    """Return dummy history data for a scheduled run"""

    result: dict[str, list[ha.State]] = {}
    idm = "binary_sensor.irrigation_unlimited_c1_m"
    idz1 = "binary_sensor.irrigation_unlimited_c1_z1"
    idz2 = "binary_sensor.irrigation_unlimited_c1_z2"
    ats1 = {"current_schedule": 1, "current_name": "Schedule 1"}
    atm = {"current_schedule": 0, "current_name": "Manual"}

    class Event(NamedTuple):
        atime: datetime
        entity_id: str

    class State(NamedTuple):
        state: str
        attributes: dict

    data: dict[Event, State] = {
        # test_history_main
        Event(mk_utc("2021-01-04 04:29:00"), idm): State("on", None),
        Event(mk_utc("2021-01-04 04:30:00"), idz1): State("on", None),
        Event(mk_utc("2021-01-04 04:32:00"), idz1): State("off", None),
        Event(mk_utc("2021-01-04 04:33:00"), idm): State("off", None),
        Event(mk_utc("2021-01-04 04:35:00"), idz2): State("on", None),
        Event(mk_utc("2021-01-04 04:38:00"), idz2): State("off", None),
        Event(mk_utc("2021-01-04 05:29:00"), idm): State("on", None),
        Event(mk_utc("2021-01-04 05:30:00"), idz1): State("on", None),
        Event(mk_utc("2021-01-04 05:32:00"), idz1): State("off", None),
        Event(mk_utc("2021-01-04 05:33:00"), idm): State("off", None),
        Event(mk_utc("2021-01-04 05:35:00"), idz2): State("on", None),
        Event(mk_utc("2021-01-04 05:38:00"), idz2): State("off", None),
        Event(mk_utc("2021-01-04 05:40:00"), idz2): State("on", None),
        Event(mk_utc("2021-01-04 05:45:00"), idz2): State("off", None),
        # test_history_object
        Event(mk_utc("2021-06-03 04:00:00"), idm): State("off", None),
        Event(mk_utc("2021-06-03 04:00:00"), idz1): State("off", None),
        Event(mk_utc("2021-06-03 04:09:00"), idm): State("on", None),
        Event(mk_utc("2021-06-03 04:10:00"), idz1): State("on", None),
        Event(mk_utc("2021-06-03 04:15:00"), idz1): State("off", None),
        Event(mk_utc("2021-06-03 04:16:00"), idm): State("off", None),
        Event(mk_utc("2021-06-03 04:19:00"), idm): State("on", None),
        Event(mk_utc("2021-06-03 04:20:00"), idz1): State("on", None),
        Event(mk_utc("2021-06-03 04:25:00"), idz1): State("off", None),
        Event(mk_utc("2021-06-03 04:26:00"), idm): State("off", None),
        Event(mk_utc("2021-06-03 04:29:00"), idm): State("on", None),
        Event(mk_utc("2021-06-03 04:30:00"), idz1): State("on", None),
        Event(mk_utc("2021-06-03 04:35:00"), idz1): State("off", None),
        Event(mk_utc("2021-06-03 04:36:00"), idm): State("off", None),
        Event(mk_utc("2021-06-04 04:09:00"), idm): State("on", None),
        Event(mk_utc("2021-06-04 04:10:00"), idz1): State("on", None),
        Event(mk_utc("2021-06-04 04:15:00"), idz1): State("off", None),
        Event(mk_utc("2021-06-04 04:16:00"), idm): State("off", None),
        Event(mk_utc("2021-06-04 04:19:00"), idm): State("on", None),
        Event(mk_utc("2021-06-04 04:20:00"), idz1): State("on", None),
        Event(mk_utc("2021-06-04 04:25:00"), idz1): State("off", None),
        Event(mk_utc("2021-06-04 04:26:00"), idm): State("off", None),
        Event(mk_utc("2021-06-04 04:29:00"), idm): State("on", None),
        Event(mk_utc("2021-06-04 04:30:00"), idz1): State("on", None),
        Event(mk_utc("2021-06-05 04:09:00"), idm): State("on", None),
        Event(mk_utc("2021-06-05 04:10:00"), idz1): State("on", None),
        # test_history_live - Test 1
        Event(mk_utc("2024-07-16 06:05:00"), idm): State("on", ats1),
        Event(mk_utc("2024-07-16 06:05:00"), idz1): State("on", ats1),
        Event(mk_utc("2024-07-16 06:11:00"), idz1): State("off", None),
        Event(mk_utc("2024-07-16 06:11:00"), idm): State("off", None),
        Event(mk_utc("2024-07-16 06:12:00"), idm): State("on", ats1),
        Event(mk_utc("2024-07-16 06:12:00"), idz2): State("on", ats1),
        Event(mk_utc("2024-07-16 06:24:00"), idz2): State("off", None),
        Event(mk_utc("2024-07-16 06:24:00"), idm): State("off", None),
        # test_history_live - Test 2
        Event(mk_utc("2024-07-23 08:05:00"), idm): State("on", atm),
        Event(mk_utc("2024-07-23 08:05:00"), idz1): State("on", atm),
        Event(mk_utc("2024-07-23 08:11:00"), idz1): State("off", None),
        Event(mk_utc("2024-07-23 08:11:00"), idm): State("off", None),
        Event(mk_utc("2024-07-23 08:12:00"), idm): State("on", atm),
        Event(mk_utc("2024-07-23 08:12:00"), idz2): State("on", atm),
        Event(mk_utc("2024-07-23 08:24:00"), idz2): State("off", None),
        Event(mk_utc("2024-07-23 08:24:00"), idm): State("off", None),
    }

    data = dict(sorted(data.items(), key=lambda x: x[0].atime))
    for event, state in data.items():
        if (
            event.entity_id in entity_ids
            and event.atime >= start_time
            and event.atime <= end_time
        ):
            if event.entity_id not in result:
                result[event.entity_id] = []
            result[event.entity_id].append(
                ha.State(event.entity_id, state.state, state.attributes, event.atime)
            )
    return result


async def test_history_routines():
    """Test out the history misc routines"""
    assert round_seconds_dt(datetime(2021, 1, 4, 12, 10, 10, 499999)) == datetime(
        2021, 1, 4, 12, 10, 10
    )
    assert round_seconds_dt(datetime(2021, 1, 4, 12, 10, 10, 500000)) == datetime(
        2021, 1, 4, 12, 10, 11
    )
    assert round_seconds_td(timedelta(0, 10, 499999)) == timedelta(0, 10)
    assert round_seconds_td(timedelta(0, 10, 500000)) == timedelta(0, 11)
    assert dt.as_local(
        midnight(dt.as_local(datetime(2021, 1, 4, 23, 59, 59, 999999)))
    ) == dt.as_local(datetime(2021, 1, 4))


async def test_history_main(hass: ha.HomeAssistant, allow_memory_db):
    """Test out the history caching and timeline"""
    # pylint: disable=redefined-outer-name

    async with IUExam(hass, "test_history.yaml") as exam:
        await exam.load_dependencies()

        with patch(
            "homeassistant.components.recorder.history.get_significant_states"
        ) as mock:
            mock.side_effect = hist_data

            await exam.begin_test(1)
            await exam.run_for("00:02:00")

            assert mock.call_count == 1
            state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
            assert state.attributes["today_total"] == 4.0
            timeline = [
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-06 06:05")),
                        ("end", mk_utc("2021-01-06 06:15")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-05 06:05")),
                        ("end", mk_utc("2021-01-05 06:15")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 06:05")),
                        ("end", mk_utc("2021-01-04 06:15")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:30")),
                        ("end", mk_utc("2021-01-04 05:32")),
                        ("schedule", None),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 04:30")),
                        ("end", mk_utc("2021-01-04 04:32")),
                        ("schedule", None),
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
                        ("start", mk_utc("2021-01-06 06:10")),
                        ("end", mk_utc("2021-01-06 06:20")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-05 06:10")),
                        ("end", mk_utc("2021-01-05 06:20")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 06:10")),
                        ("end", mk_utc("2021-01-04 06:20")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:40")),
                        ("end", mk_utc("2021-01-04 05:45")),
                        ("schedule", None),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:35")),
                        ("end", mk_utc("2021-01-04 05:38")),
                        ("schedule", None),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 04:35")),
                        ("end", mk_utc("2021-01-04 04:38")),
                        ("schedule", None),
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
            await exam.run_for("00:01:00")

            state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
            assert state.attributes["today_total"] == 4.0

            timeline = [
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-07 06:05")),
                        ("end", mk_utc("2021-01-07 06:15")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-06 06:05")),
                        ("end", mk_utc("2021-01-06 06:15")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-05 06:05")),
                        ("end", mk_utc("2021-01-05 06:15")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:30")),
                        ("end", mk_utc("2021-01-04 05:32")),
                        ("schedule", None),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 04:30")),
                        ("end", mk_utc("2021-01-04 04:32")),
                        ("schedule", None),
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
                        ("start", mk_utc("2021-01-07 06:10")),
                        ("end", mk_utc("2021-01-07 06:20")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-06 06:10")),
                        ("end", mk_utc("2021-01-06 06:20")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-05 06:10")),
                        ("end", mk_utc("2021-01-05 06:20")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:40")),
                        ("end", mk_utc("2021-01-04 05:45")),
                        ("schedule", None),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:35")),
                        ("end", mk_utc("2021-01-04 05:38")),
                        ("schedule", None),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 04:35")),
                        ("end", mk_utc("2021-01-04 04:38")),
                        ("schedule", None),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
            ]
            assert state.attributes["timeline"] == timeline

            await exam.run_until("2021-01-05 00:01:00")
            state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
            assert state.attributes["today_total"] == 0.0

            timeline = [
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-07 06:05")),
                        ("end", mk_utc("2021-01-07 06:15")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-06 06:05")),
                        ("end", mk_utc("2021-01-06 06:15")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-05 06:05")),
                        ("end", mk_utc("2021-01-05 06:15")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:30")),
                        ("end", mk_utc("2021-01-04 05:32")),
                        ("schedule", None),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 04:30")),
                        ("end", mk_utc("2021-01-04 04:32")),
                        ("schedule", None),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
            ]
            assert state.attributes["timeline"] == timeline

            state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
            assert state.attributes["today_total"] == 0.0

            timeline = [
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-07 06:10")),
                        ("end", mk_utc("2021-01-07 06:20")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-06 06:10")),
                        ("end", mk_utc("2021-01-06 06:20")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-05 06:10")),
                        ("end", mk_utc("2021-01-05 06:20")),
                        ("schedule", 1),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:40")),
                        ("end", mk_utc("2021-01-04 05:45")),
                        ("schedule", None),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:35")),
                        ("end", mk_utc("2021-01-04 05:38")),
                        ("schedule", None),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 04:35")),
                        ("end", mk_utc("2021-01-04 04:38")),
                        ("schedule", None),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
            ]
            assert state.attributes["timeline"] == timeline

            await exam.finish_test()
            exam.check_summary()


async def test_history_disabled(hass: ha.HomeAssistant, allow_memory_db):
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
            await exam.run_for("00:01:00")

            # Check there is no history
            assert mock.call_count == 0
            state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
            assert state.attributes["today_total"] == 0.0
            assert state.attributes["timeline"] == []

            await exam.finish_test()
            exam.check_summary()


async def test_history_object(hass: ha.HomeAssistant, allow_memory_db):
    """Test out the IUHistory object"""
    # pylint: disable=redefined-outer-name
    # pylint: disable=protected-access

    entity_updates: list[dict] = []

    def service_history(entity_ids: set[str]) -> None:
        entity_updates.extend(entity_ids)

    async with IUExam(hass, "test_skeleton.yaml") as exam:
        await exam.load_dependencies()

        stime = mk_utc("2021-06-04 04:32:00")
        exam.coordinator.history.load(None, False)
        assert exam.coordinator.history._enabled is True
        exam.coordinator.history.load({"history": {"enabled": False}}, True)
        assert exam.coordinator.history._enabled is False
        exam.coordinator.history.muster(stime, True)
        assert exam.coordinator.history._initialise() is False

        with patch(
            "homeassistant.components.recorder.history.get_significant_states"
        ) as mock:
            mock.side_effect = hist_data

            callback_save = exam.coordinator.history._callback
            exam.coordinator.history._callback = service_history

            try:
                # Load history data into cache
                entity_updates.clear()
                await exam.coordinator.history._async_update_history(stime)
                assert Counter(entity_updates) == Counter(
                    [
                        "binary_sensor.irrigation_unlimited_c1_m",
                        "binary_sensor.irrigation_unlimited_c1_z1",
                    ]
                )

                # Check cache working
                entity_updates.clear()
                await exam.coordinator.history._async_update_history(stime)
                assert not entity_updates

                entity_updates.clear()
                exam.coordinator.history._entity_ids.clear()
                await exam.coordinator.history._async_update_history(stime)
                assert not entity_updates

                # Examine cache contents
                assert exam.coordinator.history._cache == {
                    "binary_sensor.irrigation_unlimited_c1_m": {
                        "timeline": [
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-06-03 04:09")),
                                    ("end", mk_utc("2021-06-03 04:16")),
                                    ("schedule", None),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-06-03 04:19")),
                                    ("end", mk_utc("2021-06-03 04:26")),
                                    ("schedule", None),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-06-03 04:29")),
                                    ("end", mk_utc("2021-06-03 04:36")),
                                    ("schedule", None),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-06-04 04:09")),
                                    ("end", mk_utc("2021-06-04 04:16")),
                                    ("schedule", None),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-06-04 04:19")),
                                    ("end", mk_utc("2021-06-04 04:26")),
                                    ("schedule", None),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                        ],
                        "today_on": timedelta(seconds=1020),
                    },
                    "binary_sensor.irrigation_unlimited_c1_z1": {
                        "timeline": [
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-06-03 04:10")),
                                    ("end", mk_utc("2021-06-03 04:15")),
                                    ("schedule", None),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-06-03 04:20")),
                                    ("end", mk_utc("2021-06-03 04:25")),
                                    ("schedule", None),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-06-03 04:30")),
                                    ("end", mk_utc("2021-06-03 04:35")),
                                    ("schedule", None),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-06-04 04:10")),
                                    ("end", mk_utc("2021-06-04 04:15")),
                                    ("schedule", None),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-06-04 04:20")),
                                    ("end", mk_utc("2021-06-04 04:25")),
                                    ("schedule", None),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                        ],
                        "today_on": timedelta(seconds=720),
                    },
                }
            finally:
                exam.coordinator.history._callback = callback_save


async def test_history_live(hass: ha.HomeAssistant, allow_memory_db):
    """Test out the IUHistory object"""
    async with IUExam(hass, "test_history_live.yaml") as exam:
        await exam.load_dependencies()
        with patch(
            "homeassistant.components.recorder.history.get_significant_states"
        ) as mock:
            mock.side_effect = hist_data
            await exam.begin_test(1)
            exam.check_iu_entity(
                "c1_z1",
                STATE_OFF,
                {
                    "status": "off",
                    "current_schedule": None,
                    "next_schedule": 1,
                    "next_name": "Schedule 1",
                    "next_start": mk_local("2024-07-16 06:05:00"),
                    "next_duration": "0:06:00",
                    "today_total": 0.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-07-18 18:05:00"),
                            "end": mk_local("2024-07-18 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-18 06:05:00"),
                            "end": mk_local("2024-07-18 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 18:05:00"),
                            "end": mk_local("2024-07-17 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 06:05:00"),
                            "end": mk_local("2024-07-17 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-16 18:05:00"),
                            "end": mk_local("2024-07-16 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-16 06:05:00"),
                            "end": mk_local("2024-07-16 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "next",
                        },
                    ],
                },
            )
            exam.check_iu_entity(
                "c1_z2",
                STATE_OFF,
                {
                    "current_schedule": None,
                    "percent_complete": 0,
                    "next_adjustment": "",
                    "next_schedule": 1,
                    "next_name": "Schedule 1",
                    "next_start": mk_local("2024-07-16 06:12:00"),
                    "next_duration": "0:12:00",
                    "today_total": 0.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-07-18 18:12:00"),
                            "end": mk_local("2024-07-18 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-18 06:12:00"),
                            "end": mk_local("2024-07-18 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 18:12:00"),
                            "end": mk_local("2024-07-17 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 06:12:00"),
                            "end": mk_local("2024-07-17 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-16 18:12:00"),
                            "end": mk_local("2024-07-16 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-16 06:12:00"),
                            "end": mk_local("2024-07-16 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "next",
                        },
                    ],
                },
            )

            await exam.run_until("2024-07-16 06:08")
            exam.check_iu_entity(
                "c1_z1",
                STATE_ON,
                {
                    "current_schedule": 1,
                    "current_name": "Schedule 1",
                    "current_start": mk_local("2024-07-16 06:05:00"),
                    "current_duration": "0:06:00",
                    "time_remaining": "0:03:00",
                    "percent_complete": 50,
                    "next_schedule": 2,
                    "next_name": "Schedule 2",
                    "next_start": mk_local("2024-07-16 18:05:00"),
                    "next_duration": "0:06:00",
                    "today_total": 3.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-07-18 18:05:00"),
                            "end": mk_local("2024-07-18 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-18 06:05:00"),
                            "end": mk_local("2024-07-18 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 18:05:00"),
                            "end": mk_local("2024-07-17 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 06:05:00"),
                            "end": mk_local("2024-07-17 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-16 18:05:00"),
                            "end": mk_local("2024-07-16 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "status": "next",
                        },
                        {
                            "start": mk_local("2024-07-16 06:05:00"),
                            "end": mk_local("2024-07-16 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "status": "running",
                        },
                    ],
                },
            )
            exam.check_iu_entity(
                "c1_z2",
                STATE_OFF,
                {
                    "status": "off",
                    "current_schedule": None,
                    "percent_complete": 0,
                    "next_adjustment": "",
                    "next_schedule": 1,
                    "next_name": "Schedule 1",
                    "next_start": mk_local("2024-07-16 06:12:00"),
                    "next_duration": "0:12:00",
                    "today_total": 0.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-07-18 18:12:00"),
                            "end": mk_local("2024-07-18 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-18 06:12:00"),
                            "end": mk_local("2024-07-18 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 18:12:00"),
                            "end": mk_local("2024-07-17 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 06:12:00"),
                            "end": mk_local("2024-07-17 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-16 18:12:00"),
                            "end": mk_local("2024-07-16 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-16 06:12:00"),
                            "end": mk_local("2024-07-16 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "next",
                        },
                    ],
                    "volume": None,
                    "flow_rate": None,
                    "icon": "mdi:valve-closed",
                    "friendly_name": "Zone 2",
                },
            )
            await exam.run_until("2024-07-16 06:18")
            exam.check_iu_entity(
                "c1_z1",
                STATE_OFF,
                {
                    "status": "off",
                    "current_schedule": None,
                    "percent_complete": 0,
                    "next_adjustment": "",
                    "next_schedule": 2,
                    "next_name": "Schedule 2",
                    "next_start": mk_local("2024-07-16 18:05:00"),
                    "next_duration": "0:06:00",
                    "today_total": 6.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-07-18 18:05:00"),
                            "end": mk_local("2024-07-18 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-18 06:05:00"),
                            "end": mk_local("2024-07-18 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 18:05:00"),
                            "end": mk_local("2024-07-17 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 06:05:00"),
                            "end": mk_local("2024-07-17 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-16 18:05:00"),
                            "end": mk_local("2024-07-16 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "next",
                        },
                        {
                            "start": mk_local("2024-07-16 06:05:00"),
                            "end": mk_local("2024-07-16 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-16 06:05:00"),
                            "end": mk_local("2024-07-16 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "history",
                        },
                    ],
                },
            )
            exam.check_iu_entity(
                "c1_z2",
                STATE_ON,
                {
                    "status": "on",
                    "current_schedule": 1,
                    "current_name": "Schedule 1",
                    "current_start": mk_local("2024-07-16 06:12:00"),
                    "current_duration": "0:12:00",
                    "time_remaining": "0:06:00",
                    "percent_complete": 50,
                    "next_schedule": 2,
                    "next_name": "Schedule 2",
                    "next_start": mk_local("2024-07-16 18:12:00"),
                    "next_duration": "0:12:00",
                    "today_total": 6.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-07-18 18:12:00"),
                            "end": mk_local("2024-07-18 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-18 06:12:00"),
                            "end": mk_local("2024-07-18 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 18:12:00"),
                            "end": mk_local("2024-07-17 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 06:12:00"),
                            "end": mk_local("2024-07-17 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-16 18:12:00"),
                            "end": mk_local("2024-07-16 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "next",
                        },
                        {
                            "start": mk_local("2024-07-16 06:12:00"),
                            "end": mk_local("2024-07-16 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "running",
                        },
                    ],
                    "volume": None,
                    "flow_rate": None,
                    "icon": "mdi:valve-open",
                    "friendly_name": "Zone 2",
                },
            )

            await exam.run_until("2024-07-16 06:30")
            exam.check_iu_entity(
                "c1_z1",
                STATE_OFF,
                {
                    "status": "off",
                    "current_schedule": None,
                    "percent_complete": 0,
                    "next_adjustment": "",
                    "next_schedule": 2,
                    "next_name": "Schedule 2",
                    "next_start": mk_local("2024-07-16 18:05:00"),
                    "next_duration": "0:06:00",
                    "today_total": 6.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-07-19 06:05:00"),
                            "end": mk_local("2024-07-19 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-18 18:05:00"),
                            "end": mk_local("2024-07-18 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-18 06:05:00"),
                            "end": mk_local("2024-07-18 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 18:05:00"),
                            "end": mk_local("2024-07-17 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 06:05:00"),
                            "end": mk_local("2024-07-17 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-16 18:05:00"),
                            "end": mk_local("2024-07-16 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "next",
                        },
                        {
                            "start": mk_local("2024-07-16 06:05:00"),
                            "end": mk_local("2024-07-16 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "history",
                        },
                    ],
                },
            )
            exam.check_iu_entity(
                "c1_z2",
                STATE_OFF,
                {
                    "current_schedule": None,
                    "percent_complete": 0,
                    "next_schedule": 2,
                    "next_name": "Schedule 2",
                    "next_start": mk_local("2024-07-16 18:12:00"),
                    "next_duration": "0:12:00",
                    "today_total": 12.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-07-19 06:12:00"),
                            "end": mk_local("2024-07-19 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-18 18:12:00"),
                            "end": mk_local("2024-07-18 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-18 06:12:00"),
                            "end": mk_local("2024-07-18 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 18:12:00"),
                            "end": mk_local("2024-07-17 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-17 06:12:00"),
                            "end": mk_local("2024-07-17 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-16 18:12:00"),
                            "end": mk_local("2024-07-16 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "next",
                        },
                        {
                            "start": mk_local("2024-07-16 06:12:00"),
                            "end": mk_local("2024-07-16 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-16 06:12:00"),
                            "end": mk_local("2024-07-16 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "history",
                        },
                    ],
                },
            )
            await exam.finish_test()

            await exam.begin_test(2)
            exam.check_iu_entity(
                "c1_z1",
                STATE_OFF,
                {
                    "current_schedule": None,
                    "percent_complete": 0,
                    "next_adjustment": "",
                    "next_schedule": 2,
                    "next_name": "Schedule 2",
                    "next_start": mk_local("2024-07-23 18:05:00"),
                    "next_duration": "0:06:00",
                    "today_total": 0.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-07-26 06:05:00"),
                            "end": mk_local("2024-07-26 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-25 18:05:00"),
                            "end": mk_local("2024-07-25 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-25 06:05:00"),
                            "end": mk_local("2024-07-25 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-24 18:05:00"),
                            "end": mk_local("2024-07-24 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-24 06:05:00"),
                            "end": mk_local("2024-07-24 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-23 18:05:00"),
                            "end": mk_local("2024-07-23 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "next",
                        },
                    ],
                },
            )
            exam.check_iu_entity(
                "c1_z2",
                STATE_OFF,
                {
                    "current_schedule": None,
                    "percent_complete": 0,
                    "next_adjustment": "",
                    "next_schedule": 2,
                    "next_name": "Schedule 2",
                    "next_start": mk_local("2024-07-23 18:12:00"),
                    "next_duration": "0:12:00",
                    "today_total": 0.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-07-26 06:12:00"),
                            "end": mk_local("2024-07-26 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-25 18:12:00"),
                            "end": mk_local("2024-07-25 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-25 06:12:00"),
                            "end": mk_local("2024-07-25 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-24 18:12:00"),
                            "end": mk_local("2024-07-24 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-24 06:12:00"),
                            "end": mk_local("2024-07-24 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-23 18:12:00"),
                            "end": mk_local("2024-07-23 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "next",
                        },
                    ],
                },
            )
            await exam.run_until("2024-07-23 08:05")
            await exam.call(
                SERVICE_MANUAL_RUN,
                {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                    "time": "00:19",
                },
            )
            await exam.run_until("2024-07-23 08:30")
            exam.check_iu_entity(
                "c1_z1",
                STATE_OFF,
                {
                    "current_schedule": None,
                    "percent_complete": 0,
                    "next_adjustment": "",
                    "next_schedule": 2,
                    "next_name": "Schedule 2",
                    "next_start": mk_local("2024-07-23 18:05:00"),
                    "next_duration": "0:06:00",
                    "today_total": 6.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-07-26 06:05:00"),
                            "end": mk_local("2024-07-26 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-25 18:05:00"),
                            "end": mk_local("2024-07-25 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-25 06:05:00"),
                            "end": mk_local("2024-07-25 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-24 18:05:00"),
                            "end": mk_local("2024-07-24 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-24 06:05:00"),
                            "end": mk_local("2024-07-24 06:11:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-23 18:05:00"),
                            "end": mk_local("2024-07-23 18:11:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "next",
                        },
                        {
                            "start": mk_local("2024-07-23 08:05:00"),
                            "end": mk_local("2024-07-23 08:11:00"),
                            "schedule": 0,
                            "schedule_name": "Manual",
                            "adjustment": "",
                            "status": "history",
                        },
                    ],
                },
            )
            exam.check_iu_entity(
                "c1_z2",
                STATE_OFF,
                {
                    "current_schedule": None,
                    "percent_complete": 0,
                    "next_adjustment": "",
                    "next_schedule": 2,
                    "next_name": "Schedule 2",
                    "next_start": mk_local("2024-07-23 18:12:00"),
                    "next_duration": "0:12:00",
                    "today_total": 12.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-07-26 06:12:00"),
                            "end": mk_local("2024-07-26 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-25 18:12:00"),
                            "end": mk_local("2024-07-25 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-25 06:12:00"),
                            "end": mk_local("2024-07-25 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-24 18:12:00"),
                            "end": mk_local("2024-07-24 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-24 06:12:00"),
                            "end": mk_local("2024-07-24 06:24:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-23 18:12:00"),
                            "end": mk_local("2024-07-23 18:24:00"),
                            "schedule": 2,
                            "schedule_name": "Schedule 2",
                            "adjustment": "",
                            "status": "next",
                        },
                        {
                            "start": mk_local("2024-07-23 08:12:01"),
                            "end": mk_local("2024-07-23 08:24:01"),
                            "schedule": 0,
                            "schedule_name": "Manual",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-07-23 08:12:00"),
                            "end": mk_local("2024-07-23 08:24:00"),
                            "schedule": 0,
                            "schedule_name": "Manual",
                            "adjustment": "",
                            "status": "history",
                        },
                    ],
                },
            )
            await exam.finish_test()

        exam.check_summary()
