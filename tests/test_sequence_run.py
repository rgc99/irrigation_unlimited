"""irrigation_unlimited test unit for IUSequenceRun object"""
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    SERVICE_DISABLE,
    SERVICE_TIME_ADJUST,
)
from custom_components.irrigation_unlimited.irrigation_unlimited import IUSequenceRun
from tests.iu_test_support import IUExam, mk_local

IUExam.quiet_mode()


async def test_sequence_run(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test IUSequenceRun class."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_sequence_run.yaml") as exam:

        # Basic check
        assert len(exam.coordinator.controllers[0].sequence_status()) == 2

        # Check skeleton and dict match
        assert set(exam.coordinator.controllers[0].sequence_status()[0].keys()) == set(
            IUSequenceRun.skeleton(exam.coordinator.controllers[0].sequences[0]).keys()
        )
        assert set(
            exam.coordinator.controllers[0].sequence_status()[0]["zones"][0].keys()
        ) == set(
            IUSequenceRun.skeleton(exam.coordinator.controllers[0].sequences[0])[
                "zones"
            ][0].keys()
        )
        assert set(
            exam.coordinator.controllers[0].sequence_status()[0]["schedule"].keys()
        ) == set(
            IUSequenceRun.skeleton(exam.coordinator.controllers[0].sequences[0])[
                "schedule"
            ].keys()
        )

        # Check normal operation
        await exam.begin_test(1)
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_m").attributes[
            "sequence_status"
        ] == [
            {
                "index": 0,
                "enabled": True,
                "name": "Seq 1",
                "start": mk_local("2021-01-04 06:05"),
                "duration": 2160,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "adjustment": "",
                "schedule": {
                    "index": 0,
                    "name": "Schedule 1",
                },
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
            {
                "index": 1,
                "enabled": True,
                "name": "Seq 2",
                "start": mk_local("2021-01-04 06:10"),
                "duration": 2160,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "adjustment": "",
                "schedule": {
                    "index": 0,
                    "name": "Schedule 1",
                },
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
        ]

        await exam.run_until("2021-01-04 06:07")
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_m").attributes[
            "sequence_status"
        ] == [
            {
                "index": 0,
                "name": "Seq 1",
                "enabled": True,
                "status": "on",
                "icon": "mdi:play-circle-outline",
                "start": mk_local("2021-01-04 06:05"),
                "duration": 2160,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
            {
                "index": 1,
                "name": "Seq 2",
                "enabled": True,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "start": mk_local("2021-01-04 06:10"),
                "duration": 2160,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
        ]

        await exam.run_until("2021-01-04 06:14")
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_m").attributes[
            "sequence_status"
        ] == [
            {
                "index": 0,
                "name": "Seq 1",
                "enabled": True,
                "status": "on",
                "icon": "mdi:play-circle-outline",
                "start": mk_local("2021-01-04 06:05"),
                "duration": 1800,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
            {
                "index": 1,
                "name": "Seq 2",
                "enabled": True,
                "status": "on",
                "icon": "mdi:play-circle-outline",
                "start": mk_local("2021-01-04 06:10"),
                "duration": 2160,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
        ]

        await exam.run_until("2021-01-04 06:20")
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_m").attributes[
            "sequence_status"
        ] == [
            {
                "index": 0,
                "name": "Seq 1",
                "enabled": True,
                "status": "on",
                "icon": "mdi:play-circle-outline",
                "start": mk_local("2021-01-04 06:05"),
                "duration": 1800,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
            {
                "index": 1,
                "name": "Seq 2",
                "enabled": True,
                "status": "on",
                "icon": "mdi:play-circle-outline",
                "start": mk_local("2021-01-04 06:10"),
                "duration": 1800,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
        ]

        await exam.run_until("2021-01-04 06:27")
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_m").attributes[
            "sequence_status"
        ] == [
            {
                "index": 0,
                "name": "Seq 1",
                "enabled": True,
                "status": "on",
                "icon": "mdi:play-circle-outline",
                "start": mk_local("2021-01-04 06:05"),
                "duration": 1080,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
            {
                "index": 1,
                "name": "Seq 2",
                "enabled": True,
                "status": "on",
                "icon": "mdi:play-circle-outline",
                "start": mk_local("2021-01-04 06:10"),
                "duration": 1800,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
        ]

        await exam.run_until("2021-01-04 06:40")
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_m").attributes[
            "sequence_status"
        ] == [
            {
                "index": 0,
                "name": "Seq 1",
                "enabled": True,
                "status": "on",
                "icon": "mdi:play-circle-outline",
                "start": mk_local("2021-01-04 06:05"),
                "duration": 1080,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
            {
                "index": 1,
                "name": "Seq 2",
                "enabled": True,
                "status": "on",
                "icon": "mdi:play-circle-outline",
                "start": mk_local("2021-01-04 06:10"),
                "duration": 1080,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "on",
                        "icon": "mdi:play-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
        ]

        await exam.run_until("2021-01-04 06:50")
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_m").attributes[
            "sequence_status"
        ] == [
            {
                "index": 0,
                "name": "Seq 1",
                "enabled": True,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "start": mk_local("2021-01-05 06:05"),
                "duration": 2160,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
            {
                "index": 1,
                "name": "Seq 2",
                "enabled": True,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "start": mk_local("2021-01-05 06:10"),
                "duration": 2160,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
        ]

        await exam.finish_test()

        # Sequence 2 adjustment = %0.0
        await exam.begin_test(2)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
                "percentage": 0,
            },
            True,
        )
        assert exam.coordinator.controllers[0].sequence_status() == [
            {
                "index": 0,
                "enabled": True,
                "name": "Seq 1",
                "start": mk_local("2021-01-04 06:05"),
                "duration": 2160,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "adjustment": "",
                "schedule": {
                    "index": 0,
                    "name": "Schedule 1",
                },
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
            {
                "index": 1,
                "enabled": True,
                "name": "Seq 2",
                "start": mk_local("2021-01-04 06:10"),
                "duration": 0,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "adjustment": "%0.0",
                "schedule": {
                    "index": 0,
                    "name": "Schedule 1",
                },
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
        ]
        await exam.finish_test()

        # Sequence 2 disabled
        await exam.begin_test(3)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
            },
            True,
        )
        assert exam.coordinator.controllers[0].sequence_status() == [
            {
                "index": 0,
                "enabled": True,
                "name": "Seq 1",
                "start": mk_local("2021-01-04 06:05"),
                "duration": 2160,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "adjustment": "",
                "schedule": {
                    "index": 0,
                    "name": "Schedule 1",
                },
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
            {
                "index": 1,
                "enabled": False,
                "name": "Seq 2",
                "start": None,
                "duration": 0,
                "status": "disabled",
                "icon": "mdi:circle-off-outline",
                "adjustment": "%0.0",
                "schedule": {
                    "index": None,
                    "name": None,
                },
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "status": "blocked",
                        "icon": "mdi:alert-octagon-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "status": "blocked",
                        "icon": "mdi:alert-octagon-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "status": "blocked",
                        "icon": "mdi:alert-octagon-outline",
                        "duration": 0,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
        ]
        await exam.finish_test()

        exam.check_summary()
