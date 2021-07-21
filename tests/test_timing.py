"""Test irrigation_unlimited timing operations."""
from unittest.mock import patch
import pytest
import glob
import asyncio
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
from custom_components.irrigation_unlimited.const import DOMAIN, COORDINATOR
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA


@pytest.fixture(name="skip_setup")
def skip_setup():
    with patch(
        "custom_components.irrigation_unlimited.IUCoordinator._is_setup",
        return_value=True,
    ):
        yield


@pytest.fixture(name="skip_dependencies")
def skip_dep():
    with patch("homeassistant.loader.Integration.dependencies", return_value=[]):
        yield


@pytest.fixture(name="skip_history", autouse=True)
def skip_history():
    """Skip history calls"""
    with patch(
        "homeassistant.components.recorder.history.state_changes_during_period",
        return_value=[],
    ):
        yield


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
                await coordinator._async_timer(next_time)
                next_time += interval

        check_summary(fname, coordinator)


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
    await asyncio.sleep(duration.total_seconds())

    check_summary(full_path, coordinator)
