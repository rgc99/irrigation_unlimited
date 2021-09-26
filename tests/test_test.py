"""Test irrigation_unlimited tester"""
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


async def test_test_1(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test the testing unit. Parameter show_log=False"""

    full_path = test_config_dir + "test_test_1.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    if ha.DOMAIN in config:
        await async_process_ha_core_config(hass, config[ha.DOMAIN])
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    start_time = await begin_test(1, coordinator)
    with pytest.raises(AssertionError, match="Failed test 1, errors not zero"):
        await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(2, coordinator)
    with pytest.raises(AssertionError, match="Failed test 2, missing event"):
        await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(3, coordinator)
    with pytest.raises(AssertionError, match="Failed test 3, extra event"):
        await finish_test(hass, coordinator, start_time, True)

    with pytest.raises(AssertionError, match="Failed summary results"):
        check_summary(full_path, coordinator)


async def test_test_2(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test the testing unit. Parameter show_log=True"""

    full_path = test_config_dir + "test_test_2.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    if ha.DOMAIN in config:
        await async_process_ha_core_config(hass, config[ha.DOMAIN])
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    start_time = await begin_test(1, coordinator)
    with pytest.raises(AssertionError, match="Failed test 1, errors not zero"):
        await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(2, coordinator)
    with pytest.raises(AssertionError, match="Failed test 2, missing event"):
        await finish_test(hass, coordinator, start_time, True)

    start_time = await begin_test(3, coordinator)
    with pytest.raises(AssertionError, match="Failed test 3, extra event"):
        await finish_test(hass, coordinator, start_time, True)

    with pytest.raises(AssertionError, match="Failed summary results"):
        check_summary(full_path, coordinator)
