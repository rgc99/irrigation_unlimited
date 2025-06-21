"""Test irrigation_unlimited events."""

import asyncio
from unittest.mock import patch
from datetime import datetime
from typing import Any, NamedTuple
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    EVENT_FINISH,
    EVENT_START,
    SERVICE_TIME_ADJUST,
)
from tests.iu_test_support import IUExam, mk_local, mk_utc

IUExam.quiet_mode()


async def test_events(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test events."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_event.yaml") as exam:

        event_data: list[ha.Event] = []

        def handle_event(event: ha.Event):
            nonlocal event_data
            event_data.append(
                {
                    "event_type": event.event_type,
                    "event_time": exam.virtual_time,
                    "data": event.data,
                }
            )

        hass.bus.async_listen(f"{DOMAIN}_{EVENT_START}", handle_event)
        hass.bus.async_listen(f"{DOMAIN}_{EVENT_FINISH}", handle_event)

        await exam.run_all()

        exam.check_summary()

        assert event_data == [
            {
                "event_type": "irrigation_unlimited_start",
                "event_time": mk_local("2021-01-04 06:05:00"),
                "data": {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                    "controller": {
                        "index": 0,
                        "controller_id": "ctrl_1",
                        "name": "Test controller 1",
                    },
                    "sequence": {"index": 0, "sequence_id": "seq_1", "name": "Seq 1"},
                    "run": {"duration": 5460},
                    "zone_ids": ["zone_1", "zone_2", "zone_3", "zone_4"],
                    "schedule": {
                        "index": 0,
                        "schedule_id": "sched_1",
                        "name": "Schedule 1",
                    },
                },
            },
            {
                "event_type": "irrigation_unlimited_finish",
                "event_time": mk_local("2021-01-04 07:36:00"),
                "data": {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                    "controller": {
                        "index": 0,
                        "controller_id": "ctrl_1",
                        "name": "Test controller 1",
                    },
                    "sequence": {"index": 0, "sequence_id": "seq_1", "name": "Seq 1"},
                    "run": {"duration": 5460},
                    "zone_ids": ["zone_1", "zone_2", "zone_3", "zone_4"],
                    "schedule": {
                        "index": 0,
                        "schedule_id": "sched_1",
                        "name": "Schedule 1",
                    },
                },
            },
            {
                "event_type": "irrigation_unlimited_start",
                "event_time": mk_local("2021-01-04 09:17:00"),
                "data": {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
                    "controller": {
                        "index": 0,
                        "controller_id": "ctrl_1",
                        "name": "Test controller 1",
                    },
                    "sequence": {"index": 1, "sequence_id": "seq_2", "name": "Seq 2"},
                    "zone_ids": ["zone_1", "zone_2", "zone_3", "zone_4"],
                    "run": {"duration": 2280},
                    "schedule": {
                        "index": 0,
                        "schedule_id": "sched_2",
                        "name": "Schedule 1",
                    },
                },
            },
            {
                "event_type": "irrigation_unlimited_finish",
                "event_time": mk_local("2021-01-04 09:55:00"),
                "data": {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
                    "controller": {
                        "index": 0,
                        "controller_id": "ctrl_1",
                        "name": "Test controller 1",
                    },
                    "sequence": {"index": 1, "sequence_id": "seq_2", "name": "Seq 2"},
                    "run": {"duration": 2280},
                    "zone_ids": ["zone_1", "zone_2", "zone_3", "zone_4"],
                    "schedule": {
                        "index": 0,
                        "schedule_id": "sched_2",
                        "name": "Schedule 1",
                    },
                },
            },
        ]


async def test_event_with_adjust(hass: ha.HomeAssistant, allow_memory_db):
    """Test real world delays in automations and recorder."""
    # pylint: disable=unused-argument

    def hist_data(
        hass,
        start_time: datetime,
        end_time: datetime,
        entity_ids: list[str],
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

        class Event(NamedTuple):
            # pylint: disable=missing-class-docstring
            atime: datetime
            entity_id: str

        class State(NamedTuple):
            # pylint: disable=missing-class-docstring
            state: str
            attributes: dict

        data: dict[Event, State] = {
            Event(mk_utc("2024-09-19 06:05:00"), idm): State("on", None),
            Event(mk_utc("2024-09-19 06:05:00"), idz1): State("on", None),
            Event(mk_utc("2024-09-19 06:14:00"), idz1): State("off", None),
            Event(mk_utc("2024-09-19 06:14:00"), idm): State("off", None),
            Event(mk_utc("2024-09-20 06:05:00"), idm): State("on", None),
            Event(mk_utc("2024-09-20 06:05:00"), idz1): State("on", None),
            Event(mk_utc("2024-09-20 06:14:00"), idz1): State("off", None),
            Event(mk_utc("2024-09-20 06:14:00"), idm): State("off", None),
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
                    ha.State(
                        event.entity_id, state.state, state.attributes, event.atime
                    )
                )

        return result

    async with IUExam(hass, "test_event_and_adjust.yaml") as exam:
        await exam.load_dependencies()

        async def handle_event(event: ha.Event):
            # Simulate delay in triggering an automation and responding
            await asyncio.sleep(1)
            await exam.call(
                SERVICE_TIME_ADJUST,
                {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                    "actual": "0:00:00",
                },
            )

        hass.bus.async_listen(f"{DOMAIN}_{EVENT_FINISH}", handle_event)

        await exam.begin_test(1)

        with patch(
            "homeassistant.components.recorder.history.get_significant_states"
        ) as mock:
            mock.side_effect = hist_data

            await exam.run_until("2024-09-20 06:02:00")
            await asyncio.sleep(3)
            exam.check_iu_entity(
                "c1_z1",
                "off",
                {
                    "status": "off",
                    "adjustment": "",
                    "current_schedule": None,
                    "next_adjustment": "",
                    "next_schedule": 1,
                    "next_name": "Schedule 1",
                    "next_start": mk_local("2024-09-20 06:05:00"),
                    "next_duration": "0:10:00",
                    "today_total": 0.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-09-22 06:05:00"),
                            "end": mk_local("2024-09-22 06:15:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-09-21 06:05:00"),
                            "end": mk_local("2024-09-21 06:15:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-09-20 06:05:00"),
                            "end": mk_local("2024-09-20 06:15:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "",
                            "status": "next",
                        },
                        {
                            "start": mk_local("2024-09-19 06:05:00"),
                            "end": mk_local("2024-09-19 06:14:00"),
                            "schedule": None,
                            "schedule_name": None,
                            "adjustment": "",
                            "status": "history",
                        },
                    ],
                },
            )

            await exam.call(
                SERVICE_TIME_ADJUST,
                {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                    "actual": "0:09:00",
                },
            )
            await asyncio.sleep(3)
            exam.check_iu_entity(
                "c1_z1",
                "off",
                {
                    "status": "off",
                    "adjustment": "",
                    "current_schedule": None,
                    "next_adjustment": "=0:09:00",
                    "next_schedule": 1,
                    "next_name": "Schedule 1",
                    "next_start": mk_local("2024-09-20 06:05:00"),
                    "next_duration": "0:09:00",
                    "today_total": 0.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-09-22 06:05:00"),
                            "end": mk_local("2024-09-22 06:14:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "=0:09:00",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-09-21 06:05:00"),
                            "end": mk_local("2024-09-21 06:14:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "=0:09:00",
                            "status": "scheduled",
                        },
                        {
                            "start": mk_local("2024-09-20 06:05:00"),
                            "end": mk_local("2024-09-20 06:14:00"),
                            "schedule": 1,
                            "schedule_name": "Schedule 1",
                            "adjustment": "=0:09:00",
                            "status": "next",
                        },
                        {
                            "start": mk_local("2024-09-19 06:05:00"),
                            "end": mk_local("2024-09-19 06:14:00"),
                            "schedule": None,
                            "schedule_name": None,
                            "adjustment": "",
                            "status": "history",
                        },
                    ],
                },
            )

            await exam.run_until("2024-09-20 06:20:00")
            await asyncio.sleep(3)
            exam.check_iu_entity(
                "c1_z1",
                "off",
                {
                    "status": "off",
                    "adjustment": "",
                    "current_schedule": None,
                    "next_schedule": None,
                    "today_total": 9.0,
                    "timeline": [
                        {
                            "start": mk_local("2024-09-20 06:05:00"),
                            "end": mk_local("2024-09-20 06:14:00"),
                            "schedule": None,
                            "schedule_name": None,
                            "adjustment": "",
                            "status": "history",
                        },
                        {
                            "start": mk_local("2024-09-19 06:05:00"),
                            "end": mk_local("2024-09-19 06:14:00"),
                            "schedule": None,
                            "schedule_name": None,
                            "adjustment": "",
                            "status": "history",
                        },
                    ],
                },
            )

            await exam.finish_test()

        exam.check_summary()
