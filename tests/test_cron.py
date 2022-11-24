"""Test irrigation_unlimited cron time interface"""
# pylint: disable=unused-import
import homeassistant.core as ha
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_cron(hass: ha.HomeAssistant, skip_history):
    """Test the cron interface of the scheduler"""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_cron.yaml") as exam:
        await exam.run_all()
        exam.check_summary()
