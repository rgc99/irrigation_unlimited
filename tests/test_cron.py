"""Test irrigation_unlimited cron time interface"""
# pylint: disable=unused-import
from unittest.mock import patch
import homeassistant.core as ha
from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IULogger,
)
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_cron(hass: ha.HomeAssistant, skip_history):
    """Test the cron interface of the scheduler"""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_cron.yaml") as exam:
        await exam.run_all()
        exam.check_summary()

    async with IUExam(hass, "test_cron_error.yaml") as exam:
        with patch.object(IULogger, "_format") as mock:
            await exam.run_all()
            exam.check_summary()

            assert sum(1 for call in mock.call_args_list if call.args[1] == "CRON") == 2
