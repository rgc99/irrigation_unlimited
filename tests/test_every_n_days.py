"""Test irrigation_unlimited every Nth day scheduler"""
# pylint: disable=unused-import
import homeassistant.core as ha
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_cron(hass: ha.HomeAssistant, skip_history):
    """Test the every Nth day scheduler"""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_every_n_days.yaml") as exam:
        await exam.run_all()
        exam.check_summary()
