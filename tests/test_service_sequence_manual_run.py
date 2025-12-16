"""Test Irrigation Unlimited manual run service calls."""

# pylint: disable=too-many-lines
from unittest.mock import patch
import homeassistant.core as ha
from tests.iu_test_support import (
    IUExam,
    mk_local,
)
from custom_components.irrigation_unlimited.const import (
    SERVICE_MANUAL_RUN,
    SERVICE_CANCEL,
)

IUExam.quiet_mode()


async def test_service_manual_run_sequence_by_controller(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test manual_run service call on a sequence"""

    async with IUExam(hass, "service_manual_run_sequence.yaml") as exam:
        await exam.begin_test(1)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "time": "0:20:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
            },
        )
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "time": "0:00:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
            },
        )
        await exam.run_until("2021-01-04 10:03:00")
        await exam.call(
            SERVICE_CANCEL, {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"}
        )

        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes[
            "next_start"
        ] == mk_local("2021-01-04 12:00")
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z2").attributes[
            "next_start"
        ] == mk_local("2021-01-04 12:07")
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z3").attributes[
            "next_start"
        ] == mk_local("2021-01-04 12:07")
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z4").attributes[
            "next_start"
        ] == mk_local("2021-01-04 12:20")

        await exam.finish_test()
        exam.check_summary()


async def test_service_manual_run_sequence_by_sequence(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test manual_run service call on a sequence"""

    async with IUExam(hass, "service_manual_run_sequence.yaml") as exam:
        await exam.begin_test(1)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "time": "0:20:00",
            },
        )
        assert (
            str(exam.coordinator.controllers[0].sequences[0].runs[0])
            == "status: FUTURE, start: 2021-01-04 14:01:01, end: 2021-01-04 14:21:01, schedule: Manual"
        )
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "time": "0:00:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.run_until("2021-01-04 10:03:00")
        await exam.call(
            SERVICE_CANCEL, {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"}
        )

        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes[
            "next_start"
        ] == mk_local("2021-01-04 12:00")
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z2").attributes[
            "next_start"
        ] == mk_local("2021-01-04 12:07")
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z3").attributes[
            "next_start"
        ] == mk_local("2021-01-04 12:07")
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z4").attributes[
            "next_start"
        ] == mk_local("2021-01-04 12:20")

        await exam.finish_test()
        exam.check_summary()
