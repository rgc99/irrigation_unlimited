"""Irrigation Unlimited run queue tests"""
# pylint: disable=unused-argument
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_ENABLE,
    SERVICE_DISABLE,
    ATTR_NEXT_NAME,
)
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_run_queue_sequence(hass: ha.HomeAssistant, skip_history):
    """Test run queue clearing and regeneration"""

    async with IUExam(hass, "test_run_queue.yaml") as exam:
        await exam.begin_test(1)
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes[ATTR_NEXT_NAME] == "Dawn"
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "sequence_id": 1},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes[ATTR_NEXT_NAME] == "Dusk"
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "sequence_id": 1},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes[ATTR_NEXT_NAME] == "Dawn"
        await exam.finish_test()

        await exam.begin_test(2)
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes[ATTR_NEXT_NAME] == "Dusk"
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "sequence_id": 2},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes[ATTR_NEXT_NAME] == "Dawn"
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "sequence_id": 2},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes[ATTR_NEXT_NAME] == "Dusk"
        await exam.finish_test()

        exam.check_summary()
