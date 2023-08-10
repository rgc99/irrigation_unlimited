"""Irrigation Unlimited test for zone next_schedule attribute"""
# pylint: disable=unused-import
# pylint: disable=unused-argument
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_TIME_ADJUST,
    ATTR_NEXT_ADJUSTMENT,
)
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_next_adjustment(hass: ha.HomeAssistant, skip_history):
    """Test issue 132"""

    async with IUExam(hass, "./workshop/issue_132/configuration.yaml") as exam:
        await exam.begin_test(1)

        # Mimic restore
        await exam.run_until("2023-08-09 08:38:58")
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "percentage": 1.0,
            },
        )
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
                "percentage": 11.0,
            },
        )

        # Various service calls
        await exam.run_until("2023-08-09 08:39:30")
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "percentage": 11,
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes[ATTR_NEXT_ADJUSTMENT] == "%11.0"

        await exam.run_until("2021-08-09 08:40:42")
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
                "percentage": 0.0,
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes.get(ATTR_NEXT_ADJUSTMENT) is None

        await exam.run_until("2021-08-09 08:41:41")
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
                "reset": None,
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes[ATTR_NEXT_ADJUSTMENT] == ""

        await exam.run_until("2021-08-09 08:43:28")
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
                "percentage": 0.0,
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes.get(ATTR_NEXT_ADJUSTMENT) is None

        await exam.run_until("2021-08-09 08:44:11")
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
                "percentage": 1.0,
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes[ATTR_NEXT_ADJUSTMENT] == "%1.0"

        await exam.finish_test()
        exam.check_summary()
