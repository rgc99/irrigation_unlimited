"""irrigation_unlimited test unit for IUSequenceRun object"""
import datetime
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    SERVICE_DISABLE,
    SERVICE_TIME_ADJUST,
)
from custom_components.irrigation_unlimited.irrigation_unlimited import IUSequenceRun
from tests.iu_test_support import IUExam

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
        await exam.run_for_1_tick()
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_m").attributes[
            "sequence_status"
        ] == [
            {
                "start": datetime.datetime(
                    2021, 1, 4, 6, 5, tzinfo=datetime.timezone.utc
                ),
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
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                    },
                ],
            },
            {
                "start": datetime.datetime(
                    2021, 1, 4, 6, 10, tzinfo=datetime.timezone.utc
                ),
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
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
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
        await exam.run_for_1_tick()
        assert exam.coordinator.controllers[0].sequence_status() == [
            {
                "start": datetime.datetime(
                    2021, 1, 4, 6, 5, tzinfo=datetime.timezone.utc
                ),
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
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                    },
                ],
            },
            {
                "start": datetime.datetime(
                    2021, 1, 4, 6, 10, tzinfo=datetime.timezone.utc
                ),
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
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 0,
                        "adjustment": "",
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
        await exam.run_for_1_tick()
        assert exam.coordinator.controllers[0].sequence_status() == [
            {
                "start": datetime.datetime(
                    2021, 1, 4, 6, 5, tzinfo=datetime.timezone.utc
                ),
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
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                    },
                    {
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                    },
                ],
            },
            {
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
                        "status": "blocked",
                        "icon": "mdi:alert-octagon-outline",
                        "duration": 0,
                        "adjustment": "",
                    },
                    {
                        "status": "blocked",
                        "icon": "mdi:alert-octagon-outline",
                        "duration": 0,
                        "adjustment": "",
                    },
                    {
                        "status": "blocked",
                        "icon": "mdi:alert-octagon-outline",
                        "duration": 0,
                        "adjustment": "",
                    },
                ],
            },
        ]
        await exam.finish_test()

        exam.check_summary()
