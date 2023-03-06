"""Test irrigation_unlimited entity operations."""
from unittest.mock import patch
import homeassistant.core as ha
from homeassistant.helpers.entity_component import EntityComponent
from custom_components.irrigation_unlimited.binary_sensor import (
    find_platform,
    async_reload_platform,
)
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    COORDINATOR,
    COMPONENT,
)
from tests.iu_test_support import (
    IUExam,
)

IUExam.quiet_mode()


# pylint: disable=unused-argument
async def test_component_deregister(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test entity deregister routines."""
    async with IUExam(hass, "test_skeleton.yaml") as exam:
        assert exam.coordinator.component is not None
        component: EntityComponent = hass.data[DOMAIN][COMPONENT]
        await component.async_remove_entity(f"{DOMAIN}.{COORDINATOR}")
        assert exam.coordinator.component is None


async def test_component_dispatch(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test coordinator dispatch routines."""
    async with IUExam(hass, "test_skeleton.yaml") as exam:
        exam.coordinator.component.dispatch("", ha.ServiceCall(DOMAIN, "DUMMY", {}))


async def test_reload_platform(
    hass: ha.HomeAssistant,
    skip_dependencies,
    skip_history,
):
    """Test coordinator reload."""
    async with IUExam(hass, "test_skeleton.yaml") as exam:
        assert find_platform(hass, "dummy") is None
        assert find_platform(hass, "binary_sensor") is not None
        component: EntityComponent = hass.data[DOMAIN][COMPONENT]
        with patch(
            "custom_components.irrigation_unlimited.binary_sensor.find_platform"
        ) as mock:
            mock.return_value = None
            assert await async_reload_platform(component, exam.coordinator) is False
