"""Test irrigation_unlimited timing operations."""
from unittest.mock import patch
import pytest
import glob
import homeassistant.core as ha
from homeassistant.util import dt as dt_util
from homeassistant.config import (
    load_yaml_config_file,
    async_process_ha_core_config,
)
from homeassistant.setup import async_setup_component

from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
)
from custom_components.irrigation_unlimited.const import DOMAIN
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA


@pytest.fixture(name="skip_setup")
def skip_setup():
    with patch(
        "custom_components.irrigation_unlimited.IUCoordinator._is_setup",
        return_value=True,
    ):
        yield


test_config_dir = "tests/configs/"


async def test_timings(hass: ha.HomeAssistant, skip_setup):
    """Test timings. Process all the configuration files in the
    test_config directory matching timing_*.yaml and check the results."""

    for fname in glob.glob(test_config_dir + "timing_*.yaml"):
        print(f"Processing: {fname}")
        config = CONFIG_SCHEMA(load_yaml_config_file(fname))

        if ha.DOMAIN in config:
            await async_process_ha_core_config(hass, config[ha.DOMAIN])
        coordinator = IUCoordinator(hass).load(config[DOMAIN])

        next_time = dt_util.utcnow()
        interval = coordinator.track_interval()
        while not coordinator.tester._initialised or coordinator.tester.is_testing:
            await coordinator._async_timer(next_time)
            next_time += interval

        assert (
            coordinator.tester.total_events
            == coordinator.tester.total_checks
            == coordinator.tester.total_results
        )
        assert coordinator.tester.total_errors == 0
        print(
            "Finished: {0}; events: {1}; checks: {2}; errors: {3}; time: {4:.2f}s".format(
                fname,
                coordinator.tester.total_events,
                coordinator.tester.total_checks,
                coordinator.tester.total_errors,
                coordinator.tester.total_time,
            )
        )
