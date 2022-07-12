"""irrigation_unlimited test with no schedules"""
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_MANUAL_RUN,
)
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_sequence_no_schedule(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Model IUExam class."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_no_schedule.yaml") as exam:

        # Check loading and nothing happends
        await exam.run_test(1)

        # Zone manual run
        await exam.begin_test(2)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "time": "00:10",
            },
        )
        await exam.finish_test()

        # Sequence manual run
        await exam.begin_test(3)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "time": "00:38",
                "sequence_id": 1,
            },
        )
        await exam.finish_test()

        exam.check_summary()
