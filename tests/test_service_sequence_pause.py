"""irrigation_unlimited service pause tester"""
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_PAUSE,
)
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_service_sequence_pause(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test service calls to sequence"""
    # pylint: disable=unused-argument

    async with IUExam(hass, "service_sequence_pause.yaml") as exam:
        await exam.run_test(1)

        await exam.begin_test(2)
        await exam.run_until("2023-11-28 06:10:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:20:30")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.run_until("2023-11-28 06:07")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2023-11-28 06:17")
        await exam.call(
            SERVICE_PAUSE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        exam.check_summary()
