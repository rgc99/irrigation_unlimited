"""irrigation_unlimited module to test for edge cases"""

# pylint: disable=unused-import
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    EVENT_FINISH,
    SERVICE_TIME_ADJUST,
)
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_edge_case_1(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """This test adjusts the time on a sequence to zero right after switching
    off the last zone but the controller is still in postamble mode"""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_edge_case_1.yaml") as exam:

        async def handle_event(event: ha.Event):
            await exam.call(
                SERVICE_TIME_ADJUST,
                {
                    "actual": "0:00:00",
                    "entity_id": ["binary_sensor.irrigation_unlimited_c1_s1"],
                },
            )

        hass.bus.async_listen(f"{DOMAIN}_{EVENT_FINISH}", handle_event)
        await exam.run_test(1)
        exam.check_summary()

        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "reset": None,
                "entity_id": ["binary_sensor.irrigation_unlimited_c1_s1"],
            },
        )

    async with IUExam(hass, "test_edge_case_1.yaml") as exam:
        """Repeat above but use timing"""

        await exam.begin_test(1)
        await exam.run_until("2025-09-02 05:04:00")
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "actual": "0:00:00",
                "entity_id": ["binary_sensor.irrigation_unlimited_c1_s1"],
            },
        )
        await exam.finish_test()
        exam.check_summary()
