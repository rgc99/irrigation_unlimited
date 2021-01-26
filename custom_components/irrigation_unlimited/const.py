"""Constants for irrigation_unlimited."""
# Base component constants
NAME = "Irrigation Unlimited"
DOMAIN = "irrigation_unlimited"
DOMAIN_DATA = f"{DOMAIN}_data"
COORDINATOR = "coordinator"
COMPONENT = "component"
VERSION = "0.0.1"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/custom-components/irrigation_unlimited/issues"

# Icons
ICON = "mdi:valve"

# Platforms
BINARY_SENSOR = "binary_sensor"
PLATFORMS = [BINARY_SENSOR]

# Configuration and options
CONF_ENABLED = "enabled"
CONF_CONTROLLERS = "controllers"
CONF_ZONES = "zones"
CONF_SCHEDULES = "schedules"
CONF_SUN = "sun"
CONF_TIME = "time"
CONF_DURATION = "duration"
CONF_PREAMBLE = "preamble"
CONF_POSTAMBLE = "postamble"
CONF_TESTING = "testing"
CONF_TEST_SPEED = "test_speed"
CONF_TEST_START = "start"
CONF_TEST_END = "end"
CONF_TEST_TIMES = "test_times"
CONF_GRANULARITY = "granularity"
CONF_PERCENTAGE = "percentage"
CONF_ACTUAL = "actual"
CONF_INCREASE = "increase"
CONF_DECREASE = "decrease"
CONF_RESET = "reset"
CONF_MINIMUM = "minimum"
CONF_MAXIMUM = "maximum"
CONF_MONTH = "month"
CONF_DAY = "day"
CONF_ODD = "odd"
CONF_EVEN = "even"

# Defaults
DEFAULT_NAME = DOMAIN
DEFAULT_GRANULATITY = 60
DEFAULT_TEST_SPEED = 1.0

MONTHS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]

STARTUP_MESSAGE = f"""
{NAME} Version: {VERSION}
If you have any issues with this you need to open an issue here: {ISSUE_URL}
"""
