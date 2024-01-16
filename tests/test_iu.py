"""Test irrigation_unlimited timing operations."""
import datetime
import json
import homeassistant.core as ha
from homeassistant.util import dt

from homeassistant.const import (
    CONF_ENTITY_ID,
)

from tests.iu_test_support import IUExam

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
    round_dt,
    IUAdjustment,
    IUBase,
    IUJSONEncoder,
    IUSchedule,
    IUSequence,
)

IUExam.quiet_mode()


async def test_wash():
    """Test time washing routines."""

    reset_granularity()

    # wash_dt
    dt_test = datetime.datetime(2021, 1, 4, 12, 10, 25, 123456, dt.UTC)
    assert wash_dt(dt_test) == datetime.datetime(2021, 1, 4, 12, 10, 0, 0, dt.UTC)
    assert wash_dt(dt_test, 15) == datetime.datetime(2021, 1, 4, 12, 10, 15, 0, dt.UTC)
    assert wash_dt(dt_test, 20) == datetime.datetime(2021, 1, 4, 12, 10, 20, 0, dt.UTC)
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

    # round_dt
    assert round_dt(
        datetime.datetime(2021, 1, 4, 12, 10, 29, 999999, dt.UTC)
    ) == datetime.datetime(2021, 1, 4, 12, 10, 0, 0, dt.UTC)
    assert round_dt(
        datetime.datetime(2021, 1, 4, 12, 10, 30, 0, dt.UTC)
    ) == datetime.datetime(2021, 1, 4, 12, 11, 0, 0, dt.UTC)
    assert round_dt(
        datetime.datetime(2021, 1, 4, 12, 10, 7, 499999, dt.UTC), 15
    ) == datetime.datetime(2021, 1, 4, 12, 10, 0, 0, dt.UTC)
    assert round_dt(
        datetime.datetime(2021, 1, 4, 12, 10, 7, 500000, dt.UTC), 15
    ) == datetime.datetime(2021, 1, 4, 12, 10, 15, 0, dt.UTC)
    assert round_dt(
        datetime.datetime(2021, 1, 4, 12, 10, 9, 999999, dt.UTC), 20
    ) == datetime.datetime(2021, 1, 4, 12, 10, 0, 0, dt.UTC)
    assert round_dt(
        datetime.datetime(2021, 1, 4, 12, 10, 10, 0, dt.UTC), 20
    ) == datetime.datetime(2021, 1, 4, 12, 10, 20, 0, dt.UTC)
    assert round_dt(None) is None

    # time_to_timedelta
    assert time_to_timedelta(datetime.time(0, 30, 0)) == datetime.timedelta(minutes=30)


async def test_nc_classes():
    """Test various classes that do not require a coordinator."""

    # IUAdjustment object
    assert str(IUAdjustment("=0:10:10")) == "=0:10:00"
    assert str(IUAdjustment("%50.5")) == "%50.5"
    assert str(IUAdjustment("+0:12:40")) == "+0:12:00"
    assert str(IUAdjustment("-0:14:50")) == "-0:14:00"
    assert str(IUAdjustment()) == ""
    assert IUAdjustment("%50.0").to_str() == "%50.0"
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
    assert not adj.to_dict()

    random_date = datetime.datetime(2021, 1, 4, 12, 10, 0, 0, dt.UTC)
    # pylint: disable=protected-access
    adj._method = "invalid"
    assert adj.adjust(random_date) == random_date

    # IUBase
    base = IUBase(3)
    assert base.index == 3
    assert base.id1 == 4
    assert IUBase.ids(base, "0", 1) == "4"
    assert IUBase.idl([base], "0", 1) == ["4"]

    # IUJSONEncoder
    enc = json.loads(
        json.dumps(
            {
                "a_date": datetime.datetime.fromisoformat("2021-01-04T20:10:00+00:00"),
                "a_time": datetime.timedelta(seconds=60),
            },
            cls=IUJSONEncoder,
        )
    )
    assert dt.as_utc(
        datetime.datetime.fromisoformat(enc["a_date"])
    ) == datetime.datetime.fromisoformat("2021-01-04T20:10:00+00:00")
    assert enc["a_time"] == 60


async def test_iu_classes(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test IU classes."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_skeleton.yaml") as exam:
        # Check entities registered
        assert (
            exam.coordinator.component.entity_id == "irrigation_unlimited.coordinator"
        )
        assert (
            exam.coordinator.controllers[0].master_sensor.entity_id
            == "binary_sensor.irrigation_unlimited_c1_m"
        )
        assert (
            exam.coordinator.controllers[0].zones[0].zone_sensor.entity_id
            == "binary_sensor.irrigation_unlimited_c1_z1"
        )

        sch = IUSchedule(hass, exam.coordinator, 0)
        dte = datetime.datetime.fromisoformat("2021-01-04T20:10:00+00:00")

        # Check when no schedule is loaded
        assert (
            sch.get_next_run(
                dte,
                dte + datetime.timedelta(days=3),
                datetime.timedelta(seconds=60),
                False,
            )
            is None
        )

        seq = IUSequence(hass, exam.coordinator, exam.coordinator.controllers[0], 0)
        exam.coordinator.controllers[0].add_sequence(seq)
        assert seq == exam.coordinator.controllers[0].find_add_sequence(0)

        seq.add_schedule(sch)
        assert sch == seq.find_add_schedule(0)
        assert seq.status == "off"
        assert seq.icon == "mdi:stop-circle-outline"
        assert seq.duration is None
        assert seq.delay is None

        zone = exam.coordinator.controllers[0].zones[0]
        zone.add(sch)
        assert sch == zone.find_add(0)


async def test_iu_minimal(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test IU classes."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_minimal.yaml") as exam:
        assert (
            exam.coordinator.controllers[0].sequences[0].sequence_sensor.entity_id
            == "binary_sensor.irrigation_unlimited_c1_s1"
        )

        assert exam.coordinator.get(1) is None
        assert exam.coordinator.controllers[0].get_zone(1) is None
        assert exam.coordinator.controllers[0].get_sequence(1) is None

        await exam.begin_test(1)
        assert len(exam.coordinator.controllers[0].runs.as_list()) == 6
        assert len(exam.coordinator.controllers[0].zones[0].runs.as_list()) == 6
        await exam.run_until("2021-01-04 06:15:00")
        await exam.finish_test()

        await exam.begin_test(2)
        assert len(exam.coordinator.controllers[0].runs.as_list()) == 6
        assert len(exam.coordinator.controllers[0].zones[0].runs.as_list()) == 6
        await exam.run_until("2021-01-04 07:15:00")
        sqz = exam.coordinator.controllers[0].zones[0].runs.current_run.sequence_zone
        assert sqz.icon() == "mdi:play-circle-outline"
        assert sqz.status() == "on"
        await exam.finish_test()


async def test_service_time(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test service_time function."""
    # pylint: disable=unused-argument
    # pylint: disable=protected-access

    async with IUExam(hass, "test_skeleton.yaml") as exam:
        dte = datetime.datetime.fromisoformat("2022-12-22T10:00:00+00:00")
        exam.coordinator.clock.load(
            {
                "clock": {
                    "mode": "seer",
                    "show_log": True,
                }
            }
        )
        exam.coordinator.timer(dte)
        await exam.coordinator._async_replay_last_timer(dte)
        # Check next tick is midnight tonight
        assert exam.coordinator.clock.next_tick == dt.as_utc(
            dt.as_local(dte + datetime.timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        )

        reset_granularity()
        exam.coordinator.clock.load(
            {
                "clock": {
                    "mode": "fixed",
                    "show_log": False,
                }
            }
        )
        exam.coordinator.timer(dte)
        assert exam.coordinator.service_time() == dte
