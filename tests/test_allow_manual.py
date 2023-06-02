"""irrigation_unlimited model test template"""
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_DISABLE,
    SERVICE_MANUAL_RUN,
)
from tests.iu_test_support import IUExam

IUExam.quiet_mode()

async def test_model(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Model IUExam class."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_allow_manual.yaml") as exam:

        await exam.begin_test(1)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "time": "00:10",
            },
        )
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z2",
                "time": "00:10",
            },
        )
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z3",
            },
        )
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z3",
                "time": "00:10",
            },
        )
        await exam.finish_test()

        exam.check_summary()
