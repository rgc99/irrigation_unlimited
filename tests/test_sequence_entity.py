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
)

IUExam.quiet_mode()


async def test_sequence_run(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test IUSequenceRun class."""
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
                "next_start": mk_local("2023-11-16 06:05"),
                "next_duration": "0:38:00",
                "next_schedule": 1,
                "next_name": "Dawn",
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
                "next_start": mk_local("2023-11-16 06:10"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
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
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:play-circle-outline",
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_OFF,
            {
                "status": "off",
                "current_zone": None,
                "current_schedule": None,
                "next_start": mk_local("2023-11-16 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:stop-circle-outline",
            },
        )

        await exam.run_until("2023-11-16 06:11:30")
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "status": "paused",
                "current_zone": None,
                "current_start": mk_local("2023-11-16 06:05:00"),
                "current_duration": "0:38:00",
                "current_schedule": 1,
                "current_name": "Dawn",
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:pause-circle-outline",
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
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:play-circle-outline",
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
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:play-circle-outline",
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
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:play-circle-outline",
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
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:play-circle-outline",
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
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:play-circle-outline",
            },
        )

        await exam.run_until("2023-11-16 06:24:30")
        exam.check_iu_entity(
            "c1_s1",
            STATE_ON,
            {
                "status": "paused",
                "current_zone": None,
                "current_start": mk_local("2023-11-16 06:05:00"),
                "current_duration": "0:38:00",
                "current_schedule": 1,
                "current_name": "Dawn",
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:pause-circle-outline",
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
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:play-circle-outline",
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
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:play-circle-outline",
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
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:play-circle-outline",
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
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:play-circle-outline",
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_OFF,
            {
                "status": "off",
                "current_zone": None,
                "current_schedule": None,
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:stop-circle-outline",
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
                "next_start": mk_local("2023-11-16 17:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 2,
                "next_name": "Dusk",
                "icon": "mdi:stop-circle-outline",
            },
        )
        exam.check_iu_entity(
            "c1_s2",
            STATE_OFF,
            {
                "status": "off",
                "current_zone": None,
                "current_schedule": None,
                "next_start": mk_local("2023-11-17 06:10:00"),
                "next_duration": "0:27:00",
                "next_schedule": 1,
                "next_name": "Morning",
                "icon": "mdi:stop-circle-outline",
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
                "next_start": mk_local("2023-11-16 06:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 1,
                "next_name": "Dawn",
                "icon": "mdi:stop-circle-outline",
                "friendly_name": "Seq 1",
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
                "next_schedule": None,
                "icon": "mdi:stop-circle-outline",
                "friendly_name": "Seq 2",
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
                "next_start": mk_local("2023-11-16 06:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 1,
                "next_name": "Dawn",
                "icon": "mdi:stop-circle-outline",
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
                "next_schedule": None,
                "icon": "mdi:circle-off-outline",
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
                "next_start": mk_local("2023-11-16 06:05:00"),
                "next_duration": "0:38:00",
                "next_schedule": 1,
                "next_name": "Dawn",
                "icon": "mdi:stop-circle-outline",
                "friendly_name": "Seq 1",
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
                "next_schedule": None,
                "icon": "mdi:timer-outline",
                "friendly_name": "Seq 2",
            },
        )
        await exam.finish_test()

        exam.check_summary()
