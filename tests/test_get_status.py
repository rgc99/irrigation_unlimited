"""irrigation_unlimited get_status test"""

# pylint: disable=unused-import
import homeassistant.core as ha
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_get_status_basic(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test the get_status service call"""
    # pylint: disable=unused-argument

    async with IUExam(hass, "service_get_status.yaml") as exam:

        await exam.begin_test(1)
        assert await hass.services.async_call(
            "irrigation_unlimited", "get_status", None, True, return_response=True
        ) == {
            "version": "1.0.1",
            "controllers": [
                {
                    "index": 0,
                    "name": "Test Controller 1",
                    "state": "off",
                    "enabled": True,
                    "suspended": None,
                    "zones": [
                        {
                            "index": 0,
                            "name": "Zone 1",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                        },
                        {
                            "index": 1,
                            "name": "Zone 2",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                        },
                        {
                            "index": 2,
                            "name": "Zone 3",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                        },
                        {
                            "index": 3,
                            "name": "Zone 4",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                        },
                    ],
                    "sequences": [
                        {
                            "index": 0,
                            "name": "Seq 1",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                            "sequence_zones": [
                                {
                                    "index": 0,
                                    "state": "off",
                                    "enabled": True,
                                    "suspended": None,
                                    "adjustment": "",
                                },
                                {
                                    "index": 1,
                                    "state": "off",
                                    "enabled": True,
                                    "suspended": None,
                                    "adjustment": "",
                                },
                                {
                                    "index": 2,
                                    "state": "off",
                                    "enabled": True,
                                    "suspended": None,
                                    "adjustment": "",
                                },
                            ],
                        },
                    ],
                }
            ],
        }

        await exam.run_until("2025-10-26 06:12:30")
        assert await hass.services.async_call(
            "irrigation_unlimited", "get_status", None, True, return_response=True
        ) == {
            "version": "1.0.1",
            "controllers": [
                {
                    "index": 0,
                    "state": "on",
                    "name": "Test Controller 1",
                    "enabled": True,
                    "suspended": None,
                    "zones": [
                        {
                            "index": 0,
                            "name": "Zone 1",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                        },
                        {
                            "index": 1,
                            "name": "Zone 2",
                            "state": "on",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                        },
                        {
                            "index": 2,
                            "name": "Zone 3",
                            "state": "on",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                        },
                        {
                            "index": 3,
                            "name": "Zone 4",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                        },
                    ],
                    "sequences": [
                        {
                            "index": 0,
                            "name": "Seq 1",
                            "state": "on",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                            "sequence_zones": [
                                {
                                    "index": 0,
                                    "state": "off",
                                    "enabled": True,
                                    "suspended": None,
                                    "adjustment": "",
                                },
                                {
                                    "index": 1,
                                    "state": "on",
                                    "enabled": True,
                                    "suspended": None,
                                    "adjustment": "",
                                },
                                {
                                    "index": 2,
                                    "state": "off",
                                    "enabled": True,
                                    "suspended": None,
                                    "adjustment": "",
                                },
                            ],
                        },
                    ],
                }
            ],
        }

        await exam.finish_test()

        exam.check_summary()


async def test_get_status_extended(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test the get_status extended service call"""
    # pylint: disable=unused-argument

    async with IUExam(hass, "service_get_status.yaml") as exam:

        await exam.begin_test(1)
        assert await hass.services.async_call(
            "irrigation_unlimited",
            "get_status",
            {"extended": True},
            True,
            return_response=True,
        ) == {
            "version": "1.0.1",
            "controllers": [
                {
                    "index": 0,
                    "state": "off",
                    "controller_id": "controller_1",
                    "entity_base": "c1_m",
                    "icon": "mdi:water-off",
                    "status": "off",
                    "name": "Test Controller 1",
                    "enabled": True,
                    "suspended": None,
                    "zones": [
                        {
                            "index": 0,
                            "name": "Zone 1",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                            "icon": "mdi:valve-closed",
                            "zone_id": "zone_1",
                            "entity_base": "c1_z1",
                            "status": "off",
                            "current_duration": 0,
                            "schedules": [],
                            "switch_entity_id": None,
                        },
                        {
                            "index": 1,
                            "name": "Zone 2",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                            "icon": "mdi:valve-closed",
                            "zone_id": "2",
                            "entity_base": "c1_z2",
                            "status": "off",
                            "current_duration": 0,
                            "schedules": [],
                            "switch_entity_id": None,
                        },
                        {
                            "index": 2,
                            "name": "Zone 3",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                            "icon": "mdi:valve-closed",
                            "zone_id": "3",
                            "entity_base": "c1_z3",
                            "status": "off",
                            "current_duration": 0,
                            "schedules": [],
                            "switch_entity_id": None,
                        },
                        {
                            "index": 3,
                            "name": "Zone 4",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                            "icon": "mdi:valve-closed",
                            "zone_id": "zone_4",
                            "entity_base": "c1_z4",
                            "status": "off",
                            "current_duration": 0,
                            "schedules": [],
                            "switch_entity_id": None,
                        },
                    ],
                    "sequences": [
                        {
                            "index": 0,
                            "name": "Seq 1",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                            "icon": "mdi:stop-circle-outline",
                            "status": "off",
                            "default_duration": 180,
                            "default_delay": 180,
                            "duration_factor": 1.0,
                            "total_delay": 360,
                            "total_duration": 540,
                            "adjusted_duration": 540,
                            "current_duration": 0,
                            "sequence_zones": [
                                {
                                    "index": 0,
                                    "state": "off",
                                    "enabled": True,
                                    "suspended": None,
                                    "adjustment": "",
                                    "icon": "mdi:stop-circle-outline",
                                    "status": "off",
                                    "delay": 180,
                                    "base_duration": 180,
                                    "adjusted_duration": 180,
                                    "final_duration": 180,
                                    "zones": [1],
                                    "current_duration": 0,
                                },
                                {
                                    "index": 1,
                                    "state": "off",
                                    "enabled": True,
                                    "suspended": None,
                                    "adjustment": "",
                                    "icon": "mdi:stop-circle-outline",
                                    "status": "off",
                                    "delay": 180,
                                    "base_duration": 180,
                                    "adjusted_duration": 180,
                                    "final_duration": 180,
                                    "zones": [2, 3],
                                    "current_duration": 0,
                                },
                                {
                                    "index": 2,
                                    "state": "off",
                                    "enabled": True,
                                    "suspended": None,
                                    "adjustment": "",
                                    "icon": "mdi:stop-circle-outline",
                                    "status": "off",
                                    "delay": 180,
                                    "base_duration": 180,
                                    "adjusted_duration": 180,
                                    "final_duration": 180,
                                    "zones": [4],
                                    "current_duration": 0,
                                },
                            ],
                            "schedules": [
                                {
                                    "time": "06:05:00",
                                    "anchor": "start",
                                    "duration": None,
                                    "name": "Schedule 1",
                                    "enabled": True,
                                },
                            ],
                        },
                    ],
                },
            ],
        }

        await exam.run_until("2025-10-26 06:12:30")
        assert await hass.services.async_call(
            "irrigation_unlimited",
            "get_status",
            {"extended": True},
            True,
            return_response=True,
        ) == {
            "version": "1.0.1",
            "controllers": [
                {
                    "index": 0,
                    "name": "Test Controller 1",
                    "enabled": True,
                    "suspended": None,
                    "zones": [
                        {
                            "index": 0,
                            "name": "Zone 1",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                            "icon": "mdi:valve-closed",
                            "zone_id": "zone_1",
                            "entity_base": "c1_z1",
                            "status": "off",
                            "current_duration": 0,
                            "schedules": [],
                            "switch_entity_id": None,
                        },
                        {
                            "index": 1,
                            "name": "Zone 2",
                            "state": "on",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                            "icon": "mdi:valve-open",
                            "zone_id": "2",
                            "entity_base": "c1_z2",
                            "status": "on",
                            "current_duration": 180,
                            "schedules": [],
                            "switch_entity_id": None,
                        },
                        {
                            "index": 2,
                            "name": "Zone 3",
                            "state": "on",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                            "icon": "mdi:valve-open",
                            "zone_id": "3",
                            "entity_base": "c1_z3",
                            "status": "on",
                            "current_duration": 180,
                            "schedules": [],
                            "switch_entity_id": None,
                        },
                        {
                            "index": 3,
                            "name": "Zone 4",
                            "state": "off",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                            "icon": "mdi:valve-closed",
                            "zone_id": "zone_4",
                            "entity_base": "c1_z4",
                            "status": "off",
                            "current_duration": 0,
                            "schedules": [],
                            "switch_entity_id": None,
                        },
                    ],
                    "sequences": [
                        {
                            "index": 0,
                            "name": "Seq 1",
                            "state": "on",
                            "enabled": True,
                            "suspended": None,
                            "adjustment": "",
                            "sequence_zones": [
                                {
                                    "index": 0,
                                    "state": "off",
                                    "enabled": True,
                                    "suspended": None,
                                    "adjustment": "",
                                    "icon": "mdi:stop-circle-outline",
                                    "status": "off",
                                    "delay": 180,
                                    "base_duration": 180,
                                    "adjusted_duration": 180,
                                    "final_duration": 180,
                                    "zones": [1],
                                    "current_duration": 180,
                                },
                                {
                                    "index": 1,
                                    "state": "on",
                                    "enabled": True,
                                    "suspended": None,
                                    "adjustment": "",
                                    "icon": "mdi:play-circle-outline",
                                    "status": "on",
                                    "delay": 180,
                                    "base_duration": 180,
                                    "adjusted_duration": 180,
                                    "final_duration": 180,
                                    "zones": [2, 3],
                                    "current_duration": 180,
                                },
                                {
                                    "index": 2,
                                    "state": "off",
                                    "enabled": True,
                                    "suspended": None,
                                    "adjustment": "",
                                    "icon": "mdi:stop-circle-outline",
                                    "status": "off",
                                    "delay": 180,
                                    "base_duration": 180,
                                    "adjusted_duration": 180,
                                    "final_duration": 180,
                                    "zones": [4],
                                    "current_duration": 180,
                                },
                            ],
                            "icon": "mdi:play-circle-outline",
                            "status": "on",
                            "default_duration": 180,
                            "default_delay": 180,
                            "duration_factor": 1.0,
                            "total_delay": 360,
                            "total_duration": 540,
                            "adjusted_duration": 540,
                            "current_duration": 900,
                            "schedules": [
                                {
                                    "time": "06:05:00",
                                    "anchor": "start",
                                    "duration": None,
                                    "name": "Schedule 1",
                                    "enabled": True,
                                },
                            ],
                        },
                    ],
                    "state": "on",
                    "controller_id": "controller_1",
                    "entity_base": "c1_m",
                    "icon": "mdi:water",
                    "status": "on",
                },
            ],
        }

        await exam.finish_test()

        exam.check_summary()
