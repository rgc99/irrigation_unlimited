"""irrigation_unlimited service skip tester"""
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_SKIP,
)
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_service_sequence_skip(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test service calls to sequence"""
    # pylint: disable=unused-argument

    async with IUExam(hass, "service_sequence_skip.yaml") as exam:
        await exam.run_test(1)

        await exam.begin_test(2)
        await exam.run_until("2023-11-28 06:07")
        await exam.call(
            SERVICE_SKIP,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.run_until("2023-11-28 06:16:30")
        await exam.call(
            SERVICE_SKIP,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.run_until("2023-11-28 06:21:30")
        await exam.call(
            SERVICE_SKIP,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(5)
        await exam.run_until("2023-11-28 06:43:30")
        await exam.call(
            SERVICE_SKIP,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(6)
        await exam.run_until("2023-11-28 06:46:00")
        await exam.call(
            SERVICE_SKIP,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        exam.check_summary()
