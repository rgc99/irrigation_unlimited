"""Test irrigation_unlimited finalise"""
from asyncio import sleep
import homeassistant.core as ha
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


# pylint: disable=unused-argument
async def test_finalise(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test finialise."""

    async with IUExam(hass, "test_finalise.yaml") as exam:
        await exam.begin_test(1)
        await exam.run_for("00:14:00")
        hass.stop()
        await sleep(1)
        assert exam.coordinator.finalised is True
        await exam.finish_test()
        exam.check_summary()
