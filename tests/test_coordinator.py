"""Test irrigation_unlimited coordinator"""
# pylint: disable=unused-import
import homeassistant.core as ha
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_config(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test out coordinator functionality."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_coordinator.yaml") as exam:
        await exam.run_all()
        exam.check_summary()
