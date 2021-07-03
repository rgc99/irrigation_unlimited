"""Constants for irrigation_unlimited tests."""
from custom_components.irrigation_unlimited.const import (
    CONF_CONTROLLERS,
    CONF_SCHEDULES,
    CONF_ZONES,
)

# Mock config data to be used across multiple tests
MOCK_CONFIG = {
    "irrigation_unlimited": {
        CONF_CONTROLLERS: [
            {CONF_ZONES: [{CONF_SCHEDULES: [{"time": "06:00", "duration": "10:00"}]}]}
        ]
    }
}
