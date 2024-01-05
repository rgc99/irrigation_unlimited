"""irrigation_unlimited service suspend tester"""
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_SUSPEND,
)
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


# pylint: disable=unused-argument,too-many-statements
async def test_service_sequence_suspend_by_controller(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test suspend service call on sequences."""

    async with IUExam(hass, "service_suspend_sequence.yaml") as exam:
        await exam.begin_test(1)
        await exam.run_for("01:00:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "for": "24:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.run_for("01:00:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "until": "2021-01-06 06:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "until": "2021-01-06 06:00",
            },
        )
        await exam.run_until("2021-01-05 06:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "reset": None,
            },
        )
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.run_for("01:00:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 1,
                "for": "24:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(5)
        await exam.run_for("01:00:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 1,
                "until": "2021-01-06 06:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(6)
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 1,
                "until": "2021-01-06 06:00",
            },
        )
        await exam.run_until("2021-01-05 06:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 1,
                "reset": None,
            },
        )
        await exam.finish_test()

        exam.check_summary()


async def test_service_sequence_suspend_by_sequence(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test suspend service call on sequences."""

    async with IUExam(hass, "service_suspend_sequence.yaml") as exam:
        await exam.begin_test(1)
        await exam.run_for("01:00:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "for": "24:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.run_for("01:00:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "until": "2021-01-06 06:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "until": "2021-01-06 06:00",
            },
        )
        await exam.run_until("2021-01-05 06:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "reset": None,
            },
        )
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.run_for("01:00:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "zones": 1,
                "for": "24:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(5)
        await exam.run_for("01:00:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "zones": 1,
                "until": "2021-01-06 06:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(6)
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "zones": 1,
                "until": "2021-01-06 06:00",
            },
        )
        await exam.run_until("2021-01-05 06:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "zones": 1,
                "reset": None,
            },
        )
        await exam.finish_test()

        exam.check_summary()
