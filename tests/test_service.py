"""Test integration_blueprint setup process."""
from unittest.mock import patch

import pytest
from datetime import datetime, timedelta
import homeassistant.core as ha
from homeassistant.config import load_yaml_config_file
from homeassistant.setup import async_setup_component
from homeassistant.const import SERVICE_RELOAD
from tests.const import MOCK_CONFIG
from tests.iu_test_support import quiet_mode, begin_test, run_for, run_until, finish_test, test_config_dir, check_summary
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

quiet_mode()

async def test_service_adjust_time(
    hass: ha.HomeAssistant, skip_start, skip_dependencies, skip_history
):
    """Test adjust_time service call."""

    full_path = test_config_dir + "service_adjust_time.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    start_time = await begin_test(1, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "percentage": 50},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(2, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "percentage": 200},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(3, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "percentage": 0},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(4, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "actual": "00:30"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(5, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "increase": "00:05"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(6, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "decrease": "00:05"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(7, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "reset": None},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(8, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {
            "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
            "percentage": 100,
            "minimum": "00:20",
        },
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(9, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {
            "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
            "percentage": 100,
            "maximum": "00:05",
        },
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(10, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 50},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(11, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 200},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(12, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 0},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(13, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "actual": "00:30"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(14, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "increase": "00:05"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(15, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "decrease": "00:05"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(16, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "reset": None},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(17, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {
            "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
            "percentage": 100,
            "minimum": "00:20",
        },
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(18, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {
            "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
            "percentage": 100,
            "maximum": "00:05",
        },
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

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
    start_time = await begin_test(1, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_DISABLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    # Zone 1 on
    start_time = await begin_test(2, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ENABLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    # Zone 1 off, zone 2 on
    start_time = await begin_test(3, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    # Double toggle: zone 1 on, zone 2 off
    start_time = await begin_test(4, coordinator)
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
    await finish_test(hass, coordinator, start_time, True)

    # All off
    start_time = await begin_test(5, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    # All back on
    start_time = await begin_test(6, coordinator)
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
    await finish_test(hass, coordinator, start_time, True)

    # Controller 1 off
    start_time = await begin_test(7, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_DISABLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    # Controller 1 off, zone 1 on, zone 2 off
    start_time = await begin_test(8, coordinator)
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
    await finish_test(hass, coordinator, start_time, True)

    # Controller 1 on, zone 1 still on, zone 2 still off
    start_time = await begin_test(9, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ENABLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    # Toggle controller 1
    start_time = await begin_test(10, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    # Toggle controller 1 & zone 2 (All back on)
    start_time = await begin_test(11, coordinator)
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
    await finish_test(hass, coordinator, start_time, True)

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

    start_time = await begin_test(1, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_MANUAL_RUN,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "time": "00:10"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(2, coordinator)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_MANUAL_RUN,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "time": "00:10"},
        True,
    )
    await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(3, coordinator)
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
    await finish_test(hass, coordinator, start_time, True)

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

    start_time = await begin_test(1, coordinator)
    next_time = await run_until(hass, coordinator, start_time, datetime.fromisoformat("2021-01-04 06:11:45+00:00"), True)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CANCEL,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        True,
    )
    await finish_test(hass, coordinator, next_time, True)

    start_time = await begin_test(2, coordinator)
    next_time = await run_until(hass, coordinator, start_time, datetime.fromisoformat("2021-01-04 06:11:45+00:00"), True)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CANCEL,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        True,
    )
    await finish_test(hass, coordinator, next_time, True)

    check_summary(full_path, coordinator)


async def test_service_reload(
    hass: ha.HomeAssistant,
    skip_start,
    skip_dependencies,
    skip_history,
):
    """Test reload service call."""

    full_path = test_config_dir + "service_reload.yaml"
    await async_setup_component(hass, DOMAIN, CONFIG_SCHEMA(MOCK_CONFIG))
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    with patch(
        "homeassistant.core.Config.path",
        return_value=full_path,
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            None,
            True,
        )

    start_time = await begin_test(1, coordinator)
    await finish_test(hass, coordinator, start_time, True)

    check_summary(full_path, coordinator)


async def test_service_reload_error(
    hass: ha.HomeAssistant,
    skip_start,
    skip_dependencies,
    skip_history,
):
    """Test reload service call on a bad config file."""

    full_path = test_config_dir + "service_reload_error.yaml"
    await async_setup_component(hass, DOMAIN, CONFIG_SCHEMA(MOCK_CONFIG))
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    with patch(
        "homeassistant.core.Config.path",
        return_value=full_path,
    ):
        with pytest.raises(KeyError, match="controllers"):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RELOAD,
                None,
                True,
            )


async def test_service_adjust_time_while_running(
    hass: ha.HomeAssistant, skip_start, skip_dependencies, skip_history
):
    """Test adjust_time service call while sequence is running."""

    full_path = test_config_dir + "service_adjust_time_while_running.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    # Start a sequence
    start_time = await begin_test(1, coordinator)
    next_time = await run_for(hass, coordinator, start_time, timedelta(minutes=28), True)
    # Hit zone 4 with adjustment midway through sequence
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_z4", "percentage": 200},
        True,
    )
    await finish_test(hass, coordinator, next_time, True)
    # Run next test which should be 200%
    start_time = await begin_test(2, coordinator)
    await finish_test(hass, coordinator, start_time, True)

    # Reset adjustments
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "reset": None},
        True,
    )

    # Start a sequence
    start_time = await begin_test(3, coordinator)
    next_time = await run_for(hass, coordinator, start_time, timedelta(minutes=28), True)
    # Hit controller with adjustment halfway through sequence
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TIME_ADJUST,
        {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 200},
        True,
    )
    await finish_test(hass, coordinator, next_time, True)
    # Run next test which should be 200%
    start_time = await begin_test(4, coordinator)
    await finish_test(hass, coordinator, start_time, True)

    check_summary(full_path, coordinator)
