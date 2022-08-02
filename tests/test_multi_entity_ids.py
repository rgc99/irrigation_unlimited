"""Test irrigation_unlimited switches."""
# pylint: disable=unused-import
from datetime import timedelta, datetime
import homeassistant.core as ha
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
)
import homeassistant.util.dt as dt
from tests.iu_test_support import IUExam, mk_local

IUExam.quiet_mode()


async def test_multi_entity_ids(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test turning on multiple entities."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_multi_entity_ids.yaml") as exam:

        await exam.load_component("homeassistant")
        await exam.load_component("input_boolean")

        await exam.begin_test(1)

        assert hass.states.is_state("input_boolean.dummy_s1", STATE_OFF) is True
        assert hass.states.is_state("input_boolean.dummy_s2", STATE_OFF) is True
        assert hass.states.is_state("input_boolean.dummy_s3", STATE_OFF) is True
        assert hass.states.is_state("input_boolean.dummy_s4", STATE_OFF) is True
        assert hass.states.is_state("input_boolean.dummy_s5", STATE_OFF) is True

        await exam.run_until(mk_local("2021-01-04 06:07"))
        assert hass.states.is_state("input_boolean.dummy_s1", STATE_ON) is True
        assert hass.states.is_state("input_boolean.dummy_s2", STATE_ON) is True
        assert hass.states.is_state("input_boolean.dummy_s3", STATE_ON) is True
        assert hass.states.is_state("input_boolean.dummy_s4", STATE_OFF) is True
        assert hass.states.is_state("input_boolean.dummy_s5", STATE_OFF) is True

        await exam.run_until(mk_local("2021-01-04 06:12"))
        assert hass.states.is_state("input_boolean.dummy_s1", STATE_ON) is True
        assert hass.states.is_state("input_boolean.dummy_s2", STATE_ON) is True
        assert hass.states.is_state("input_boolean.dummy_s3", STATE_ON) is True
        assert hass.states.is_state("input_boolean.dummy_s4", STATE_ON) is True
        assert hass.states.is_state("input_boolean.dummy_s5", STATE_ON) is True

        await exam.run_until(mk_local("2021-01-04 06:17"))
        assert hass.states.is_state("input_boolean.dummy_s1", STATE_ON) is True
        assert hass.states.is_state("input_boolean.dummy_s2", STATE_OFF) is True
        assert hass.states.is_state("input_boolean.dummy_s3", STATE_OFF) is True
        assert hass.states.is_state("input_boolean.dummy_s4", STATE_ON) is True
        assert hass.states.is_state("input_boolean.dummy_s5", STATE_ON) is True

        await exam.run_until(mk_local("2021-01-04 06:25"))
        assert hass.states.is_state("input_boolean.dummy_s1", STATE_OFF) is True
        assert hass.states.is_state("input_boolean.dummy_s2", STATE_OFF) is True
        assert hass.states.is_state("input_boolean.dummy_s3", STATE_OFF) is True
        assert hass.states.is_state("input_boolean.dummy_s4", STATE_OFF) is True
        assert hass.states.is_state("input_boolean.dummy_s5", STATE_OFF) is True

        await exam.finish_test()

        exam.check_summary()
