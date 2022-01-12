"""Test irrigation_unlimited timing operations."""
import datetime
import homeassistant.core as ha
import homeassistant.util.dt as dt

from homeassistant.const import (
    CONF_ENTITY_ID,
)

from custom_components.irrigation_unlimited.const import (
    CONF_ACTUAL,
    CONF_DECREASE,
    CONF_INCREASE,
    CONF_MAXIMUM,
    CONF_MINIMUM,
    CONF_PERCENTAGE,
    CONF_RESET,
)

from custom_components.irrigation_unlimited.service import (
    TIME_ADJUST_SCHEMA,
)

from custom_components.irrigation_unlimited.irrigation_unlimited import (
    reset_granularity,
    round_td,
    time_to_timedelta,
    wash_dt,
    wash_t,
    wash_td,
    IUAdjustment,
)

# pylint: disable=unused-argument
async def test_wash(hass: ha.HomeAssistant):
    """Test time washing routines."""

    reset_granularity()

    # wash_dt
    dt_test = dt.as_utc(datetime.datetime(2021, 1, 4, 12, 10, 25, 123456))
    assert wash_dt(dt_test) == dt.as_utc(datetime.datetime(2021, 1, 4, 12, 10, 0, 0))
    assert wash_dt(dt_test, 15) == dt.as_utc(
        datetime.datetime(2021, 1, 4, 12, 10, 15, 0)
    )
    assert wash_dt(dt_test, 20) == dt.as_utc(
        datetime.datetime(2021, 1, 4, 12, 10, 20, 0)
    )
    assert wash_dt(None) is None

    # wash_td
    td_test = datetime.timedelta(0, 85, 123456)
    assert wash_td(td_test) == datetime.timedelta(0, 60)
    assert wash_td(td_test, 15) == datetime.timedelta(0, 75)
    assert wash_td(td_test, 20) == datetime.timedelta(0, 80)
    assert wash_td(None) is None

    # wash_t
    t_test = datetime.time(6, 10, 25, 123456, dt.UTC)
    assert wash_t(t_test) == datetime.time(6, 10, 0, 0, dt.UTC)
    assert wash_t(t_test, 15) == datetime.time(6, 10, 15, 0, dt.UTC)
    assert wash_t(t_test, 20) == datetime.time(6, 10, 20, 0, dt.UTC)
    assert wash_t(None) is None

    # round_td
    assert round_td(datetime.timedelta(0, 89, 999999)) == datetime.timedelta(0, 60, 0)
    assert round_td(datetime.timedelta(0, 90, 0)) == datetime.timedelta(0, 120, 0)
    assert round_td(datetime.timedelta(0, 67, 499999), 15) == datetime.timedelta(
        0, 60, 0
    )
    assert round_td(datetime.timedelta(0, 67, 500000), 15) == datetime.timedelta(
        0, 75, 0
    )
    assert round_td(datetime.timedelta(0, 69, 999999), 20) == datetime.timedelta(
        0, 60, 0
    )
    assert round_td(datetime.timedelta(0, 70, 0), 20) == datetime.timedelta(0, 80, 0)
    assert round_td(None) is None

    # time_to_timedelta
    assert time_to_timedelta(datetime.time(0, 30, 0)) == datetime.timedelta(minutes=30)

    # IUAdjustment object
    assert str(IUAdjustment("=0:10:10")) == "=0:10:00"
    assert str(IUAdjustment("%50.5")) == "%50.5"
    assert str(IUAdjustment("+0:12:40")) == "+0:12:00"
    assert str(IUAdjustment("-0:14:50")) == "-0:14:00"
    assert str(IUAdjustment()) == ""
    assert IUAdjustment().to_str() == "None"
    adj = IUAdjustment()
    adj.load(
        TIME_ADJUST_SCHEMA(
            {
                CONF_ENTITY_ID: "dummy.dummy",
                CONF_ACTUAL: "0:10:10",
            }
        )
    )
    assert str(adj) == "=0:10:00"
    assert adj.to_dict() == {CONF_ACTUAL: datetime.timedelta(seconds=600)}
    adj.load(
        TIME_ADJUST_SCHEMA(
            {
                CONF_ENTITY_ID: "dummy.dummy",
                CONF_PERCENTAGE: 50.5,
            }
        )
    )
    assert str(adj) == "%50.5"
    assert adj.to_dict() == {CONF_PERCENTAGE: float(50.5)}
    adj.load(
        TIME_ADJUST_SCHEMA(
            {
                CONF_ENTITY_ID: "dummy.dummy",
                CONF_INCREASE: "0:12:40",
            }
        )
    )
    assert str(adj) == "+0:12:00"
    assert adj.to_dict() == {CONF_INCREASE: datetime.timedelta(seconds=720)}
    adj.load(
        TIME_ADJUST_SCHEMA(
            {
                CONF_ENTITY_ID: "dummy.dummy",
                CONF_DECREASE: "0:14:50",
            }
        )
    )
    assert str(adj) == "-0:14:00"
    assert adj.to_dict() == {CONF_DECREASE: datetime.timedelta(seconds=840)}
    adj.load(
        TIME_ADJUST_SCHEMA(
            {
                CONF_ENTITY_ID: "dummy.dummy",
                CONF_ACTUAL: "0:10:00",
                CONF_MINIMUM: "0:05:00",
                CONF_MAXIMUM: "0:20:00",
            }
        )
    )
    assert str(adj) == "=0:10:00"
    assert adj.to_dict() == {
        CONF_ACTUAL: datetime.timedelta(seconds=600),
        CONF_MINIMUM: datetime.timedelta(seconds=300),
        CONF_MAXIMUM: datetime.timedelta(seconds=1200),
    }
    adj.load(
        TIME_ADJUST_SCHEMA(
            {
                CONF_ENTITY_ID: "dummy.dummy",
                CONF_RESET: None,
            }
        )
    )
    assert str(adj) == ""
    assert adj.to_dict() == {}
