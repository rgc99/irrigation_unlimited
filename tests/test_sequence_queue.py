"""irrigation_unlimited test sequence queue"""
import datetime
import zoneinfo
import homeassistant.core as ha
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_fill_and_drain(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test sequence queue class."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_sequence_queue.yaml") as exam:
        await exam.begin_test(1)
        assert exam.coordinator.controllers[0].sequences[0].runs.as_list() == [
            {
                "index": 0,
                "name": "Seq 1",
                "enabled": True,
                "suspended": None,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "start": datetime.datetime(
                    2023, 11, 6, 6, 5, tzinfo=zoneinfo.ZoneInfo(key="Australia/Sydney")
                ),
                "duration": 2160,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
            {
                "index": 0,
                "name": "Seq 1",
                "enabled": True,
                "suspended": None,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "start": datetime.datetime(
                    2023, 11, 7, 6, 5, tzinfo=zoneinfo.ZoneInfo(key="Australia/Sydney")
                ),
                "duration": 2160,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
            {
                "index": 0,
                "name": "Seq 1",
                "enabled": True,
                "suspended": None,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "start": datetime.datetime(
                    2023, 11, 8, 6, 5, tzinfo=zoneinfo.ZoneInfo(key="Australia/Sydney")
                ),
                "duration": 2160,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
        ]

        await exam.run_until("2023-11-06 06:59:00")
        assert exam.coordinator.controllers[0].sequences[0].runs.as_list() == [
            {
                "index": 0,
                "name": "Seq 1",
                "enabled": True,
                "suspended": None,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "start": datetime.datetime(
                    2023, 11, 7, 6, 5, tzinfo=zoneinfo.ZoneInfo(key="Australia/Sydney")
                ),
                "duration": 2160,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
            {
                "index": 0,
                "name": "Seq 1",
                "enabled": True,
                "suspended": None,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "start": datetime.datetime(
                    2023, 11, 8, 6, 5, tzinfo=zoneinfo.ZoneInfo(key="Australia/Sydney")
                ),
                "duration": 2160,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 1080,
                        "adjustment": "",
                        "zone_ids": ["4"],
                    },
                ],
            },
            {
                "index": 0,
                "name": "Seq 1",
                "enabled": True,
                "suspended": None,
                "status": "off",
                "icon": "mdi:stop-circle-outline",
                "start": datetime.datetime(
                    2023, 11, 9, 6, 5, tzinfo=zoneinfo.ZoneInfo(key="Australia/Sydney")
                ),
                "duration": 2160,
                "adjustment": "",
                "schedule": {"index": 0, "name": "Schedule 1"},
                "zones": [
                    {
                        "index": 0,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 360,
                        "adjustment": "",
                        "zone_ids": ["1"],
                    },
                    {
                        "index": 1,
                        "enabled": True,
                        "suspended": None,
                        "status": "off",
                        "icon": "mdi:stop-circle-outline",
                        "duration": 720,
                        "adjustment": "",
                        "zone_ids": ["2", "3"],
                    },
                    {
                        "index": 2,
                        "enabled": True,
                        "suspended": None,
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
        exam.check_summary()
