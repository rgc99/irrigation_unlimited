"""Test irrigation_unlimited finalise"""
from datetime import timedelta
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
    run_for,
    TEST_CONFIG_DIR,
)

quiet_mode()

# pylint: disable=unused-argument
async def test_finalise(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test finialise."""

    full_path = TEST_CONFIG_DIR + "test_finalise.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    if ha.DOMAIN in config:
        await async_process_ha_core_config(hass, config[ha.DOMAIN])
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    start_time = await begin_test(1, coordinator)
    next_time = await run_for(
        hass, coordinator, start_time, timedelta(minutes=14), True
    )
    hass.stop()
    await finish_test(hass, coordinator, next_time, True)

    check_summary(full_path, coordinator)
