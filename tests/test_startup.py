"""irrigation_unlimited model test template"""
import homeassistant.core as ha
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_startup(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test startup while sequence is running."""
    # pylint: disable=unused-argument

    # Start an examination
    async with IUExam(hass, "test_startup.yaml") as exam:

        await exam.run_all()
        exam.check_summary()
