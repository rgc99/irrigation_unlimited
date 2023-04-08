"""Test integration_unlimited template calls."""
import homeassistant.core as ha
from tests.iu_test_support import (
    IUExam,
)
from custom_components.irrigation_unlimited.const import (
    SERVICE_MANUAL_RUN,
    SERVICE_TIME_ADJUST,
)

IUExam.quiet_mode()

# pylint: disable=unused-argument
# pylint: disable=too-many-statements
async def test_template_manual_run(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test manual_run service call using templates."""

    async with IUExam(hass, "test_template.yaml") as exam:

        async def set_dummy_value(value: str):
            await hass.services.async_call(
                "input_text",
                "set_value",
                {"entity_id": "input_text.dummy_text_1", "value": value},
                True,
            )

        await exam.load_component("homeassistant")
        await exam.load_component("input_text")

        await set_dummy_value("00:10")
        await exam.begin_test(1)
        await exam.run_until("2021-01-04 06:00:29")
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "time": "{{ states('input_text.dummy_text_1') | default('00:00') }}",
            },
        )
        await exam.finish_test()

        await set_dummy_value("00:10")
        await exam.begin_test(2)
        await exam.run_until("2021-01-04 08:00:29")
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "time": "{{ states('input_text.dummy_text_1') | default('00:00') }}",
            },
        )
        await exam.finish_test()

        await set_dummy_value("00:21")
        await exam.begin_test(3)
        await exam.run_until("2021-01-04 06:00:29")
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c2_m",
                "time": "{{ states('input_text.dummy_text_1') | default('00:00') }}",
                "sequence_id": 1,
            },
        )
        await exam.finish_test()

        await set_dummy_value("50")
        await exam.begin_test(4)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z2",
                "percentage": "{{ states('input_text.dummy_text_1') | float(100) }}",
            },
        )
        await exam.finish_test()

        await set_dummy_value("50")
        await exam.begin_test(5)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c2_m",
                "sequence_id": 1,
                "percentage": "{{ states('input_text.dummy_text_1') | float(100) }}",
            },
        )
        await exam.finish_test()

        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c2_m",
                "sequence_id": 1,
                "reset": None,
            },
        )

        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z2",
                "reset": None,
            },
        )

        exam.check_summary()
