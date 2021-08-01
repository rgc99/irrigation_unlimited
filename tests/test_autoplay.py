"""Test irrigation_unlimited autoplay operations."""
import pytest
import asyncio
import homeassistant.core as ha
from homeassistant.config import (
    load_yaml_config_file,
    async_process_ha_core_config,
)
from homeassistant.setup import async_setup_component

from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
)
from custom_components.irrigation_unlimited.const import DOMAIN, COORDINATOR
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA
from tests.iu_test_support import quiet_mode, test_config_dir, check_summary

quiet_mode()

async def test_autoplay(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test autoplay feature."""

    full_path = test_config_dir + "test_autoplay.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    if ha.DOMAIN in config:
        await async_process_ha_core_config(hass, config[ha.DOMAIN])
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    duration = coordinator.tester.total_virtual_duration
    await asyncio.sleep(duration.total_seconds() + 5) # Add a few seconds to allow tests to finish

    check_summary(full_path, coordinator)
