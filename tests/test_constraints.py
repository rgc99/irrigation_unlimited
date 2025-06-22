"""irrigation_unlimited model test template"""
# pylint: disable=unused-import
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_TIME_ADJUST,
)
from tests.iu_test_support import IUExam

IUExam.quiet_mode()

async def test_constraints(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test IUZone constraints."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_constraints.yaml") as exam:
        await exam.run_test(1)
        await exam.run_test(2)
        await exam.run_test(3)
        await exam.run_test(4)
        await exam.run_test(5)

        exam.check_summary()
