"""irrigation_unlimited service pause/resume tester"""

import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_PAUSE,
    SERVICE_RESUME,
    DOMAIN,
    EVENT_FINISH,
    EVENT_START,
)
from tests.iu_test_support import IUExam, mk_local

IUExam.quiet_mode()


# pylint: disable=unused-argument
async def test_service_sequence_pause_resume_notify(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test pause/resume service calls to sequence notifications"""
    async with IUExam(hass, "service_sequence_pause_resume_notify.yaml") as exam:
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

        await exam.begin_test(1)
        await exam.run_until("2024-08-14 06:07:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        exam.check_iu_entity(
            "c1_z1",
            "off",
            {
                "timeline": [
                    {
                        "start": mk_local("2024-08-16 06:05:00"),
                        "end": mk_local("2024-08-16 06:09:00"),
                        "schedule": 1,
                        "schedule_name": "Schedule 1",
                        "adjustment": "",
                        "status": "scheduled",
                    },
                    {
                        "start": mk_local("2024-08-15 06:05:00"),
                        "end": mk_local("2024-08-15 06:09:00"),
                        "schedule": 1,
                        "schedule_name": "Schedule 1",
                        "adjustment": "",
                        "status": "next",
                    },
                    {
                        "start": mk_local("2024-08-14 06:07:00"),
                        "end": mk_local("2024-08-14 06:09:00"),
                        "schedule": 1,
                        "schedule_name": "Schedule 1",
                        "adjustment": "",
                        "status": "scheduled",
                    },
                ],
            },
        )
        await exam.run_until("2024-08-14 06:12:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        exam.check_iu_entity(
            "c1_z1",
            "on",
            {
                "timeline": [
                    {
                        "start": mk_local("2024-08-16 06:05:00"),
                        "end": mk_local("2024-08-16 06:09:00"),
                        "schedule": 1,
                        "schedule_name": "Schedule 1",
                        "adjustment": "",
                        "status": "scheduled",
                    },
                    {
                        "start": mk_local("2024-08-15 06:05:00"),
                        "end": mk_local("2024-08-15 06:09:00"),
                        "schedule": 1,
                        "schedule_name": "Schedule 1",
                        "adjustment": "",
                        "status": "next",
                    },
                    {
                        "start": mk_local("2024-08-14 06:12:00"),
                        "end": mk_local("2024-08-14 06:14:00"),
                        "schedule": 1,
                        "schedule_name": "Schedule 1",
                        "adjustment": "",
                        "status": "running",
                    },
                ],
            },
        )
        await exam.finish_test()
        assert event_data == [
            {
                "event_type": "irrigation_unlimited_start",
                "event_time": mk_local("2024-08-14 06:05"),
                "data": {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                    "id": "1_1",
                    "iu_id": "c1_s1",
                    "volume": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test Controller",
                    },
                    "zones": [
                        {
                            "duration": 240,
                            "index": 0,
                            "name": "Zone 1",
                            "volume": None,
                            "zone_id": "1",
                        },
                        {
                            "duration": 240,
                            "index": 1,
                            "name": "Zone 2",
                            "volume": None,
                            "zone_id": "2",
                        },
                    ],
                    "sequence": {"index": 0, "sequence_id": "1", "name": "Seq 1"},
                    "run": {"duration": 600},
                    "zone_ids": ["1", "2"],
                    "schedule": {"index": 0, "schedule_id": None, "name": "Schedule 1"},
                },
            },
            {
                "event_type": "irrigation_unlimited_finish",
                "event_time": mk_local("2024-08-14 06:20"),
                "data": {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                    "id": "1_1",
                    "iu_id": "c1_s1",
                    "volume": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test Controller",
                    },
                    "zones": [
                        {
                            "duration": 120,
                            "index": 0,
                            "name": "Zone 1",
                            "volume": None,
                            "zone_id": "1",
                        },
                        {
                            "duration": 240,
                            "index": 1,
                            "name": "Zone 2",
                            "volume": None,
                            "zone_id": "2",
                        },
                    ],
                    "sequence": {"index": 0, "sequence_id": "1", "name": "Seq 1"},
                    "run": {"duration": 900},
                    "zone_ids": ["1", "2"],
                    "schedule": {"index": 0, "schedule_id": None, "name": "Schedule 1"},
                },
            },
        ]
        exam.check_summary()


async def test_service_sequence_pause_resume_multi(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test basic pause/resume service calls to sequence"""
    async with IUExam(hass, "service_sequence_pause_resume_multi.yaml") as exam:
        await exam.run_test(1)

        await exam.begin_test(2)
        await exam.run_until("2023-11-28 06:07:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:12:00")
        # Should have no effect
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:17:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:22:00")
        # should have no effect
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.run_until("2023-11-28 06:07:00")
        # Target wrong entity
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
            },
        )
        await exam.run_until("2023-11-28 06:17:00")
        # Target wrong entity
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
            },
        )
        await exam.finish_test()

        await exam.run_test(4)

        await exam.begin_test(5)
        await exam.run_until("2023-11-28 08:26:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 3,
            },
        )
        await exam.run_until("2023-11-28 08:36:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 3,
            },
        )
        await exam.finish_test()

        await exam.begin_test(6)
        await exam.run_until("2023-11-28 08:26:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
            },
        )
        await exam.run_until("2023-11-28 08:36:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
            },
        )
        await exam.finish_test()

        await exam.begin_test(7)
        await exam.run_until("2023-11-28 08:17:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
            },
        )
        await exam.run_until("2023-11-28 08:26:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 3,
            },
        )
        await exam.run_until("2023-11-28 08:27:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
            },
        )
        await exam.run_until("2023-11-28 08:36:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 3,
            },
        )
        await exam.finish_test()

        exam.check_summary()


async def test_service_sequence_pause_resume_exhaustive(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test pause/resume service calls to sequence"""

    async with IUExam(hass, "service_sequence_pause_resume_exhustive.yaml") as exam:

        # Sequence 1 tests
        await exam.run_test(1)

        await exam.begin_test(2)
        await exam.run_until("2023-11-28 06:03:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:07:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.run_until("2023-11-28 06:09:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:11:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.run_until("2023-11-28 06:15:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:17:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(5)
        await exam.run_until("2023-11-28 06:22:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(6)
        await exam.run_until("2023-11-28 06:04:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:06:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(7)
        await exam.run_until("2023-11-28 06:10:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:12:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(8)
        await exam.run_until("2023-11-28 06:16:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:18:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(9)
        await exam.run_until("2023-11-28 06:07:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:09:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(10)
        await exam.run_until("2023-11-28 06:12:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:14:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(11)
        await exam.run_until("2023-11-28 06:18:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:20:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(12)
        await exam.run_until("2023-11-28 06:08:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:10:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(13)
        await exam.run_until("2023-11-28 06:14:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:16:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(14)
        await exam.run_until("2023-11-28 06:20:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:22:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(15)

        # Preamble z1
        await exam.run_until("2023-11-28 06:04:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:06:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )

        # Running z1
        await exam.run_until("2023-11-28 06:08:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:10:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )

        # Postamble z1
        await exam.run_until("2023-11-28 06:14:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:16:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )

        # Preamble z2,z3
        await exam.run_until("2023-11-28 06:16:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:18:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )

        # Postamble z2,z3
        await exam.run_until("2023-11-28 06:23:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:25:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )

        # Preamble z4
        await exam.run_until("2023-11-28 06:25:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:27:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )

        # Running z4
        await exam.run_until("2023-11-28 06:29:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:31:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )

        # Postamble z4
        await exam.run_until("2023-11-28 06:35:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:37:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )

        await exam.finish_test()

        # Sequence 2 tests - overlapped pre/postamble
        await exam.run_test(16)

        await exam.begin_test(17)
        await exam.run_until("2023-11-28 08:10:20")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        await exam.run_until("2023-11-28 08:20:20")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        await exam.finish_test()

        await exam.begin_test(18)
        await exam.run_until("2023-11-28 08:07")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        await exam.run_until("2023-11-28 08:17")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        await exam.finish_test()

        # Controller 2 (No pre or post amble)
        await exam.run_test(19)

        await exam.begin_test(20)
        await exam.run_until("2023-11-28 10:07")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c2_s1",
            },
        )
        await exam.run_until("2023-11-28 10:17")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c2_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(21)
        await exam.run_until("2023-11-28 10:09")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c2_s1",
            },
        )
        await exam.run_until("2023-11-28 10:19")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c2_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(22)
        await exam.run_until("2023-11-28 10:12")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c2_s1",
            },
        )
        await exam.run_until("2023-11-28 10:22")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c2_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(23)
        await exam.run_until("2023-11-28 10:15")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c2_s1",
            },
        )
        await exam.run_until("2023-11-28 10:25")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c2_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(24)
        await exam.run_until("2023-11-28 10:18")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c2_s1",
            },
        )
        await exam.run_until("2023-11-28 10:28")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c2_s1",
            },
        )
        await exam.finish_test()

        await exam.run_test(25)

        await exam.begin_test(26)
        await exam.run_until("2023-11-28 12:05:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.run_until("2023-11-28 12:15:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(27)
        await exam.run_until("2023-11-28 12:06:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.run_until("2023-11-28 12:16:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(28)
        await exam.run_until("2023-11-28 12:09:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.run_until("2023-11-28 12:19:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(29)
        await exam.run_until("2023-11-28 12:12:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.run_until("2023-11-28 12:22:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(30)
        await exam.run_until("2023-11-28 12:15:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.run_until("2023-11-28 12:25:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(31)
        await exam.run_until("2023-11-28 12:17:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.run_until("2023-11-28 12:27:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(32)
        await exam.run_until("2023-11-28 12:19:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.run_until("2023-11-28 12:29:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(33)
        await exam.run_until("2023-11-28 12:22:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.run_until("2023-11-28 12:32:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(34)
        await exam.run_until("2023-11-28 12:25:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.run_until("2023-11-28 12:35:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(35)
        await exam.run_until("2023-11-28 12:28:00")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.run_until("2023-11-28 12:38:00")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(36)
        await exam.run_until("2023-11-28 12:29:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.run_until("2023-11-28 12:39:30")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c3_s1",
            },
        )
        await exam.finish_test()

        exam.check_summary()
