"""Test integration_unlimited reload service calls."""
from unittest.mock import patch
from datetime import datetime
import pytest
import homeassistant.core as ha
from homeassistant.setup import async_setup_component
from homeassistant.const import SERVICE_RELOAD
from tests.const import MOCK_CONFIG
from tests.iu_test_support import (
    quiet_mode,
    begin_test,
    run_until,
    finish_test,
    TEST_CONFIG_DIR,
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

# pylint: disable=unused-argument
async def test_service_reload(
    hass: ha.HomeAssistant,
    skip_start,
    skip_dependencies,
    skip_history,
):
    """Test reload service call."""

    full_path = TEST_CONFIG_DIR + "service_reload.yaml"
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

    full_path = TEST_CONFIG_DIR + "service_reload_error.yaml"
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

    full_path = TEST_CONFIG_DIR + "service_reload_2.yaml"
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

    full_path = TEST_CONFIG_DIR + "service_reload_3.yaml"
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

    full_path = TEST_CONFIG_DIR + "service_reload_1.yaml"
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


async def test_service_reload_shrink_while_on(
    hass: ha.HomeAssistant,
    skip_start,
    skip_dependencies,
    skip_history,
):
    """Test reload service call reducing entities while on."""

    await async_setup_component(hass, DOMAIN, CONFIG_SCHEMA(MOCK_CONFIG))
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    full_path = TEST_CONFIG_DIR + "service_reload_while_on.yaml"
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
    # Reload while entities are on.
    start_time = await begin_test(1, coordinator)
    await run_until(
        hass,
        coordinator,
        start_time,
        datetime.fromisoformat("2021-01-04 06:16:00+00:00"),
        True,
    )
    full_path = TEST_CONFIG_DIR + "service_reload_1.yaml"
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

    # The reload mid stream has blown away our test and results. So
    # don't attempt to finish or check results, there are none.
    # await finish_test(hass, coordinator, start_time, True)
    # check_summary(full_path, coordinator)
