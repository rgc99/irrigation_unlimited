"""Test irrigation_unlimited switches."""

# pylint: disable=unused-import
import homeassistant.core as ha
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
    STATE_CLOSED,
    STATE_OPEN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_CLOSE_VALVE,
    SERVICE_OPEN_VALVE,
    Platform,
)
import homeassistant.util.dt as dt
from tests.iu_test_support import IUExam
from pytest_homeassistant_custom_component.common import async_mock_service

IUExam.quiet_mode()


# pylint: disable=unused-argument
async def test_switches(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test related switch entities."""

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


async def test_switch_types(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test related switch entities."""

    async with IUExam(hass, "test_switch_types.yaml") as exam:

        zs0 = exam.coordinator.controllers[0].zones[0]._switch

        # Test HA generic (switch, light) turn_off, turn_on
        switch_entity_id = f"{Platform.SWITCH}.test_switch"
        hass.states.async_set(switch_entity_id, STATE_OFF)
        ha_off_calls = async_mock_service(hass, ha.DOMAIN, SERVICE_TURN_OFF)
        ha_on_calls = async_mock_service(hass, ha.DOMAIN, SERVICE_TURN_ON)

        zs0._switch_entity_id = [switch_entity_id]
        await exam.begin_test(1)
        await exam.run_until("2021-01-04 06:05:15")
        hass.states.async_set(switch_entity_id, STATE_ON)
        await exam.run_until("2021-01-04 06:15:15")
        hass.states.async_set(switch_entity_id, STATE_OFF)
        await exam.finish_test()

        assert len(ha_off_calls) == 1
        call = ha_off_calls[0]
        assert call.domain == ha.DOMAIN
        assert call.service == SERVICE_TURN_OFF
        assert call.data == {"entity_id": switch_entity_id}

        assert len(ha_on_calls) == 1
        call = ha_on_calls[0]
        assert call.domain == ha.DOMAIN
        assert call.service == SERVICE_TURN_ON
        assert call.data == {"entity_id": switch_entity_id}

        # Test valve platform
        valve_entity_id = f"{Platform.VALVE}.test_valve"
        hass.states.async_set(valve_entity_id, STATE_CLOSED)
        valve_off_calls = async_mock_service(hass, Platform.VALVE, SERVICE_CLOSE_VALVE)
        valve_on_calls = async_mock_service(hass, Platform.VALVE, SERVICE_OPEN_VALVE)

        zs0._switch_entity_id = [valve_entity_id]
        await exam.begin_test(2)
        await exam.run_until("2021-01-04 06:05:15")
        hass.states.async_set(valve_entity_id, STATE_OPEN)
        await exam.run_until("2021-01-04 06:15:15")
        hass.states.async_set(valve_entity_id, STATE_CLOSED)
        await exam.finish_test()

        assert len(valve_off_calls) == 1
        call = valve_off_calls[0]
        assert call.domain == Platform.VALVE
        assert call.service == SERVICE_CLOSE_VALVE
        assert call.data == {"entity_id": valve_entity_id}

        assert len(valve_on_calls) == 1
        call = valve_on_calls[0]
        assert call.domain == Platform.VALVE
        assert call.service == SERVICE_OPEN_VALVE
        assert call.data == {"entity_id": valve_entity_id}

        # Test cover platform
        cover_entity_id = f"{Platform.COVER}.test_cover"
        hass.states.async_set(cover_entity_id, STATE_CLOSED)
        cover_off_calls = async_mock_service(hass, Platform.COVER, SERVICE_CLOSE_COVER)
        cover_on_calls = async_mock_service(hass, Platform.COVER, SERVICE_OPEN_COVER)

        zs0._switch_entity_id = [cover_entity_id]
        await exam.begin_test(3)
        await exam.run_until("2021-01-04 06:05:15")
        hass.states.async_set(cover_entity_id, STATE_OPEN)
        await exam.run_until("2021-01-04 06:15:15")
        hass.states.async_set(cover_entity_id, STATE_CLOSED)
        await exam.finish_test()

        assert len(cover_off_calls) == 1
        call = cover_off_calls[0]
        assert call.domain == Platform.COVER
        assert call.service == SERVICE_CLOSE_COVER
        assert call.data == {"entity_id": cover_entity_id}

        assert len(valve_on_calls) == 1
        call = cover_on_calls[0]
        assert call.domain == Platform.COVER
        assert call.service == SERVICE_OPEN_COVER
        assert call.data == {"entity_id": cover_entity_id}

        # Mixed entity domains
        zs0._switch_entity_id = [switch_entity_id, valve_entity_id, cover_entity_id]
        await exam.begin_test(4)
        await exam.run_until("2021-01-04 06:05:15")
        hass.states.async_set(switch_entity_id, STATE_ON)
        hass.states.async_set(valve_entity_id, STATE_OPEN)
        hass.states.async_set(cover_entity_id, STATE_OPEN)
        await exam.run_until("2021-01-04 06:15:15")
        hass.states.async_set(switch_entity_id, STATE_OFF)
        hass.states.async_set(valve_entity_id, STATE_CLOSED)
        hass.states.async_set(cover_entity_id, STATE_CLOSED)
        await exam.finish_test()

        assert len(ha_off_calls) == 2
        assert len(ha_on_calls) == 2
        assert len(valve_off_calls) == 2
        assert len(valve_on_calls) == 2
        assert len(cover_off_calls) == 2
        assert len(cover_on_calls) == 2

        exam.check_summary()
