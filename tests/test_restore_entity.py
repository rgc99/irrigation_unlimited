"""Test irrigation_unlimited history."""
from unittest.mock import patch
from datetime import datetime
import pytest
import homeassistant.core as ha
from homeassistant.config import load_yaml_config_file
from homeassistant.setup import async_setup_component

from custom_components.irrigation_unlimited.const import DOMAIN
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA
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
