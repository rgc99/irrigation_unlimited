"""Test irrigation_unlimited history."""
from unittest.mock import patch
from datetime import datetime
import pytest
import homeassistant.core as ha
from homeassistant.config import load_yaml_config_file
from homeassistant.setup import async_setup_component

from custom_components.irrigation_unlimited.const import COORDINATOR, DOMAIN
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA
from custom_components.irrigation_unlimited.irrigation_unlimited import IUCoordinator
from tests.iu_test_support import quiet_mode, TEST_CONFIG_DIR

quiet_mode()


@pytest.fixture(name="mock_state_z1_none")
def mock_state_z1_none():
    """Patch HA with no entity history"""
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        mock.return_value = None
        yield


@pytest.fixture(name="mock_state_z1_enabled")
def mock_state_z1_enabled():
    """Patch HA history with entity in enabled state"""
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        idx = "binary_sensor.irrigation_unlimited_c1_z1"
        mock.return_value = ha.State(
            idx,
            "on",
            {"enabled": True},
            datetime.fromisoformat("2021-01-04 04:30:00+00:00"),
        )
        yield


@pytest.fixture(name="mock_state_z1_disabled")
def mock_state_z1_disabled():
    """Patch HA history with entity in disabled state"""
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        idx = "binary_sensor.irrigation_unlimited_c1_z1"
        mock.return_value = ha.State(
            idx,
            "on",
            {"enabled": False},
            datetime.fromisoformat("2021-01-04 04:30:00+00:00"),
        )
        yield


@pytest.fixture(name="mock_state_coordinator")
def mock_state_coordinator():
    """Patch HA history"""
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        # pylint: disable=line-too-long
        dct = {
            "configuration": '{"controllers": [{"index": 0, "name": "Fundos", "state": "off", "enabled": true, "icon": "mdi:water-off", "status": "off", "zones": [{"index": 0, "name": "Gramado", "state": "off", "enabled": true, "icon": "mdi:valve-closed", "zone_id": "1", "status": "off", "adjustment": "%50.0", "current_duration": "", "schedules": []}, {"index": 1, "name": "Lateral", "state": "off", "enabled": true, "icon": "mdi:valve-closed", "zone_id": "2", "status": "off", "adjustment": "", "current_duration": "", "schedules": []}, {"index": 2, "name": "Corredor", "state": "off", "enabled": true, "icon": "mdi:valve-closed", "zone_id": "3", "status": "off", "adjustment": "", "current_duration": "", "schedules": []}, {"index": 3, "name": "Horta", "state": "off", "enabled": false, "icon": "mdi:circle-off-outline", "zone_id": "4", "status": "disabled", "adjustment": "", "current_duration": "", "schedules": []}], "sequences": [{"index": 0, "name": "Multi zone", "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "default_duration": "600", "default_delay": "20", "duration_factor": 0.24848484848484848, "total_delay": "40", "total_duration": "1650", "adjusted_duration": "410", "current_duration": "", "adjustment": "%25.0", "sequence_zones": [{"index": 0, "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "delay": "20", "base_duration": "600", "adjusted_duration": "450", "final_duration": "110", "zones": "1", "current_duration": "", "adjustment": "%75.0"}, {"index": 1, "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "delay": "20", "base_duration": "600", "adjusted_duration": "600", "final_duration": "150", "zones": "2", "current_duration": "", "adjustment": ""}, {"index": 2, "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "delay": "20", "base_duration": "600", "adjusted_duration": "600", "final_duration": "150", "zones": "3", "current_duration": "", "adjustment": ""}]}, {"index": 1, "name": "Outer zone", "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "default_duration": "900", "default_delay": "10", "duration_factor": 1.0, "total_delay": "10", "total_duration": "1800", "adjusted_duration": "1800", "current_duration": "", "adjustment": "", "sequence_zones": [{"index": 0, "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "delay": "10", "base_duration": "900", "adjusted_duration": "900", "final_duration": "900", "zones": "1", "current_duration": "", "adjustment": ""}, {"index": 1, "state": "off", "enabled": false, "icon": "mdi:circle-off-outline", "status": "disabled", "delay": "", "base_duration": "", "adjusted_duration": "", "final_duration": "", "zones": "2", "current_duration": "", "adjustment": ""}, {"index": 2, "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "delay": "10", "base_duration": "900", "adjusted_duration": "900", "final_duration": "900", "zones": "3,4", "current_duration": "", "adjustment": ""}]}, {"index": 2, "name": "Later zone", "state": "off", "enabled": false, "icon": "mdi:circle-off-outline", "status": "disabled", "default_duration": "720", "default_delay": "10", "duration_factor": 1.0, "total_delay": "", "total_duration": "", "adjusted_duration": "", "current_duration": "", "adjustment": "", "sequence_zones": [{"index": 0, "state": "off", "enabled": true, "icon": "mdi:alert-octagon-outline", "status": "blocked", "delay": "", "base_duration": "", "adjusted_duration": "", "final_duration": "", "zones": "3", "current_duration": "", "adjustment": ""}, {"index": 1, "state": "off", "enabled": true, "icon": "mdi:alert-octagon-outline", "status": "blocked", "delay": "", "base_duration": "", "adjusted_duration": "", "final_duration": "", "zones": "2", "current_duration": "", "adjustment": ""}, {"index": 2, "state": "off", "enabled": true, "icon": "mdi:alert-octagon-outline", "status": "blocked", "delay": "", "base_duration": "", "adjusted_duration": "", "final_duration": "", "zones": "1", "current_duration": "", "adjustment": ""}]}]}]}'
        }
        mock.return_value = ha.State(
            "irrigation_unlimited.coordinator",
            "ok",
            dct,
            datetime.fromisoformat("2021-01-04 04:30:00+00:00"),
        )
        yield


@pytest.fixture(name="mock_state_attributes_none")
def mock_state_attribute_none():
    """Patch HA history"""
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        mock.return_value = ha.State(
            "irrigation_unlimited.coordinator",
            "ok",
            None,
            datetime.fromisoformat("2021-01-04 04:30:00+00:00"),
        )
        yield


@pytest.fixture(name="mock_state_attributes_empty")
def mock_state_attribute_empty():
    """Patch HA history"""
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        mock.return_value = ha.State(
            "irrigation_unlimited.coordinator",
            "ok",
            {},
            datetime.fromisoformat("2021-01-04 04:30:00+00:00"),
        )
        yield


@pytest.fixture(name="mock_state_configuration_none")
def mock_state_configuration_none():
    """Patch HA history"""
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        dct = {"configuration": None}
        mock.return_value = ha.State(
            "irrigation_unlimited.coordinator",
            "ok",
            dct,
            datetime.fromisoformat("2021-01-04 04:30:00+00:00"),
        )
        yield


@pytest.fixture(name="mock_state_configuration_empty")
def mock_state_configuration_empty():
    """Patch HA history"""
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        dct = {"configuration": '{"dummy": "dummy"}'}
        mock.return_value = ha.State(
            "irrigation_unlimited.coordinator",
            "ok",
            dct,
            datetime.fromisoformat("2021-01-04 04:30:00+00:00"),
        )
        yield


# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
async def test_restore_none(
    hass: ha.HomeAssistant, skip_dependencies, skip_history, mock_state_z1_none
):
    """Test restoring entity with no history"""

    full_path = TEST_CONFIG_DIR + "test_restore_entity.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert sta.attributes["enabled"] is True


async def test_restore_enabled(
    hass: ha.HomeAssistant, skip_dependencies, skip_history, mock_state_z1_enabled
):
    """Test restoring entity in enabled state"""

    full_path = TEST_CONFIG_DIR + "test_restore_entity.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert sta.attributes["enabled"] is True


async def test_restore_disabled(
    hass: ha.HomeAssistant, skip_dependencies, skip_history, mock_state_z1_disabled
):
    """Test restoring entity in disabled state"""

    full_path = TEST_CONFIG_DIR + "test_restore_entity.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert sta.attributes["enabled"] is False


async def test_restore_coordinator(
    hass: ha.HomeAssistant, skip_dependencies, skip_history, mock_state_coordinator
):
    """Test restoring coordinator"""

    full_path = TEST_CONFIG_DIR + "test_restore_entity_sequence.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]
    assert str(coordinator.controllers[0].zones[0].adjustment) == "%50.0"
    assert str(coordinator.controllers[0].sequences[0].adjustment) == "%25.0"
    assert str(coordinator.controllers[0].sequences[0].zones[0].adjustment) == "%75.0"

    assert coordinator.controllers[0].zones[3].enabled is False
    sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
    assert sta.attributes["enabled"] is False

    assert coordinator.controllers[0].sequences[2].enabled is False
    assert coordinator.controllers[0].sequences[2].status == "disabled"
    assert coordinator.controllers[0].sequences[2].zones[0].status == "blocked"
    assert coordinator.controllers[0].sequences[2].zones[1].status == "blocked"
    assert coordinator.controllers[0].sequences[2].zones[2].status == "blocked"

    assert coordinator.controllers[0].sequences[1].zones[1].enabled is False
    assert coordinator.controllers[0].sequences[1].zones[1].status == "disabled"


async def test_restore_attributes_none(
    hass: ha.HomeAssistant, skip_dependencies, skip_history, mock_state_attributes_none
):
    """Test restoring coordinator with no attributes"""

    full_path = TEST_CONFIG_DIR + "test_restore_entity_sequence.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()


async def test_restore_attributes_empty(
    hass: ha.HomeAssistant, skip_dependencies, skip_history, mock_state_attributes_empty
):
    """Test restoring coordinator with empty attributes"""

    full_path = TEST_CONFIG_DIR + "test_restore_entity_sequence.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()


async def test_restore_configuration_none(
    hass: ha.HomeAssistant,
    skip_dependencies,
    skip_history,
    mock_state_configuration_none,
):
    """Test restoring coordinator with configuration None"""

    full_path = TEST_CONFIG_DIR + "test_restore_entity_sequence.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()


async def test_restore_configuration_empty(
    hass: ha.HomeAssistant,
    skip_dependencies,
    skip_history,
    mock_state_configuration_empty,
):
    """Test restoring coordinator with configuration None"""

    full_path = TEST_CONFIG_DIR + "test_restore_entity_sequence.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
