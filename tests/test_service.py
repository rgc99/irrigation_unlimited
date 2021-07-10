"""Test integration_blueprint setup process."""
from unittest.mock import patch

import pytest
from datetime import datetime, timedelta
import logging
import homeassistant.core as ha
from homeassistant.config import load_yaml_config_file
from homeassistant.setup import async_setup_component
from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
)
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    COORDINATOR,
    SERVICE_CANCEL,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_MANUAL_RUN,
    SERVICE_TIME_ADJUST,
    SERVICE_TOGGLE,
)
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA


@pytest.fixture(name="skip_start")
def skip_start():
    with patch(
        "custom_components.irrigation_unlimited.IUCoordinator.start",
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


# Shh, quiet now.
logging.basicConfig(level=logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("homeassistant.core").setLevel(logging.WARNING)
logging.getLogger("homeassistant.components.recorder").setLevel(logging.WARNING)
logging.getLogger("pytest_homeassistant_custom_component.common").setLevel(
    logging.WARNING
)
_LOGGER = logging.getLogger(__name__)


async def begin_test(
    hass: ha.HomeAssistant,
    coordinator: IUCoordinator,
    next_time: datetime,
    how_long: timedelta,
    block: bool,
) -> datetime:

    test = coordinator.tester.current_test
    _LOGGER.debug("Starting test %s", test.name)

    start_time = next_time
    interval = coordinator.track_interval()
    next_time += interval
    while coordinator.tester.is_testing and (
        how_long is None or next_time - start_time < how_long
    ):
        await coordinator._async_timer(next_time)
        if block:
            await hass.async_block_till_done()
        next_time += interval
    return next_time


async def finish_test(
    hass: ha.HomeAssistant, coordinator: IUCoordinator, next_time: datetime, block: bool
):
    interval = coordinator.track_interval()
    while coordinator.tester.is_testing:
        await coordinator._async_timer(next_time)
        if block:
            await hass.async_block_till_done()
        next_time += interval

    test = coordinator.tester.last_test
    assert test.errors == 0, f"Failed test {test.index + 1}"
    assert test.events == test.total_results, f"Failed test {test.index + 1}"
    _LOGGER.debug("Finished test %s time: %.2fs", test.name, test.test_time)
    return


async def run_test(
    hass: ha.HomeAssistant,
    coordinator: IUCoordinator,
    next_time: datetime,
    block: bool,
):
    next_time = await begin_test(hass, coordinator, next_time, None, block)
    await finish_test(hass, coordinator, next_time, block)

    return


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


async def test_service_adjust_time(
    hass: ha.HomeAssistant, skip_start, skip_dependencies, skip_history
):
    """Test adjust_time service call."""
    full_path = test_config_dir + "service_adjust_time.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    next_time = coordinator.start_test(1)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "percentage": 50},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(2)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "percentage": 200},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(3)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "percentage": 0},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(4)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "actual": "00:30"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(5)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "increase": "00:05"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(6)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "decrease": "00:05"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(7)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "reset": None},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(8)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 50},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(9)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 200},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(10)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 0},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(11)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "actual": "00:30"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(12)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "increase": "00:05"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(13)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "decrease": "00:05"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(14)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "reset": None},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    check_summary(full_path, coordinator)


async def test_service_enable_disable(
    hass: ha.HomeAssistant, skip_start, skip_dependencies, skip_history
):
    """Test enable/disable service call."""

    full_path = test_config_dir + "service_enable_disable.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    # Zone 1 off
    next_time = coordinator.start_test(1)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_DISABLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    # Zone 1 on
    next_time = coordinator.start_test(2)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ENABLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    # Zone 1 off, zone 2 on
    next_time = coordinator.start_test(3)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    # Double toggle: zone 1 on, zone 2 off
    next_time = coordinator.start_test(4)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        True,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z2"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    # All off
    next_time = coordinator.start_test(5)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    # All back on
    next_time = coordinator.start_test(6)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        True,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z2"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    # Controller 1 off
    next_time = coordinator.start_test(7)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_DISABLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    # Controller 1 off, zone 1 on, zone 2 off
    next_time = coordinator.start_test(8)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ENABLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        True,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_DISABLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z2"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    # Controller 1 on, zone 1 still on, zone 2 still off
    next_time = coordinator.start_test(9)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ENABLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    # Toggle controller 1
    next_time = coordinator.start_test(10)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    # Toggle controller 1 & zone 2 (All back on)
    next_time = coordinator.start_test(11)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        True,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z2"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    check_summary(full_path, coordinator)


async def test_service_manual_run(
    hass: ha.HomeAssistant, skip_start, skip_dependencies, skip_history
):
    """Test manual_run service call."""

    full_path = test_config_dir + "service_manual_run.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    next_time = coordinator.start_test(1)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_MANUAL_RUN,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "time": "00:10"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(2)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_MANUAL_RUN,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "time": "00:10"},
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    next_time = coordinator.start_test(3)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_MANUAL_RUN,
        {
            "entity_id": "binary_sensor.irrigation_unlimited_c2_m",
            "time": "00:20",
            "sequence_id": 1,
        },
        True,
    )
    await run_test(hass, coordinator, next_time, True)

    check_summary(full_path, coordinator)


async def test_service_cancel(
    hass: ha.HomeAssistant, skip_start, skip_dependencies, skip_history
):
    """Test cancel service call."""

    full_path = test_config_dir + "service_cancel.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    start_time = coordinator.start_test(1)
    next_time = await begin_test(
        hass, coordinator, start_time, timedelta(minutes=12), True
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CANCEL,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        True,
    )
    await finish_test(hass, coordinator, next_time, True)

    start_time = coordinator.start_test(2)
    next_time = await begin_test(
        hass, coordinator, start_time, timedelta(minutes=12), True
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CANCEL,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        True,
    )
    await finish_test(hass, coordinator, next_time, True)

    check_summary(full_path, coordinator)
