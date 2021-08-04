"""Test irrigation_unlimited history."""
from unittest.mock import patch
from datetime import datetime
import pytest
import homeassistant.core as ha
from homeassistant.config import load_yaml_config_file
from homeassistant.setup import async_setup_component

from custom_components.irrigation_unlimited.const import DOMAIN
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA
from tests.iu_test_support import quiet_mode, test_config_dir

quiet_mode()


@pytest.fixture(name="mock_state_z1_none")
def mock_state_z1_none():
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        mock.return_value = None
        yield


@pytest.fixture(name="mock_state_z1_enabled")
def mock_state_z1_enabled():
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        id = "binary_sensor.irrigation_unlimited_c1_z1"
        mock.return_value = ha.State(
            id,
            "on",
            {"enabled": True},
            datetime.fromisoformat("2021-01-04 04:30:00+00:00"),
        )
        yield


@pytest.fixture(name="mock_state_z1_disabled")
def mock_state_z1_disabled():
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        id = "binary_sensor.irrigation_unlimited_c1_z1"
        mock.return_value = ha.State(
            id,
            "on",
            {"enabled": False},
            datetime.fromisoformat("2021-01-04 04:30:00+00:00"),
        )
        yield


async def test_restore_none(hass: ha.HomeAssistant, mock_state_z1_none):

    full_path = test_config_dir + "test_restore_entity.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.attributes["enabled"] == True


async def test_restore_enabled(hass: ha.HomeAssistant, mock_state_z1_enabled):

    full_path = test_config_dir + "test_restore_entity.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.attributes["enabled"] == True


async def test_restore_disabled(hass: ha.HomeAssistant, mock_state_z1_disabled):

    full_path = test_config_dir + "test_restore_entity.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.attributes["enabled"] == False
