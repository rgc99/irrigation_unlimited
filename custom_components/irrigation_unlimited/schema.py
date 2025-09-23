"""This module holds the vaious schemas"""

from datetime import datetime, date
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_AFTER,
    CONF_BEFORE,
    CONF_NAME,
    CONF_WEEKDAY,
    CONF_REPEAT,
    CONF_DELAY,
    CONF_FOR,
    CONF_UNTIL,
)

from .const import (
    CONF_ALLOW_MANUAL,
    CONF_CLOCK,
    CONF_ENABLED,
    CONF_FINISH,
    CONF_FIXED,
    CONF_FUTURE_SPAN,
    CONF_HISTORY,
    CONF_HISTORY_REFRESH,
    CONF_HISTORY_SPAN,
    CONF_MAX_LOG_ENTRIES,
    CONF_MAXIMUM,
    CONF_MINIMUM,
    CONF_THRESHOLD,
    CONF_MODE,
    CONF_MONTH,
    CONF_DAY,
    CONF_ODD,
    CONF_EVEN,
    CONF_RENAME_ENTITIES,
    CONF_RESULTS,
    CONF_SHOW_LOG,
    CONF_AUTOPLAY,
    CONF_ANCHOR,
    CONF_SPAN,
    CONF_SYNC_SWITCHES,
    CONF_SEER,
    CONF_CONTROLLERS,
    CONF_SCHEDULES,
    CONF_ZONES,
    CONF_DURATION,
    CONF_SUN,
    CONF_TIME,
    CONF_PREAMBLE,
    CONF_POSTAMBLE,
    CONF_GRANULARITY,
    CONF_TESTING,
    CONF_SPEED,
    CONF_TIMES,
    CONF_START,
    CONF_END,
    MONTHS,
    CONF_SHOW,
    CONF_CONFIG,
    CONF_TIMELINE,
    CONF_CONTROLLER_ID,
    CONF_ZONE_ID,
    CONF_SEQUENCES,
    CONF_ALL_ZONES_CONFIG,
    CONF_REFRESH_INTERVAL,
    CONF_OUTPUT_EVENTS,
    CONF_CRON,
    CONF_EVERY_N_DAYS,
    CONF_START_N_DAYS,
    CONF_CHECK_BACK,
    CONF_RETRIES,
    CONF_RESYNC,
    CONF_STATE_ON,
    CONF_STATE_OFF,
    CONF_PERCENTAGE,
    CONF_ACTUAL,
    CONF_INCREASE,
    CONF_DECREASE,
    CONF_RESET,
    CONF_SEQUENCE_ID,
    CONF_STATES,
    CONF_SCHEDULE_ID,
    CONF_FROM,
    CONF_VOLUME,
    CONF_VOLUME_PRECISION,
    CONF_VOLUME_SCALE,
    CONF_FLOW_RATE_PRECISION,
    CONF_FLOW_RATE_SCALE,
    CONF_QUEUE,
    CONF_QUEUE_MANUAL,
    CONF_USER,
    CONF_TOGGLE,
    CONF_EXTENDED_CONFIG,
    CONF_RESTORE_FROM_ENTITY,
    CONF_READ_DELAY,
    CONF_SHOW_CONFIG,
    CONF_SHOW_SEQUENCE_STATUS,
    CONF_ENTITY_STATES,
)

IU_ID = r"^[a-z0-9]+(_[a-z0-9]+)*$"


def _list_is_not_empty(value):
    if value is None or len(value) < 1:
        raise vol.Invalid("Must have at least one entry")
    return value


def _parse_dd_mmm(value: str) -> date | None:
    """Convert a date string in dd mmm format to a date object."""
    if isinstance(value, date):
        return value
    return datetime.strptime(f"{value} {datetime.today().year}", "%d %b %Y").date()


USER_SCHEMA = vol.Schema(
    {},
    extra=vol.ALLOW_EXTRA,
)

SHOW_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CONFIG, False): cv.boolean,
        vol.Optional(CONF_TIMELINE, False): cv.boolean,
    }
)

SUN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SUN): cv.sun_event,
        vol.Optional(CONF_BEFORE): cv.positive_time_period,
        vol.Optional(CONF_AFTER): cv.positive_time_period,
    }
)

CRON_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CRON): cv.string,
    }
)

EVERY_N_DAYS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EVERY_N_DAYS): cv.positive_int,
        vol.Required(CONF_START_N_DAYS): cv.date,
    }
)

time_event = vol.Any(cv.time, SUN_SCHEMA, CRON_SCHEMA)
anchor_event = vol.Any(CONF_START, CONF_FINISH)
month_event = vol.All(cv.ensure_list, [vol.In(MONTHS)])

day_number = vol.All(vol.Coerce(int), vol.Range(min=0, max=31))
day_event = vol.Any(
    CONF_ODD, CONF_EVEN, cv.ensure_list(day_number), EVERY_N_DAYS_SCHEMA
)

SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TIME): time_event,
        vol.Required(CONF_ANCHOR, default=CONF_START): anchor_event,
        vol.Required(CONF_DURATION): cv.positive_time_period,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_SCHEDULE_ID): cv.matches_regex(IU_ID),
        vol.Optional(CONF_WEEKDAY): cv.weekdays,
        vol.Optional(CONF_MONTH): month_event,
        vol.Optional(CONF_DAY): day_event,
        vol.Optional(CONF_ENABLED): cv.boolean,
        vol.Inclusive(CONF_FROM, "span"): _parse_dd_mmm,
        vol.Inclusive(CONF_UNTIL, "span"): _parse_dd_mmm,
    }
)

SEQUENCE_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TIME): time_event,
        vol.Required(CONF_ANCHOR, default=CONF_START): anchor_event,
        vol.Optional(CONF_DURATION): cv.positive_time_period,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_SCHEDULE_ID): cv.matches_regex(IU_ID),
        vol.Optional(CONF_WEEKDAY): cv.weekdays,
        vol.Optional(CONF_MONTH): month_event,
        vol.Optional(CONF_DAY): day_event,
        vol.Optional(CONF_ENABLED): cv.boolean,
        vol.Inclusive(CONF_FROM, "span"): _parse_dd_mmm,
        vol.Inclusive(CONF_UNTIL, "span"): _parse_dd_mmm,
    }
)

LOAD_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SCHEDULE_ID): cv.matches_regex(IU_ID),
        vol.Optional(CONF_TIME): time_event,
        vol.Optional(CONF_ANCHOR): anchor_event,
        vol.Optional(CONF_DURATION): cv.positive_time_period_template,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_WEEKDAY): cv.weekdays,
        vol.Optional(CONF_MONTH): month_event,
        vol.Optional(CONF_DAY): day_event,
        vol.Optional(CONF_ENABLED): cv.boolean,
        vol.Inclusive(CONF_FROM, "span"): _parse_dd_mmm,
        vol.Inclusive(CONF_UNTIL, "span"): _parse_dd_mmm,
    }
)

CHECK_BACK_SCHEMA = vol.All(
    cv.deprecated(CONF_STATE_ON),
    cv.deprecated(CONF_STATE_OFF),
    vol.Schema(
        {
            vol.Optional(CONF_STATES): vol.Any("none", "all", "on", "off"),
            vol.Optional(CONF_DELAY): cv.positive_int,
            vol.Optional(CONF_RETRIES): cv.positive_int,
            vol.Optional(CONF_RESYNC): cv.boolean,
            vol.Optional(CONF_STATE_ON): cv.string,  # Deprecated
            vol.Optional(CONF_STATE_OFF): cv.string,  # Deprecated
            vol.Optional(CONF_ENTITY_ID): cv.entity_id,
            vol.Optional(CONF_TOGGLE): cv.boolean,
        }
    ),
)

VOLUME_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Optional(CONF_VOLUME_PRECISION): cv.positive_int,
        vol.Optional(CONF_VOLUME_SCALE): cv.positive_float,
        vol.Optional(CONF_FLOW_RATE_PRECISION): cv.positive_int,
        vol.Optional(CONF_FLOW_RATE_SCALE): cv.positive_float,
    }
)

ZONE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SCHEDULES): vol.All(cv.ensure_list, [SCHEDULE_SCHEMA]),
        vol.Optional(CONF_ZONE_ID): cv.matches_regex(IU_ID),
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_ENTITY_ID): cv.entity_ids,
        vol.Optional(CONF_ENTITY_STATES): vol.Any("none", "all", "on", "off"),
        vol.Optional(CONF_ENABLED): cv.boolean,
        vol.Optional(CONF_ALLOW_MANUAL): cv.boolean,
        vol.Optional(CONF_MINIMUM): cv.positive_time_period,
        vol.Optional(CONF_MAXIMUM): cv.positive_time_period,
        vol.Optional(CONF_THRESHOLD): cv.positive_time_period,
        vol.Optional(CONF_FUTURE_SPAN): cv.positive_float,
        vol.Optional(CONF_SHOW): vol.All(SHOW_SCHEMA),
        vol.Optional(CONF_CHECK_BACK): vol.All(CHECK_BACK_SCHEMA),
        vol.Optional(CONF_VOLUME): vol.All(VOLUME_SCHEMA),
        vol.Optional(CONF_DURATION): cv.positive_time_period_template,
        vol.Optional(CONF_USER): vol.All(USER_SCHEMA),
    }
)

ALL_ZONES_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SHOW): vol.All(SHOW_SCHEMA),
        vol.Optional(CONF_MINIMUM): cv.positive_time_period,
        vol.Optional(CONF_MAXIMUM): cv.positive_time_period,
        vol.Optional(CONF_THRESHOLD): cv.positive_time_period,
        vol.Optional(CONF_FUTURE_SPAN): cv.positive_float,
        vol.Optional(CONF_ALLOW_MANUAL): cv.boolean,
        vol.Optional(CONF_CHECK_BACK): vol.All(CHECK_BACK_SCHEMA),
        vol.Optional(CONF_VOLUME): vol.All(VOLUME_SCHEMA),
        vol.Optional(CONF_DURATION): cv.positive_time_period_template,
        vol.Optional(CONF_USER): vol.All(USER_SCHEMA),
        vol.Optional(CONF_ENTITY_STATES): vol.Any("none", "all", "on", "off"),
    }
)

SEQUENCE_ZONE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ZONE_ID): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_DELAY): cv.time_period,
        vol.Optional(CONF_DURATION): cv.positive_time_period,
        vol.Optional(CONF_REPEAT): cv.positive_int,
        vol.Optional(CONF_ENABLED): cv.boolean,
        vol.Optional(CONF_VOLUME): cv.positive_float,
    }
)

SEQUENCE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ZONES, default={}): vol.All(
            cv.ensure_list, [SEQUENCE_ZONE_SCHEMA], _list_is_not_empty
        ),
        vol.Optional(CONF_SCHEDULES): vol.All(
            cv.ensure_list, [SEQUENCE_SCHEDULE_SCHEMA]
        ),
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_SEQUENCE_ID): cv.matches_regex(IU_ID),
        vol.Optional(CONF_DELAY): cv.time_period,
        vol.Optional(CONF_DURATION): cv.positive_time_period,
        vol.Optional(CONF_REPEAT): cv.positive_int,
        vol.Optional(CONF_ENABLED): cv.boolean,
    }
)

CONTROLLER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ZONES): vol.All(
            cv.ensure_list, [ZONE_SCHEMA], _list_is_not_empty
        ),
        vol.Optional(CONF_SEQUENCES): vol.All(
            cv.ensure_list, [SEQUENCE_SCHEMA], _list_is_not_empty
        ),
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_CONTROLLER_ID): cv.matches_regex(IU_ID),
        vol.Optional(CONF_ENTITY_ID): cv.entity_ids,
        vol.Optional(CONF_ENTITY_STATES): vol.Any("none", "all", "on", "off"),
        vol.Optional(CONF_PREAMBLE): cv.time_period,
        vol.Optional(CONF_POSTAMBLE): cv.time_period,
        vol.Optional(CONF_ENABLED): cv.boolean,
        vol.Optional(CONF_ALL_ZONES_CONFIG): vol.All(ALL_ZONES_SCHEMA),
        vol.Optional(CONF_QUEUE_MANUAL): cv.boolean,
        vol.Optional(CONF_CHECK_BACK): vol.All(CHECK_BACK_SCHEMA),
        vol.Optional(CONF_VOLUME): vol.All(VOLUME_SCHEMA),
        vol.Optional(CONF_USER): vol.All(USER_SCHEMA),
        vol.Optional(CONF_SHOW_SEQUENCE_STATUS): cv.boolean,
    }
)

HISTORY_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ENABLED): cv.boolean,
        vol.Optional(CONF_REFRESH_INTERVAL): cv.positive_int,
        vol.Optional(CONF_SPAN): cv.positive_int,
        vol.Optional(CONF_READ_DELAY): cv.positive_int,
    }
)

clock_mode = vol.Any(CONF_FIXED, CONF_SEER)

CLOCK_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_MODE, default=CONF_SEER): clock_mode,
        vol.Optional(CONF_SHOW_LOG, default=False): cv.boolean,
        vol.Optional(CONF_MAX_LOG_ENTRIES): cv.positive_int,
    }
)

TEST_RESULT_SCHEMA = vol.Schema(
    {
        vol.Required("t"): cv.datetime,
        vol.Required("c"): cv.positive_int,
        vol.Required("z"): cv.positive_int,
        vol.Required("s"): cv.boolean,
    }
)

TEST_TIME_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_START): cv.datetime,
        vol.Required(CONF_END): cv.datetime,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_RESULTS): [TEST_RESULT_SCHEMA],
    }
)

TEST_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ENABLED): cv.boolean,
        vol.Optional(CONF_SPEED): cv.positive_float,
        vol.Optional(CONF_TIMES): [TEST_TIME_SCHEMA],
        vol.Optional(CONF_OUTPUT_EVENTS): cv.boolean,
        vol.Optional(CONF_SHOW_LOG): cv.boolean,
        vol.Optional(CONF_AUTOPLAY): cv.boolean,
    }
)

IRRIGATION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CONTROLLERS, default={}): vol.All(
            cv.ensure_list, [CONTROLLER_SCHEMA], _list_is_not_empty
        ),
        vol.Optional(CONF_GRANULARITY): cv.positive_int,
        vol.Optional(CONF_REFRESH_INTERVAL): cv.positive_int,
        vol.Optional(CONF_HISTORY_SPAN): cv.positive_int,
        vol.Optional(CONF_HISTORY_REFRESH): cv.positive_int,
        vol.Optional(CONF_SYNC_SWITCHES): cv.boolean,
        vol.Optional(CONF_RENAME_ENTITIES): cv.boolean,
        vol.Optional(CONF_TESTING): TEST_SCHEMA,
        vol.Optional(CONF_HISTORY): HISTORY_SCHEMA,
        vol.Optional(CONF_CLOCK): CLOCK_SCHEMA,
        vol.Optional(CONF_EXTENDED_CONFIG): cv.boolean,
        vol.Optional(CONF_RESTORE_FROM_ENTITY): cv.boolean,
        vol.Optional(CONF_SHOW_CONFIG): cv.boolean,
    }
)


positive_float_template = vol.Any(cv.positive_float, cv.template)

ENTITY_SCHEMA = {vol.Required(CONF_ENTITY_ID): cv.entity_id}

ENABLE_DISABLE_SCHEMA = {
    vol.Required(CONF_ENTITY_ID): cv.entity_ids,
    vol.Optional(CONF_ZONES): cv.ensure_list,
    vol.Optional(CONF_SEQUENCE_ID): cv.ensure_list,
}

TIME_ADJUST_SCHEMA = vol.All(
    cv.make_entity_service_schema(
        {
            vol.Required(CONF_ENTITY_ID): cv.entity_ids,
            vol.Exclusive(
                CONF_ACTUAL, "adjust_method"
            ): cv.positive_time_period_template,
            vol.Exclusive(CONF_PERCENTAGE, "adjust_method"): positive_float_template,
            vol.Exclusive(
                CONF_INCREASE, "adjust_method"
            ): cv.positive_time_period_template,
            vol.Exclusive(
                CONF_DECREASE, "adjust_method"
            ): cv.positive_time_period_template,
            vol.Exclusive(CONF_RESET, "adjust_method"): None,
            vol.Optional(CONF_MINIMUM): cv.positive_time_period_template,
            vol.Optional(CONF_MAXIMUM): cv.positive_time_period_template,
            vol.Optional(CONF_ZONES): cv.ensure_list,
            vol.Optional(CONF_SEQUENCE_ID): cv.ensure_list,
        }
    ),
    cv.has_at_least_one_key(
        CONF_ACTUAL, CONF_PERCENTAGE, CONF_INCREASE, CONF_DECREASE, CONF_RESET
    ),
)

MANUAL_RUN_SCHEMA = {
    vol.Required(CONF_ENTITY_ID): cv.entity_ids,
    vol.Optional(CONF_TIME): cv.positive_time_period_template,
    vol.Optional(CONF_DELAY): cv.time_period,
    vol.Optional(CONF_QUEUE): cv.boolean,
    vol.Optional(CONF_ZONES): cv.ensure_list,
    vol.Optional(CONF_SEQUENCE_ID): cv.ensure_list,
}

SUSPEND_SCHEMA = vol.All(
    cv.make_entity_service_schema(
        {
            vol.Required(CONF_ENTITY_ID): cv.entity_ids,
            vol.Exclusive(CONF_FOR, "time_method"): cv.positive_time_period_template,
            vol.Exclusive(CONF_UNTIL, "time_method"): cv.datetime,
            vol.Exclusive(CONF_RESET, "time_method"): None,
            vol.Optional(CONF_ZONES): cv.ensure_list,
            vol.Optional(CONF_SEQUENCE_ID): cv.ensure_list,
        }
    ),
    cv.has_at_least_one_key(CONF_FOR, CONF_UNTIL, CONF_RESET),
)

CANCEL_SCHEMA = {
    vol.Required(CONF_ENTITY_ID): cv.entity_ids,
    vol.Optional(CONF_ZONES): cv.ensure_list,
    vol.Optional(CONF_SEQUENCE_ID): cv.ensure_list,
}

PAUSE_RESUME_SCHEMA = {
    vol.Required(CONF_ENTITY_ID): cv.entity_ids,
    vol.Optional(CONF_SEQUENCE_ID): cv.ensure_list,
}

RELOAD_SERVICE_SCHEMA = vol.Schema({})
