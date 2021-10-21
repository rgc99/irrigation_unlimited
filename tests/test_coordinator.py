"""Test irrigation_unlimited coordinator"""
# pylint: disable=unused-import
import pytest
import homeassistant.core as ha
from homeassistant.config import (
    load_yaml_config_file,
    async_process_ha_core_config,
)
from homeassistant.setup import async_setup_component

from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
)
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    COORDINATOR,
)
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA
from tests.iu_test_support import (
    begin_test,
    check_summary,
    finish_test,
    quiet_mode,
    test_config_dir,
)

quiet_mode()


async def test_config(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test out coordinator functionality."""
    # pylint: disable=unused-argument

    full_path = test_config_dir + "test_coordinator.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    if ha.DOMAIN in config:
        await async_process_ha_core_config(hass, config[ha.DOMAIN])
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    for test in range(coordinator.tester.total_tests):
        start_time = await begin_test(test + 1, coordinator)
        await finish_test(hass, coordinator, start_time, True)

    check_summary(full_path, coordinator)
