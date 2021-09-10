"""Test integration_unlimited reload service calls."""
from unittest.mock import patch

import pytest
import homeassistant.core as ha
from homeassistant.config import load_yaml_config_file
from homeassistant.setup import async_setup_component
from homeassistant.const import SERVICE_RELOAD
from tests.const import MOCK_CONFIG
from tests.iu_test_support import (
    no_check,
    quiet_mode,
    begin_test,
    run_for,
    run_for_1_tick,
    run_until,
    finish_test,
    test_config_dir,
    check_summary,
)
from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
)
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    COORDINATOR,
)
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA

quiet_mode()


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
    # pylint: disable=unused-variable
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


async def test_service_reload_extend_shrink(
    hass: ha.HomeAssistant,
    skip_start,
    skip_dependencies,
    skip_history,
):
    """Test reload service call expanding and reducing entities."""

    await async_setup_component(hass, DOMAIN, CONFIG_SCHEMA(MOCK_CONFIG))
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    full_path = test_config_dir + "service_reload_2.yaml"
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

    full_path = test_config_dir + "service_reload_3.yaml"
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

    full_path = test_config_dir + "service_reload_1.yaml"
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
