"""Constants for irrigation_unlimited."""
# Base component constants
NAME = "Irrigation Unlimited"
DOMAIN = "irrigation_unlimited"
DOMAIN_DATA = f"{DOMAIN}_data"
COORDINATOR = "coordinator"
COMPONENT = "component"
VERSION = "2021.9.0"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/rgc99/irrigation_unlimited/issues"

# Icons
ICON = "mdi:valve"
ICON_ON = "mdi:valve-open"
ICON_OFF = "mdi:valve-closed"
ICON_DISABLED = "mdi:circle-off-outline"
ICON_BLOCKED = "mdi:alert-octagon-outline"
ICON_CONTROLLER_ON = "mdi:water"
ICON_CONTROLLER_OFF = "mdi:water-off"
ICON_CONTROLLER_PAUSED = "mdi:pause-circle-outline"

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
CONF_SPEED = "speed"
CONF_START = "start"
CONF_END = "end"
CONF_TIMES = "times"
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
CONF_SHOW = "show"
CONF_CONFIG = "config"
CONF_TIMELINE = "timeline"
CONF_ZONE_ID = "zone_id"
CONF_SEQUENCE_ID = "sequence_id"
CONF_SEQUENCES = "sequences"
CONF_ALL_ZONES_CONFIG = "all_zones_config"
CONF_REFRESH_INTERVAL = "refresh_interval"
CONF_INDEX = "index"
CONF_RESULTS = "results"
CONF_OUTPUT_EVENTS = "output_events"
CONF_SHOW_LOG = "show_log"
CONF_AUTOPLAY = "autoplay"
CONF_FUTURE_SPAN = "future_span"
CONF_ANCHOR = "anchor"
CONF_START = "start"
CONF_FINISH = "finish"

# Defaults
DEFAULT_NAME = DOMAIN
DEFAULT_GRANULATITY = 60
DEFAULT_TEST_SPEED = 1.0
DEFAULT_REFRESH_INTERVAL = 30

# Services
SERVICE_ENABLE = "enable"
SERVICE_DISABLE = "disable"
SERVICE_TOGGLE = "toggle"
SERVICE_CANCEL = "cancel"
SERVICE_TIME_ADJUST = "adjust_time"
SERVICE_MANUAL_RUN = "manual_run"

# Status
STATUS_DISABLED = "disabled"
STATUS_BLOCKED = "blocked"
STATUS_INITIALISING = "initialising"
STATUS_PAUSED = "paused"

# Attributes
ATTR_ENABLED = "enabled"
ATTR_STATUS = "status"
ATTR_INDEX = "index"

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
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
