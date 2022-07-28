"""irrigation_unlimited clock tester"""
import asyncio
from datetime import datetime
import homeassistant.core as ha
from tests.iu_test_support import IUExam, mk_local

IUExam.quiet_mode()


async def test_clock(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test the IUClock class."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_clock.yaml") as exam:

        # Wait to go into testing mode
        while not exam.coordinator.tester.is_testing:
            await asyncio.sleep(1)

        # Now wait for the test to finish
        while exam.coordinator.tester.is_testing:
            await asyncio.sleep(1)

        # Convert tick_log to virtual time
        tick_log: list[datetime] = []
        test = exam.coordinator.tester.last_test
        for atime in exam.coordinator.clock.tick_log:
            tick_log.append(test.virtual_time(atime))

        assert tick_log == [
            mk_local("2021-01-04 06:30:00"),
            mk_local("2021-01-04 06:27:00"),
            mk_local("2021-01-04 06:26:40"),
            mk_local("2021-01-04 06:26:20"),
            mk_local("2021-01-04 06:26:00"),
            mk_local("2021-01-04 06:25:40"),
            mk_local("2021-01-04 06:25:20"),
            mk_local("2021-01-04 06:25:00"),
            mk_local("2021-01-04 06:24:40"),
            mk_local("2021-01-04 06:24:20"),
            mk_local("2021-01-04 06:24:00"),
            mk_local("2021-01-04 06:23:40"),
            mk_local("2021-01-04 06:23:20"),
            mk_local("2021-01-04 06:23:00"),
            mk_local("2021-01-04 06:22:40"),
            mk_local("2021-01-04 06:22:20"),
            mk_local("2021-01-04 06:22:00"),
            mk_local("2021-01-04 06:21:40"),
            mk_local("2021-01-04 06:21:20"),
            mk_local("2021-01-04 06:21:00"),
            mk_local("2021-01-04 06:20:40"),
            mk_local("2021-01-04 06:20:20"),
            mk_local("2021-01-04 06:20:00"),
            mk_local("2021-01-04 06:19:40"),
            mk_local("2021-01-04 06:19:20"),
            mk_local("2021-01-04 06:19:00"),
            mk_local("2021-01-04 06:18:40"),
            mk_local("2021-01-04 06:18:20"),
            mk_local("2021-01-04 06:18:00"),
            mk_local("2021-01-04 06:17:40"),
            mk_local("2021-01-04 06:17:20"),
            mk_local("2021-01-04 06:17:00"),
            mk_local("2021-01-04 06:16:40"),
            mk_local("2021-01-04 06:16:20"),
            mk_local("2021-01-04 06:16:00"),
            mk_local("2021-01-04 06:15:40"),
            mk_local("2021-01-04 06:15:20"),
            mk_local("2021-01-04 06:15:00"),
            mk_local("2021-01-04 06:14:40"),
            mk_local("2021-01-04 06:14:20"),
            mk_local("2021-01-04 06:14:00"),
            mk_local("2021-01-04 06:13:40"),
            mk_local("2021-01-04 06:13:20"),
            mk_local("2021-01-04 06:13:00"),
            mk_local("2021-01-04 06:12:00"),
            mk_local("2021-01-04 06:11:40"),
            mk_local("2021-01-04 06:11:20"),
            mk_local("2021-01-04 06:11:00"),
            mk_local("2021-01-04 06:10:40"),
            mk_local("2021-01-04 06:10:20"),
            mk_local("2021-01-04 06:10:00"),
            mk_local("2021-01-04 06:09:40"),
            mk_local("2021-01-04 06:09:20"),
            mk_local("2021-01-04 06:09:00"),
            mk_local("2021-01-04 06:08:40"),
            mk_local("2021-01-04 06:08:20"),
            mk_local("2021-01-04 06:08:00"),
            mk_local("2021-01-04 06:07:40"),
            mk_local("2021-01-04 06:07:20"),
            mk_local("2021-01-04 06:07:00"),
            mk_local("2021-01-04 06:06:40"),
            mk_local("2021-01-04 06:06:20"),
            mk_local("2021-01-04 06:06:00"),
            mk_local("2021-01-04 06:05:40"),
            mk_local("2021-01-04 06:05:20"),
            mk_local("2021-01-04 06:05:00"),
            mk_local("2021-01-04 06:04:40"),
            mk_local("2021-01-04 06:04:20"),
            mk_local("2021-01-04 06:04:00"),
            mk_local("2021-01-04 06:00:00"),
        ]

        exam.check_summary()
