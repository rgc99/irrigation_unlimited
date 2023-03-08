"""Test irrigation_unlimited history."""
from unittest.mock import patch
from datetime import datetime, timedelta
from collections import Counter
from typing import OrderedDict, List, Any
import pytest
import homeassistant.core as ha
from homeassistant.util import dt
from custom_components.irrigation_unlimited.const import (
    SERVICE_DISABLE,
)
from custom_components.irrigation_unlimited.history import (
    midnight,
    round_seconds_dt,
    round_seconds_td,
)
from tests.iu_test_support import (
    IUExam,
    mk_utc,
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
    """Return dummy history data"""

    result: dict[str, list[ha.State]] = {}
    idx = "binary_sensor.irrigation_unlimited_c1_m"
    if idx in entity_ids:
        result[idx] = []
        if start_time >= mk_utc("2020-12-28 00:00:00") and end_time <= mk_utc(
            "2021-01-04 23:59:59"
        ):
            result[idx].append(ha.State(idx, "on", None, mk_utc("2021-01-04 04:29:00")))
            result[idx].append(
                ha.State(idx, "off", None, mk_utc("2021-01-04 04:33:00"))
            )
            result[idx].append(ha.State(idx, "on", None, mk_utc("2021-01-04 05:29:00")))
            result[idx].append(
                ha.State(idx, "off", None, mk_utc("2021-01-04 05:33:00"))
            )
    idx = "binary_sensor.irrigation_unlimited_c1_z1"
    if idx in entity_ids:
        result[idx] = []
        if start_time >= mk_utc("2020-12-28 00:00:00") and end_time <= mk_utc(
            "2021-01-04 23:59:59"
        ):
            result[idx].append(ha.State(idx, "on", None, mk_utc("2021-01-04 04:30:00")))
            result[idx].append(
                ha.State(idx, "off", None, mk_utc("2021-01-04 04:32:00"))
            )
            result[idx].append(ha.State(idx, "on", None, mk_utc("2021-01-04 05:30:00")))
            result[idx].append(
                ha.State(idx, "off", None, mk_utc("2021-01-04 05:32:00"))
            )
    idx = "binary_sensor.irrigation_unlimited_c1_z2"
    if idx in entity_ids:
        result[idx] = []
        if start_time >= mk_utc("2020-12-28 00:00:00") and end_time <= mk_utc(
            "2021-01-04 23:59:59"
        ):
            result[idx].append(ha.State(idx, "on", None, mk_utc("2021-01-04 04:35:00")))
            result[idx].append(
                ha.State(idx, "off", None, mk_utc("2021-01-04 04:38:00"))
            )
            result[idx].append(ha.State(idx, "on", None, mk_utc("2021-01-04 05:35:00")))
            result[idx].append(
                ha.State(idx, "off", None, mk_utc("2021-01-04 05:38:00"))
            )
            result[idx].append(ha.State(idx, "on", None, mk_utc("2021-01-04 05:40:00")))
            result[idx].append(
                ha.State(idx, "off", None, mk_utc("2021-01-04 05:45:00"))
            )

    return result


def hist_data_2(
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
    """Return dummy history data. Random off at start and left running at end"""

    result: dict[str, list[ha.State]] = {}
    idm = "binary_sensor.irrigation_unlimited_c1_m"
    idz = "binary_sensor.irrigation_unlimited_c1_z1"
    result[idm] = []
    result[idz] = []
    result[idm].append(ha.State(idm, "off", None, mk_utc("2021-01-03 04:00:00")))
    result[idz].append(ha.State(idz, "off", None, mk_utc("2021-01-03 04:00:00")))

    result[idm].append(ha.State(idm, "on", None, mk_utc("2021-01-03 04:09:00")))
    result[idz].append(ha.State(idz, "on", None, mk_utc("2021-01-03 04:10:00")))
    result[idz].append(ha.State(idz, "off", None, mk_utc("2021-01-03 04:15:00")))
    result[idm].append(ha.State(idm, "off", None, mk_utc("2021-01-03 04:16:00")))

    result[idm].append(ha.State(idm, "on", None, mk_utc("2021-01-03 04:19:00")))
    result[idz].append(ha.State(idz, "on", None, mk_utc("2021-01-03 04:20:00")))
    result[idz].append(ha.State(idz, "off", None, mk_utc("2021-01-03 04:25:00")))
    result[idm].append(ha.State(idm, "off", None, mk_utc("2021-01-03 04:26:00")))

    result[idm].append(ha.State(idm, "on", None, mk_utc("2021-01-03 04:29:00")))
    result[idz].append(ha.State(idz, "on", None, mk_utc("2021-01-03 04:30:00")))
    result[idz].append(ha.State(idz, "off", None, mk_utc("2021-01-03 04:35:00")))
    result[idm].append(ha.State(idm, "off", None, mk_utc("2021-01-03 04:36:00")))

    result[idm].append(ha.State(idm, "on", None, mk_utc("2021-01-04 04:09:00")))
    result[idz].append(ha.State(idz, "on", None, mk_utc("2021-01-04 04:10:00")))
    result[idz].append(ha.State(idz, "off", None, mk_utc("2021-01-04 04:15:00")))
    result[idm].append(ha.State(idm, "off", None, mk_utc("2021-01-04 04:16:00")))

    result[idm].append(ha.State(idm, "on", None, mk_utc("2021-01-04 04:19:00")))
    result[idz].append(ha.State(idz, "on", None, mk_utc("2021-01-04 04:20:00")))
    result[idz].append(ha.State(idz, "off", None, mk_utc("2021-01-04 04:25:00")))
    result[idm].append(ha.State(idm, "off", None, mk_utc("2021-01-04 04:26:00")))

    result[idm].append(ha.State(idm, "on", None, mk_utc("2021-01-04 04:29:00")))
    result[idz].append(ha.State(idz, "on", None, mk_utc("2021-01-04 04:30:00")))

    result[idm].append(ha.State(idm, "on", None, mk_utc("2021-01-05 04:09:00")))
    result[idz].append(ha.State(idz, "on", None, mk_utc("2021-01-05 04:10:00")))

    return result


@pytest.fixture(name="allow_memory_db")
def allow_memory_db():
    """Allow in memory DB"""
    with patch(
        "homeassistant.components.recorder.ALLOW_IN_MEMORY_DB",
        return_value=True,
    ):
        yield


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


async def test_history(hass: ha.HomeAssistant, allow_memory_db):
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
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-05 06:05")),
                        ("end", mk_utc("2021-01-05 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 06:05")),
                        ("end", mk_utc("2021-01-04 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:30")),
                        ("end", mk_utc("2021-01-04 05:32")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 04:30")),
                        ("end", mk_utc("2021-01-04 04:32")),
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
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-05 06:10")),
                        ("end", mk_utc("2021-01-05 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 06:10")),
                        ("end", mk_utc("2021-01-04 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:40")),
                        ("end", mk_utc("2021-01-04 05:45")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:35")),
                        ("end", mk_utc("2021-01-04 05:38")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 04:35")),
                        ("end", mk_utc("2021-01-04 04:38")),
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
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-06 06:05")),
                        ("end", mk_utc("2021-01-06 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-05 06:05")),
                        ("end", mk_utc("2021-01-05 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:30")),
                        ("end", mk_utc("2021-01-04 05:32")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 04:30")),
                        ("end", mk_utc("2021-01-04 04:32")),
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
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-06 06:10")),
                        ("end", mk_utc("2021-01-06 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-05 06:10")),
                        ("end", mk_utc("2021-01-05 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:40")),
                        ("end", mk_utc("2021-01-04 05:45")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 05:35")),
                        ("end", mk_utc("2021-01-04 05:38")),
                        ("schedule_name", None),
                        ("adjustment", ""),
                        ("status", "history"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-04 04:35")),
                        ("end", mk_utc("2021-01-04 04:38")),
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
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-06 06:05")),
                        ("end", mk_utc("2021-01-06 06:15")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-05 06:05")),
                        ("end", mk_utc("2021-01-05 06:15")),
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
                        ("start", mk_utc("2021-01-07 06:10")),
                        ("end", mk_utc("2021-01-07 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-06 06:10")),
                        ("end", mk_utc("2021-01-06 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "scheduled"),
                    ]
                ),
                OrderedDict(
                    [
                        ("start", mk_utc("2021-01-05 06:10")),
                        ("end", mk_utc("2021-01-05 06:20")),
                        ("schedule_name", "Schedule 1"),
                        ("adjustment", ""),
                        ("status", "next"),
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

        stime = mk_utc("2021-01-04 04:32:00")
        exam.coordinator.history.load(None, False)
        assert exam.coordinator.history._enabled is True
        exam.coordinator.history.load({"history": {"enabled": False}}, True)
        assert exam.coordinator.history._enabled is False
        exam.coordinator.history.muster(stime, True)
        assert exam.coordinator.history._initialise() is False

        with patch(
            "homeassistant.components.recorder.history.get_significant_states"
        ) as mock:
            mock.side_effect = hist_data_2

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
                                    ("start", mk_utc("2021-01-03 04:09")),
                                    ("end", mk_utc("2021-01-03 04:16")),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-01-03 04:19")),
                                    ("end", mk_utc("2021-01-03 04:26")),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-01-03 04:29")),
                                    ("end", mk_utc("2021-01-03 04:36")),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-01-04 04:09")),
                                    ("end", mk_utc("2021-01-04 04:16")),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-01-04 04:19")),
                                    ("end", mk_utc("2021-01-04 04:26")),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-01-04 04:29")),
                                    ("end", mk_utc("2021-01-04 04:32")),
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
                                    ("start", mk_utc("2021-01-03 04:10")),
                                    ("end", mk_utc("2021-01-03 04:15")),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-01-03 04:20")),
                                    ("end", mk_utc("2021-01-03 04:25")),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-01-03 04:30")),
                                    ("end", mk_utc("2021-01-03 04:35")),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-01-04 04:10")),
                                    ("end", mk_utc("2021-01-04 04:15")),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-01-04 04:20")),
                                    ("end", mk_utc("2021-01-04 04:25")),
                                    ("schedule_name", None),
                                    ("adjustment", ""),
                                ]
                            ),
                            OrderedDict(
                                [
                                    ("start", mk_utc("2021-01-04 04:30")),
                                    ("end", mk_utc("2021-01-04 04:32")),
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
