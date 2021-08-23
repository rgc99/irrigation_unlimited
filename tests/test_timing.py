"""Test irrigation_unlimited timing operations."""
import pytest
import glob
import homeassistant.core as ha
from homeassistant.config import (
    load_yaml_config_file,
    async_process_ha_core_config,
)
from tests.iu_test_support import (
    begin_test,
    finish_test,
    quiet_mode,
    test_config_dir,
    check_summary,
)
from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
)
from custom_components.irrigation_unlimited.const import DOMAIN
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA

quiet_mode()


async def test_timings(hass: ha.HomeAssistant, skip_setup):
    """Test timings. Process all the configuration files in the
    test_config directory matching timing_*.yaml and check the results."""

    for fname in glob.glob(test_config_dir + "timing_*.yaml"):
        print(f"Processing: {fname}")
        config = CONFIG_SCHEMA(load_yaml_config_file(fname))
        if ha.DOMAIN in config:
            await async_process_ha_core_config(hass, config[ha.DOMAIN])
        coordinator = IUCoordinator(hass).load(config[DOMAIN])

        for t in range(coordinator.tester.total_tests):
            next_time = await begin_test(t + 1, coordinator)
            await finish_test(hass, coordinator, next_time, True)

        check_summary(fname, coordinator)
