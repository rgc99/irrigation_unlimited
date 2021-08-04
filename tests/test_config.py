"""Test irrigation_unlimited user configurations. Not exactly a test
   but a place to check if configuration files are valid and possibly
   debug them."""
import pytest
import json
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
from tests.iu_test_support import quiet_mode, test_config_dir

quiet_mode()


@pytest.mark.skip
async def test_config(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test loading of a config."""

    full_path = test_config_dir + "test_config.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    if ha.DOMAIN in config:
        await async_process_ha_core_config(hass, config[ha.DOMAIN])
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]
    print(json.dumps(coordinator.as_dict(), default=str))
