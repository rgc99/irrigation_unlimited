"""Test irrigation_unlimited timing operations."""
import datetime
import homeassistant.core as ha
import homeassistant.util.dt as dt

from custom_components.irrigation_unlimited.irrigation_unlimited import (
    reset_granularity,
    round_td,
    time_to_timedelta,
    wash_dt,
    wash_t,
    wash_td,
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
