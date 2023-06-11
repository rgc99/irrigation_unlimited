"""irrigation_unlimited model test template"""
# pylint: disable=unused-import
import homeassistant.core as ha
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_model(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test negative times on controller preamble & postamble and sequence delay."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_negative_delay.yaml") as exam:
        await exam.run_all()
        exam.check_summary()
