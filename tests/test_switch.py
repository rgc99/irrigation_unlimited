"""Test irrigation_unlimited switches."""
# pylint: disable=unused-import
from datetime import timedelta, datetime
import homeassistant.core as ha
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
)
import homeassistant.util.dt as dt
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_switches(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test related switch entities."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_switch.yaml") as exam:

        await exam.load_component("homeassistant")
        await exam.load_component("input_boolean")

        # Check switches are in the correct state
        assert hass.states.is_state("input_boolean.dummy_switch_c1_m", STATE_ON) is True
        assert (
            hass.states.is_state("input_boolean.dummy_switch_c1_z1", STATE_OFF) is True
        )
        assert (
            hass.states.is_state("input_boolean.dummy_switch_c1_z2", STATE_OFF) is True
        )
        assert (
            hass.states.is_state("input_boolean.dummy_switch_c1_z3", STATE_ON) is True
        )
        assert (
            hass.states.is_state("input_boolean.dummy_switch_c1_z4", STATE_ON) is True
        )

        exam.coordinator.timer(dt.utcnow())
        await hass.async_block_till_done()

        # Check switches have been reset
        assert (
            hass.states.is_state("input_boolean.dummy_switch_c1_m", STATE_OFF) is True
        )
        assert (
            hass.states.is_state("input_boolean.dummy_switch_c1_z1", STATE_OFF) is True
        )
        assert (
            hass.states.is_state("input_boolean.dummy_switch_c1_z2", STATE_OFF) is True
        )
        assert (
            hass.states.is_state("input_boolean.dummy_switch_c1_z3", STATE_OFF) is True
        )
        assert (
            hass.states.is_state("input_boolean.dummy_switch_c1_z4", STATE_OFF) is True
        )
