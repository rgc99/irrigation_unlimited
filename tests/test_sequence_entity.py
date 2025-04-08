"""irrigation_unlimited test unit for IUSequenceRun object"""

# pylint: disable=too-many-lines
import homeassistant.core as ha
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
)
from tests.iu_test_support import IUExam, mk_local
from custom_components.irrigation_unlimited.const import (
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_TIME_ADJUST,
    SERVICE_SUSPEND,
    SERVICE_PAUSE,
    SERVICE_RESUME,
    SERVICE_SKIP,
    SERVICE_CANCEL,
)

IUExam.quiet_mode()


async def test_sequence_entity(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test IUSequence class."""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-statements
    async with IUExam(hass, "test_sequence_entity.yaml") as exam:
        await exam.begin_test(1)
        # Exhustive test of entity
        exam.check_iu_entity(
            "c1_s1",
            STATE_OFF,
            {
                "friendly_name": "Seq 1",
                "icon": "mdi:stop-circle-outline",
                "enabled": True,
                "suspended": None,
                "index": 0,
                "status": "off",
                "schedule_count": 2,
                "adjustment": "",
                "current_zone": None,
                "current_schedule": None,
                "percent_complete": 0,
                "next_start": mk_local("2023-11-16 06:05"),
                "next_duration": "0:38:00",
                "next_schedule": 1,
                "next_name": "Dawn",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:06:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                        "duration": "0:12:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["4"],
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_OFF,
            {
                "friendly_name": "Seq 2",
                "icon": "mdi:stop-circle-outline",
                "enabled": True,
                "suspended": None,
                "index": 1,
                "status": "off",
                "schedule_count": 1,
                "adjustment": "",
                "current_zone": None,
                "current_schedule": None,
                "percent_complete": 0,
                "next_start": mk_local("2023-11-16 06:10"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:05:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["3"],
                        "duration": "0:08:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["5"],
                        "duration": "0:13:00",
                    },
                ],
            },
        )

        await exam.run_until("2023-11-16 06:07")
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "status": "on",
                "current_zone": 1,
                "current_start": mk_local("2023-11-16 06:05:00"),
                "current_duration": "0:38:00",
                "current_schedule": 1,
                "current_name": "Dawn",
                "time_remaining": "0:36:00",
                "percent_complete": 5,
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": "0:06:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:12:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_OFF,
            {
                "status": "off",
                "current_zone": None,
                "current_schedule": None,
                "percent_complete": 0,
                "next_start": mk_local("2023-11-16 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:stop-circle-outline",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:05:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:08:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:13:00",
                    },
                ],
            },
        )

        await exam.run_until("2023-11-16 06:11:30")
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "status": "delay",
                "current_zone": None,
                "current_start": mk_local("2023-11-16 06:05:00"),
                "current_duration": "0:38:00",
                "current_schedule": 1,
                "current_name": "Dawn",
                "time_remaining": "0:31:30",
                "percent_complete": 17,
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:timer-sand",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:12:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_ON,
            {
                "status": "on",
                "current_zone": 1,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:27:00",
                "current_schedule": 1,
                "current_name": "Morning",
                "time_remaining": "0:25:30",
                "percent_complete": 5,
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": "0:05:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:08:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:13:00",
                    },
                ],
            },
        )

        await exam.run_until("2023-11-16 06:14")
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "status": "on",
                "current_zone": 2,
                "current_start": mk_local("2023-11-16 06:05:00"),
                "current_duration": "0:38:00",
                "current_schedule": 1,
                "current_name": "Dawn",
                "time_remaining": "0:29:00",
                "percent_complete": 23,
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": "0:12:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_ON,
            {
                "status": "on",
                "current_zone": 1,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:27:00",
                "current_schedule": 1,
                "current_name": "Morning",
                "time_remaining": "0:23:00",
                "percent_complete": 14,
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": "0:05:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:08:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:13:00",
                    },
                ],
            },
        )

        await exam.run_until("2023-11-16 06:20")
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "status": "on",
                "current_zone": 2,
                "current_start": mk_local("2023-11-16 06:05:00"),
                "current_duration": "0:38:00",
                "current_schedule": 1,
                "current_name": "Dawn",
                "time_remaining": "0:23:00",
                "percent_complete": 39,
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": "0:12:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_ON,
            {
                "status": "on",
                "current_zone": 2,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:27:00",
                "current_schedule": 1,
                "current_name": "Morning",
                "time_remaining": "0:17:00",
                "percent_complete": 37,
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": "0:08:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:13:00",
                    },
                ],
            },
        )

        await exam.run_until("2023-11-16 06:24:30")
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "status": "delay",
                "current_zone": None,
                "current_start": mk_local("2023-11-16 06:05:00"),
                "current_duration": "0:38:00",
                "current_schedule": 1,
                "current_name": "Dawn",
                "time_remaining": "0:18:30",
                "percent_complete": 51,
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:timer-sand",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_ON,
            {
                "status": "on",
                "current_zone": 3,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:27:00",
                "current_schedule": 1,
                "current_name": "Morning",
                "time_remaining": "0:12:30",
                "percent_complete": 53,
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": "0:13:00",
                    },
                ],
            },
        )

        await exam.run_until("2023-11-16 06:27")
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "status": "on",
                "current_zone": 3,
                "current_start": mk_local("2023-11-16 06:05:00"),
                "current_duration": "0:38:00",
                "current_schedule": 1,
                "current_name": "Dawn",
                "time_remaining": "0:16:00",
                "percent_complete": 57,
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_ON,
            {
                "status": "on",
                "current_zone": 3,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:27:00",
                "current_schedule": 1,
                "current_name": "Morning",
                "time_remaining": "0:10:00",
                "percent_complete": 62,
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": "0:13:00",
                    },
                ],
            },
        )

        await exam.run_until("2023-11-16 06:40")
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "status": "on",
                "current_zone": 3,
                "current_start": mk_local("2023-11-16 06:05:00"),
                "current_duration": "0:38:00",
                "current_schedule": 1,
                "current_name": "Dawn",
                "time_remaining": "0:03:00",
                "percent_complete": 92,
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:00:00",
                    },
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_OFF,
            {
                "status": "off",
                "current_zone": None,
                "current_schedule": None,
                "percent_complete": 0,
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:stop-circle-outline",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:05:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:08:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:13:00",
                    },
                ],
            },
        )

        await exam.run_until("2023-11-16 06:50")
        exam.check_iu_entity(
            "c1_s1",
            STATE_OFF,
            {
                "status": "off",
                "current_zone": None,
                "current_schedule": None,
                "percent_complete": 0,
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:stop-circle-outline",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:06:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:12:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_OFF,
            {
                "status": "off",
                "current_zone": None,
                "current_schedule": None,
                "percent_complete": 0,
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:stop-circle-outline",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:05:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:08:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": "0:13:00",
                    },
                ],
            },
        )

        await exam.finish_test()

        # Sequence 2 adjustment = %0.0
        await exam.begin_test(2)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
                "percentage": 0,
            },
        )
        exam.check_iu_entity(
            "c1_s1",
            STATE_OFF,
            {
                "index": 0,
                "enabled": True,
                "suspended": None,
                "status": "off",
                "zone_count": 3,
                "schedule_count": 2,
                "adjustment": "",
                "current_zone": None,
                "current_schedule": None,
                "percent_complete": 0,
                "next_start": mk_local("2023-11-16 06:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 1,
                "next_name": "Dawn",
                "icon": "mdi:stop-circle-outline",
                "friendly_name": "Seq 1",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:06:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                        "duration": "0:12:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["4"],
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_OFF,
            {
                "index": 1,
                "enabled": True,
                "suspended": None,
                "status": "off",
                "zone_count": 3,
                "schedule_count": 1,
                "adjustment": "%0.0",
                "current_zone": None,
                "current_schedule": None,
                "percent_complete": 0,
                "next_schedule": None,
                "icon": "mdi:stop-circle-outline",
                "friendly_name": "Seq 2",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:00:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["3"],
                        "duration": "0:00:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["5"],
                        "duration": "0:00:00",
                    },
                ],
            },
        )
        await exam.finish_test()

        # Sequence 2 disabled
        await exam.begin_test(3)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
                "reset": None,
            },
        )
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
            },
        )
        exam.check_iu_entity(
            "c1_s1",
            STATE_OFF,
            {
                "enabled": True,
                "suspended": None,
                "status": "off",
                "adjustment": "",
                "current_zone": None,
                "current_schedule": None,
                "percent_complete": 0,
                "next_start": mk_local("2023-11-16 06:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 1,
                "next_name": "Dawn",
                "icon": "mdi:stop-circle-outline",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:06:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                        "duration": "0:12:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["4"],
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_OFF,
            {
                "enabled": False,
                "suspended": None,
                "status": "disabled",
                "adjustment": "",
                "current_zone": None,
                "current_schedule": None,
                "percent_complete": 0,
                "next_schedule": None,
                "icon": "mdi:circle-off-outline",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "blocked",
                        "icon": "mdi:alert-octagon-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:00:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "blocked",
                        "icon": "mdi:alert-octagon-outline",
                        "adjustment": "",
                        "zone_ids": ["3"],
                        "duration": "0:00:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "blocked",
                        "icon": "mdi:alert-octagon-outline",
                        "adjustment": "",
                        "zone_ids": ["5"],
                        "duration": "0:00:00",
                    },
                ],
            },
        )
        await exam.finish_test()

        # Sequence 2 suspended
        await exam.begin_test(4)
        await exam.call(
            SERVICE_ENABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
            },
        )
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
                "for": "0:20:00",
            },
        )
        exam.check_iu_entity(
            "c1_s1",
            STATE_OFF,
            {
                "index": 0,
                "enabled": True,
                "suspended": None,
                "status": "off",
                "zone_count": 3,
                "schedule_count": 2,
                "adjustment": "",
                "current_zone": None,
                "current_schedule": None,
                "percent_complete": 0,
                "next_start": mk_local("2023-11-16 06:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 1,
                "next_name": "Dawn",
                "icon": "mdi:stop-circle-outline",
                "friendly_name": "Seq 1",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:06:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                        "duration": "0:12:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["4"],
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_OFF,
            {
                "index": 1,
                "enabled": True,
                "suspended": mk_local("2023-11-16 06:20:00"),
                "status": "suspended",
                "zone_count": 3,
                "schedule_count": 1,
                "adjustment": "",
                "current_zone": None,
                "current_schedule": None,
                "percent_complete": 0,
                "next_schedule": None,
                "icon": "mdi:timer-outline",
                "friendly_name": "Seq 2",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "blocked",
                        "icon": "mdi:alert-octagon-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:00:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "blocked",
                        "icon": "mdi:alert-octagon-outline",
                        "adjustment": "",
                        "zone_ids": ["3"],
                        "duration": "0:00:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "blocked",
                        "icon": "mdi:alert-octagon-outline",
                        "adjustment": "",
                        "zone_ids": ["5"],
                        "duration": "0:00:00",
                    },
                ],
            },
        )
        await exam.finish_test()

        await exam.begin_test(5)
        await exam.run_until("2023-11-16 06:14")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "status": "on",
                "adjustment": "",
                "current_zone": 2,
                "current_start": mk_local("2023-11-16 06:05:00"),
                "current_duration": "0:38:00",
                "current_schedule": 1,
                "current_name": "Dawn",
                "time_remaining": "0:29:00",
                "percent_complete": 23,
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:00:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                        "duration": "0:12:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["4"],
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_ON,
            {
                "status": "paused",
                "adjustment": "",
                "current_zone": 1,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:27:00",
                "current_schedule": 1,
                "current_name": "Morning",
                "time_remaining": "0:23:00",
                "percent_complete": 14,
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:pause-circle-outline",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:01:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["3"],
                        "duration": "0:08:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["5"],
                        "duration": "0:13:00",
                    },
                ],
            },
        )
        await exam.run_until("2023-11-16 06:19")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "status": "on",
                "current_zone": 2,
                "current_start": mk_local("2023-11-16 06:05:00"),
                "current_duration": "0:38:00",
                "time_remaining": "0:24:00",
                "percent_complete": 36,
                "current_schedule": 1,
                "current_name": "Dawn",
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "start": None,
                        "duration": "0:00:00",
                    },
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "start": mk_local("2023-11-16 06:12:00"),
                        "duration": "0:12:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "start": mk_local("2023-11-16 06:25:00"),
                        "duration": "0:18:00",
                    },
                ],
                "icon": "mdi:play-circle-outline",
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_ON,
            {
                "status": "on",
                "adjustment": "",
                "current_zone": 1,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:32:00",
                "current_schedule": 1,
                "current_name": "Morning",
                "time_remaining": "0:23:00",
                "percent_complete": 28,
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:01:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["3"],
                        "duration": "0:08:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["5"],
                        "duration": "0:13:00",
                    },
                ],
            },
        )
        await exam.run_until("2023-11-16 06:20:15")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_ON,
            {
                "status": "paused",
                "current_zone": None,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:32:00",
                "time_remaining": "0:21:45",
                "percent_complete": 32,
                "current_schedule": 1,
                "current_name": "Morning",
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "start": None,
                        "duration": "0:00:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "start": mk_local("2023-11-16 06:20:30"),
                        "duration": "0:08:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "start": mk_local("2023-11-16 06:29:00"),
                        "duration": "0:13:00",
                    },
                ],
                "icon": "mdi:pause-circle-outline",
            },
        )
        await exam.run_until("2023-11-16 06:25:15")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_ON,
            {
                "status": "on",
                "current_zone": 2,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:36:45",
                "time_remaining": "0:21:30",
                "percent_complete": 41,
                "current_schedule": 1,
                "current_name": "Morning",
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "start": None,
                        "duration": "0:00:00",
                    },
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "start": mk_local("2023-11-16 06:25:15"),
                        "duration": "0:08:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "start": mk_local("2023-11-16 06:33:45"),
                        "duration": "0:13:00",
                    },
                ],
                "icon": "mdi:play-circle-outline",
            },
        )
        await exam.run_until("2023-11-16 06:40")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_ON,
            {
                "status": "paused",
                "adjustment": "",
                "current_zone": 3,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:36:45",
                "time_remaining": "0:06:45",
                "percent_complete": 81,
                "current_schedule": 1,
                "current_name": "Morning",
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "start": None,
                        "duration": "0:00:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "start": None,
                        "duration": "0:00:00",
                    },
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "start": mk_local("2023-11-16 06:40:00"),
                        "duration": "0:06:45",
                    },
                ],
                "icon": "mdi:pause-circle-outline",
            },
        )
        await exam.run_until("2023-11-16 06:45")
        await exam.call(
            SERVICE_RESUME,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_ON,
            {
                "status": "on",
                "adjustment": "",
                "current_zone": 3,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:41:45",
                "time_remaining": "0:06:45",
                "percent_complete": 83,
                "current_schedule": 1,
                "current_name": "Morning",
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "zones": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "start": None,
                        "duration": "0:00:00",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "start": None,
                        "duration": "0:00:00",
                    },
                    {
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "start": mk_local("2023-11-16 06:45:00"),
                        "duration": "0:06:45",
                    },
                ],
                "icon": "mdi:play-circle-outline",
            },
        )
        await exam.run_until("2023-11-16 06:52")
        exam.check_iu_entity(
            "c1_s1",
            STATE_OFF,
            {
                "status": "off",
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "zones": [
                    {
                        "status": "off",
                        "duration": "0:06:00",
                    },
                    {
                        "status": "off",
                        "duration": "0:12:00",
                    },
                    {
                        "status": "off",
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_OFF,
            {
                "status": "off",
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "zones": [
                    {
                        "status": "off",
                        "duration": "0:05:00",
                    },
                    {
                        "status": "off",
                        "duration": "0:08:00",
                    },
                    {
                        "status": "off",
                        "duration": "0:13:00",
                    },
                ],
            },
        )
        # Old style sequence status via controller
        exam.check_iu_entity(
            "c1_m",
            STATE_OFF,
            {
                "enabled": True,
                "suspended": None,
                "status": "off",
                "sequence_status": [
                    {
                        "status": "off",
                        "start": mk_local("2023-11-16 17:05:00"),
                        "duration": 2160,
                        "zones": [
                            {
                                "status": "off",
                                "duration": 360,
                            },
                            {
                                "status": "off",
                                "duration": 720,
                            },
                            {
                                "status": "off",
                                "duration": 1080,
                            },
                        ],
                    },
                    {
                        "status": "off",
                        "start": mk_local("2023-11-17 06:10:00"),
                        "duration": 1560,
                        "zones": [
                            {
                                "status": "off",
                                "duration": 300,
                            },
                            {
                                "status": "off",
                                "duration": 480,
                            },
                            {
                                "status": "off",
                                "duration": 780,
                            },
                        ],
                    },
                ],
                "current_zone": "not running",
                "percent_complete": 0,
                "next_zone": 1,
                "next_name": "Zone 1",
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:06:00",
                "icon": "mdi:water-off",
            },
        )
        await exam.finish_test()

        await exam.begin_test(6)
        await exam.run_until("2023-11-16 06:13")
        await exam.call(
            SERVICE_SKIP,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "status": "on",
                "adjustment": "",
                "current_zone": 2,
                "current_start": mk_local("2023-11-16 06:05:00"),
                "current_duration": "0:38:00",
                "current_schedule": 1,
                "current_name": "Dawn",
                "time_remaining": "0:30:00",
                "percent_complete": 21,
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:00:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                        "duration": "0:12:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["4"],
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_ON,
            {
                "status": "delay",
                "adjustment": "",
                "current_zone": None,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:25:00",
                "current_schedule": 1,
                "current_name": "Morning",
                "time_remaining": "0:22:00",
                "percent_complete": 12,
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:timer-sand",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:00:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["3"],
                        "duration": "0:08:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["5"],
                        "duration": "0:13:00",
                    },
                ],
            },
        )
        await exam.run_until("2023-11-16 06:14")
        exam.check_iu_entity(
            "c1_s2",
            STATE_ON,
            {
                "status": "on",
                "adjustment": "",
                "current_zone": 2,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:25:00",
                "current_schedule": 1,
                "current_name": "Morning",
                "time_remaining": "0:21:00",
                "percent_complete": 16,
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:play-circle-outline",
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["1"],
                        "duration": "0:00:00",
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["3"],
                        "duration": "0:08:00",
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "adjustment": "",
                        "zone_ids": ["5"],
                        "duration": "0:13:00",
                    },
                ],
            },
        )
        await exam.finish_test()

        await exam.begin_test(7)
        await exam.run_until("2023-11-16 06:13")
        await exam.call(
            SERVICE_CANCEL,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "status": "on",
                "current_zone": 2,
                "current_start": mk_local("2023-11-16 06:05:00"),
                "current_duration": "0:38:00",
                "time_remaining": "0:30:00",
                "percent_complete": 21,
                "current_schedule": 1,
                "current_name": "Dawn",
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "zones": [
                    {
                        "status": "off",
                        "start": None,
                        "duration": "0:00:00",
                    },
                    {
                        "status": "on",
                        "start": mk_local("2023-11-16 06:12:00"),
                        "duration": "0:12:00",
                    },
                    {
                        "status": "off",
                        "start": mk_local("2023-11-16 06:25:00"),
                        "duration": "0:18:00",
                    },
                ],
                "icon": "mdi:play-circle-outline",
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_OFF,
            {
                "status": "off",
                "current_zone": None,
                "current_start": mk_local("2023-11-16 06:10:00"),
                "current_duration": "0:03:00",
                "time_remaining": "0:00:00",
                "percent_complete": 100,
                "current_schedule": 1,
                "current_name": "Morning",
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "zones": [
                    {
                        "status": "off",
                        "start": None,
                        "duration": "0:00:00",
                    },
                    {
                        "status": "off",
                        "start": None,
                        "duration": "0:00:00",
                    },
                    {
                        "status": "off",
                        "start": None,
                        "duration": "0:00:00",
                    },
                ],
                "icon": "mdi:stop-circle-outline",
            },
        )
        await exam.run_until("2023-11-16 06:45")
        exam.check_iu_entity(
            "c1_s1",
            STATE_OFF,
            {
                "status": "off",
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "zones": [
                    {
                        "status": "off",
                        "duration": "0:06:00",
                    },
                    {
                        "status": "off",
                        "duration": "0:12:00",
                    },
                    {
                        "status": "off",
                        "duration": "0:18:00",
                    },
                ],
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_OFF,
            {
                "status": "off",
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "zones": [
                    {
                        "status": "off",
                        "duration": "0:05:00",
                    },
                    {
                        "status": "off",
                        "duration": "0:08:00",
                    },
                    {
                        "status": "off",
                        "duration": "0:13:00",
                    },
                ],
            },
        )
        # Old style sequence status via controller
        exam.check_iu_entity(
            "c1_m",
            STATE_OFF,
            {
                "status": "off",
                "sequence_status": [
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "start": mk_local("2023-11-16 17:05:00"),
                        "duration": 2160,
                        "adjustment": "",
                        "schedule": {"index": 1, "name": "Dusk"},
                        "zones": [
                            {
                                "status": "off",
                                "icon": "mdi:stop-circle-outline",
                                "duration": 360,
                            },
                            {
                                "status": "off",
                                "icon": "mdi:stop-circle-outline",
                                "duration": 720,
                            },
                            {
                                "status": "off",
                                "icon": "mdi:stop-circle-outline",
                                "duration": 1080,
                            },
                        ],
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "start": mk_local("2023-11-17 06:10:00"),
                        "duration": 1560,
                        "schedule": {"index": 0, "name": "Morning"},
                        "zones": [
                            {
                                "status": "off",
                                "icon": "mdi:stop-circle-outline",
                                "duration": 300,
                            },
                            {
                                "status": "off",
                                "icon": "mdi:stop-circle-outline",
                                "duration": 480,
                            },
                            {
                                "status": "off",
                                "icon": "mdi:stop-circle-outline",
                                "duration": 780,
                            },
                        ],
                    },
                ],
                "current_zone": "not running",
                "percent_complete": 0,
                "next_zone": 1,
                "next_name": "Zone 1",
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:06:00",
                "icon": "mdi:water-off",
            },
        )
        await exam.finish_test()

        exam.check_summary()


async def test_sequence_repeat(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test Sequence repeats."""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-statements
    async with IUExam(hass, "test_sequence_repeat.yaml") as exam:
        await exam.begin_test(1)
        await exam.run_until("2024-09-05 06:06")
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "index": 0,
                "time_remaining": "1:10:00",
                "percent_complete": 1,
                "repeat": "1/2",
            },
        )
        await exam.run_until("2024-09-05 06:40:30")
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "index": 0,
                "time_remaining": "0:36:00",
                "percent_complete": 49,
                "repeat": "2/2",
            },
        )
        await exam.finish_test()

        exam.check_summary()


async def test_sequence_repeat_single(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test Sequence repeats."""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-statements
    async with IUExam(hass, "test_sequence_repeat_single.yaml") as exam:
        await exam.begin_test(1)
        await exam.run_until("2024-11-11 12:02:00")
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "index": 0,
                "time_remaining": "0:09:00",
                "percent_complete": 18,
                "repeat": "1/2",
            },
        )
        await exam.run_until("2024-11-11 12:09:00")
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "index": 0,
                "time_remaining": "0:02:00",
                "percent_complete": 81,
                "repeat": "2/2",
            },
        )
        await exam.finish_test()

        exam.check_summary()
