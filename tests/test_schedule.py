"""Test irrigation_unlimited schedule"""
# pylint: disable=unused-import
import homeassistant.core as ha
from tests.iu_test_support import IUExam

IUExam.quiet_mode()

# pylint: disable=unused-argument


async def test_schedule(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test schedule functionality."""
    async with IUExam(hass, "test_schedule.yaml") as exam:
        await exam.run_all()
        exam.check_summary()

    async with IUExam(hass, "test_schedule_from_until.yaml") as exam:
        await exam.run_all()
        exam.check_summary()
