"""Test irrigation_unlimited timing operations."""
import pytest
import glob
import logging
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

# Shh, quiet now.
logging.basicConfig(level=logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("homeassistant.core").setLevel(logging.WARNING)
logging.getLogger("homeassistant.components.recorder").setLevel(logging.WARNING)
logging.getLogger("pytest_homeassistant_custom_component.common").setLevel(
    logging.WARNING
)


def check_summary(full_path: str, coordinator: IUCoordinator):
    assert (
        coordinator.tester.total_events
        == coordinator.tester.total_checks
        == coordinator.tester.total_results
    )
    assert coordinator.tester.total_errors == 0
    print(
        "Finished: {0}; tests: {1}; events: {2}; checks: {3}; errors: {4}; time: {5:.2f}s".format(
            full_path,
            coordinator.tester.total_tests,
            coordinator.tester.total_events,
            coordinator.tester.total_checks,
            coordinator.tester.total_errors,
            coordinator.tester.total_time,
        )
    )
    return


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

        for t in range(coordinator.tester.total_tests):
            next_time = coordinator.start_test(t + 1)
            interval = coordinator.track_interval()
            while coordinator.tester.is_testing:
                coordinator.timer(next_time)
                next_time += interval

        check_summary(fname, coordinator)
