"""Test irrigation_unlimited timing operations."""
import pytest
import voluptuous as vol
import homeassistant.core as ha

from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    CONF_CONTROLLERS,
    CONF_ZONES,
)
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA


MOCK_CONFIG_BAD_1 = {DOMAIN: {CONF_CONTROLLERS: []}}
MOCK_CONFIG_BAD_2 = {DOMAIN: {CONF_CONTROLLERS: [{CONF_ZONES: []}]}}


async def test_init(hass: ha.HomeAssistant):
    """Test init module."""

    with pytest.raises(vol.MultipleInvalid, match="Must have at least one entry for*"):
        # No controller configured
        CONFIG_SCHEMA(MOCK_CONFIG_BAD_1)

        # No zone configured
        CONFIG_SCHEMA(MOCK_CONFIG_BAD_2)
