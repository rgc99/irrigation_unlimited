"""Test integration_unlimited service calls."""

# pylint: disable=too-many-lines
from unittest.mock import patch
import homeassistant.core as ha
from tests.iu_test_support import (
    IUExam,
)
from custom_components.irrigation_unlimited.const import (
    SERVICE_CANCEL,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_TIME_ADJUST,
    SERVICE_TOGGLE,
    SERVICE_LOAD_SCHEDULE,
    SERVICE_SUSPEND,
)
from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IULogger,
)

IUExam.quiet_mode()


# pylint: disable=unused-argument
# pylint: disable=too-many-statements
async def test_service_adjust_time_basic(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test adjust_time service call."""

    async with IUExam(hass, "service_adjust_time.yaml") as exam:
        await exam.begin_test(1)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "percentage": 50},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%50.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "percentage": 200,
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "percentage": 0},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%0.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "actual": "00:30",
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "=0:30:00"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(5)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "increase": "00:05",
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "+0:05:00"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(6)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "decrease": "00:05",
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "-0:05:00"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(7)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "reset": None},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(8)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "percentage": 100,
                "minimum": "00:20",
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%100.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(9)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "percentage": 100,
                "maximum": "00:05",
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%100.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(10)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 50},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%50.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%50.0"
        await exam.finish_test()

        await exam.begin_test(11)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 200},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%200.0"
        await exam.finish_test()

        await exam.begin_test(12)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 0},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%0.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%0.0"
        await exam.finish_test()

        await exam.begin_test(13)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "actual": "00:30"},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "=0:30:00"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "=0:30:00"
        await exam.finish_test()

        await exam.begin_test(14)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "increase": "00:05",
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "+0:05:00"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "+0:05:00"
        await exam.finish_test()

        await exam.begin_test(15)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "decrease": "00:05",
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "-0:05:00"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "-0:05:00"
        await exam.finish_test()

        await exam.begin_test(16)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "reset": None},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(17)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "percentage": 100,
                "minimum": "00:20",
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%100.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%100.0"
        await exam.finish_test()

        await exam.begin_test(18)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "percentage": 100,
                "maximum": "00:05",
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%100.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%100.0"
        await exam.finish_test()

        await exam.begin_test(19)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "percentage": 50,
                "zones": ['zone_1', 'zone_2']
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%50.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%50.0"
        await exam.finish_test()

        await exam.begin_test(20)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "percentage": 25,
                "zones": 0
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%25.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%25.0"
        await exam.finish_test()
        exam.check_summary()


async def test_service_enable_disable_zone(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test enable/disable service call."""

    async with IUExam(hass, "service_enable_disable.yaml") as exam:
        # Zone 1 off
        await exam.begin_test(1)
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["status"] == "disabled"
        assert sta.attributes["enabled"] is False
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        await exam.finish_test()

        # Zone 1 on
        await exam.begin_test(2)
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        await exam.finish_test()

        # Zone 1 off, zone 2 on
        await exam.begin_test(3)
        await exam.call(
            SERVICE_TOGGLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["status"] == "disabled"
        assert sta.attributes["enabled"] is False
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        await exam.finish_test()

        # Double toggle: zone 1 on, zone 2 off
        await exam.begin_test(4)
        await exam.call(
            SERVICE_TOGGLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        await exam.call(
            SERVICE_TOGGLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z2"},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["status"] == "disabled"
        assert sta.attributes["enabled"] is False
        await exam.finish_test()

        # All off
        await exam.begin_test(5)
        await exam.call(
            SERVICE_TOGGLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["status"] == "disabled"
        assert sta.attributes["enabled"] is False
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["status"] == "disabled"
        assert sta.attributes["enabled"] is False
        await exam.finish_test()

        # All back on
        await exam.begin_test(6)
        await exam.call(
            SERVICE_TOGGLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        await exam.call(
            SERVICE_TOGGLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z2"},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        await exam.finish_test()

        # Controller 1 off
        await exam.begin_test(7)
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.attributes["status"] == "disabled"
        assert sta.attributes["enabled"] is False
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["status"] == "blocked"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["status"] == "blocked"
        assert sta.attributes["enabled"] is True
        await exam.finish_test()

        # Controller 1 off, zone 1 on, zone 2 off
        await exam.begin_test(8)
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z2"},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.attributes["status"] == "disabled"
        assert sta.attributes["enabled"] is False
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["status"] == "blocked"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["status"] == "blocked"
        assert sta.attributes["enabled"] is False
        await exam.finish_test()

        # Controller 1 on, zone 1 still on, zone 2 still off
        await exam.begin_test(9)
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["status"] == "disabled"
        assert sta.attributes["enabled"] is False
        await exam.finish_test()

        # Toggle controller 1
        await exam.begin_test(10)
        await exam.call(
            SERVICE_TOGGLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.attributes["status"] == "disabled"
        assert sta.attributes["enabled"] is False
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["status"] == "blocked"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["status"] == "blocked"
        assert sta.attributes["enabled"] is False
        await exam.finish_test()

        # Toggle controller 1 & zone 2 (All back on)
        await exam.begin_test(11)
        await exam.call(
            SERVICE_TOGGLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        )
        await exam.call(
            SERVICE_TOGGLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z2"},
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["status"] == "off"
        assert sta.attributes["enabled"] is True
        await exam.finish_test()

        # Seq 1 zone 1 off
        await exam.begin_test(12)
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        await exam.finish_test()

        # Seq 1 zone 2 off
        await exam.begin_test(13)
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z2"},
        )
        await exam.finish_test()

        # Seq 1 zone 4 off
        await exam.begin_test(14)
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z4"},
        )
        await exam.finish_test()

        # Seq 1 zone 3 off
        await exam.begin_test(15)
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z3"},
        )
        await exam.finish_test()

        # Seq 1 all zones on
        await exam.begin_test(16)
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z2"},
        )
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z3"},
        )
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z4"},
        )
        await exam.finish_test()

        # Seq 2 zone 1 off
        await exam.begin_test(17)
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        await exam.finish_test()

        # Seq 2 zone 2 off
        await exam.begin_test(18)
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z2"},
        )
        await exam.finish_test()

        # Seq 2 zone 4 off
        await exam.begin_test(19)
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z4"},
        )
        await exam.finish_test()

        # Seq 2 zone 3 off
        await exam.begin_test(20)
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z3"},
        )
        await exam.finish_test()

        # Seq 2 all zones on
        await exam.begin_test(21)
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z2"},
        )
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z3"},
        )
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z4"},
        )
        await exam.finish_test()

        exam.check_summary()


async def test_service_cancel(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test cancel service call."""

    async with IUExam(hass, "service_cancel.yaml") as exam:
        await exam.begin_test(1)
        await exam.run_until("2021-01-04 06:12:00")
        await exam.call(
            SERVICE_CANCEL,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.run_until("2021-01-04 06:12:00")
        await exam.call(
            SERVICE_CANCEL,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m"},
        )
        await exam.finish_test()

        exam.check_summary()


async def test_service_adjust_time_while_running(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test adjust_time service call while sequence is running."""

    async with IUExam(hass, "service_adjust_time_while_running.yaml") as exam:
        # Start a sequence
        await exam.begin_test(1)
        await exam.run_for("00:28:00")
        # Hit zone 4 with adjustment midway through sequence
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z4",
                "percentage": 200,
            },
        )
        await exam.finish_test()

        # Run next test which should be 200%
        await exam.begin_test(2)
        await exam.run_until("2021-01-04 07:55")
        # Reset adjustments
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "reset": None},
        )
        await exam.finish_test()

        # Start a sequence
        await exam.begin_test(3)
        await exam.run_for("00:28:00")
        # Hit controller with adjustment halfway through sequence
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 200},
        )
        await exam.finish_test()

        # Run next test which should be 200%
        await exam.begin_test(4)
        await exam.finish_test()

        exam.check_summary()


async def test_service_adjust_time_finish(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test adjust_time service call on a schedules with finish anchor."""

    async with IUExam(hass, "service_adjust_time_finish.yaml") as exam:
        await exam.begin_test(1)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "percentage": 50},
        )
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "percentage": 200,
            },
        )
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "percentage": 0},
        )
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "actual": "00:30",
            },
        )
        await exam.finish_test()

        await exam.begin_test(5)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "increase": "00:05",
            },
        )
        await exam.finish_test()

        await exam.begin_test(6)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "decrease": "00:05",
            },
        )
        await exam.finish_test()

        await exam.begin_test(7)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1", "reset": None},
        )
        await exam.finish_test()

        await exam.begin_test(8)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "percentage": 100,
                "minimum": "00:20",
            },
        )
        await exam.finish_test()

        await exam.begin_test(9)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "percentage": 100,
                "maximum": "00:05",
            },
        )
        await exam.finish_test()

        await exam.begin_test(10)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 50},
        )
        await exam.finish_test()

        await exam.begin_test(11)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 200},
        )
        await exam.finish_test()

        await exam.begin_test(12)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "percentage": 0},
        )
        await exam.finish_test()

        await exam.begin_test(13)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "actual": "00:30"},
        )
        await exam.finish_test()

        await exam.begin_test(14)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "increase": "00:05",
            },
        )
        await exam.finish_test()

        await exam.begin_test(15)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "decrease": "00:05",
            },
        )
        await exam.finish_test()

        await exam.begin_test(16)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_m", "reset": None},
        )
        await exam.finish_test()

        await exam.begin_test(17)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "percentage": 100,
                "minimum": "00:20",
            },
        )
        await exam.finish_test()

        await exam.begin_test(18)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "percentage": 100,
                "maximum": "00:05",
            },
        )
        await exam.finish_test()

        await exam.begin_test(19)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "percentage": 50,
            },
        )
        await exam.finish_test()

        await exam.begin_test(20)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "percentage": 200,
            },
        )
        await exam.finish_test()

        await exam.begin_test(21)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "percentage": 0,
            },
        )
        await exam.finish_test()

        await exam.begin_test(22)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "actual": "00:30",
            },
        )
        await exam.finish_test()

        await exam.begin_test(23)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "increase": "00:05",
            },
        )
        await exam.finish_test()

        await exam.begin_test(24)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "decrease": "00:05",
            },
        )
        await exam.finish_test()

        await exam.begin_test(25)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "actual": "7:30:00",
            },
        )
        await exam.finish_test()

        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "reset": None,
            },
        )
        await exam.begin_test(26)
        await exam.finish_test()

        exam.check_summary()


async def test_service_load_schedule(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test load_schedule service call."""

    async with IUExam(hass, "service_load_schedule.yaml") as exam:
        await exam.begin_test(1)
        await exam.call(
            SERVICE_LOAD_SCHEDULE,
            {"schedule_id": "zone_1_schedule_1", "time": "06:05", "duration": "00:15"},
        )
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.call(
            SERVICE_LOAD_SCHEDULE,
            {
                "schedule_id": "sequence_1_schedule_1",
                "time": "08:05",
                "duration": "00:47",
            },
        )
        await exam.finish_test()

        exam.check_summary()


async def test_service_suspend_controller_and_zone(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test suspend service call."""

    async with IUExam(hass, "service_suspend.yaml") as exam:
        await exam.begin_test(1)
        await exam.run_for("01:00:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "for": "24:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.run_for("01:00:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "until": "2021-01-06 06:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "until": "2021-01-06 06:00",
            },
        )
        await exam.run_until("2021-01-05 06:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "reset": None,
            },
        )
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.run_until("2021-01-05 06:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "for": "24:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(5)
        await exam.run_for("01:00:00")
        # await exam.run_until("2021-01-05 06:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "until": "2021-01-06 06:00",
            },
        )
        await exam.finish_test()

        await exam.begin_test(6)
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "until": "2021-01-06 06:00",
            },
        )
        await exam.run_until("2021-01-05 06:00")
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "reset": None,
            },
        )
        await exam.finish_test()

        exam.check_summary()


async def test_service_bad(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test bad service calls in general"""
    async with IUExam(hass, "service_bad.yaml") as exam:
        await exam.begin_test(1)
        with patch.object(IULogger, "_format") as mock:
            await exam.call(
                SERVICE_TIME_ADJUST,
                {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                    "zones": 999,
                    "reset": None,
                },
            )
        await exam.finish_test()
        assert (
            sum([1 for call in mock.call_args_list if call.args[1] == "ZONE_ID"])
            == 1
        )

        await exam.begin_test(2)
        with patch.object(IULogger, "_format") as mock:
            await exam.call(
                SERVICE_TIME_ADJUST,
                {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                    "zones": 'zone_x',
                    "reset": None,
                },
            )
        await exam.finish_test()
        assert (
            sum([1 for call in mock.call_args_list if call.args[1] == "ZONE_ID"])
            == 1
        )
        exam.check_summary()

async def test_service_suspend_sequence_bad(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test bad calls to the suspend service"""

    async with IUExam(hass, "service_suspend_sequence_bad.yaml") as exam:
        await exam.begin_test(1)
        with patch.object(IULogger, "_format") as mock:
            await exam.call(
                SERVICE_SUSPEND,
                {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                    "sequence_id": 999,
                    "reset": None,
                },
            )
        await exam.finish_test()
        assert (
            sum([1 for call in mock.call_args_list if call.args[1] == "SEQUENCE_ID"])
            == 1
        )

        # Service call for sequence but targetting a zone entity
        await exam.begin_test(2)
        with patch.object(IULogger, "_format") as mock:
            await exam.call(
                SERVICE_SUSPEND,
                {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                    "sequence_id": 1,
                    "reset": None,
                },
            )
        await exam.finish_test()
        assert sum(1 for call in mock.call_args_list if call.args[1] == "ENTITY") == 1

        # Duplicate service call
        await exam.begin_test(3)
        with patch.object(IULogger, "_format") as mock:
            await exam.call(
                SERVICE_SUSPEND,
                {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                    "sequence_id": 1,
                    "for": "01:00",
                },
            )
            await exam.call(
                SERVICE_SUSPEND,
                {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                    "sequence_id": 1,
                    "for": "01:00",
                },
            )
        await exam.finish_test()
        print(mock.call_args_list)
        assert (
            sum(
                1
                for call in mock.call_args_list
                if call.args[0] == 20 and call.args[1] == "CALL"
            )
            == 1
        )


async def test_service_sequence_id_list(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test service calls using sequence_id as a list"""
    async with IUExam(hass, "service_sequence_id_list.yaml") as exam:
        await exam.run_test(1)

        await exam.begin_test(2)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": [1],
                "percentage": 50,
            },
        )
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": [0],
                "percentage": 25,
            },
        )
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": ['seq_1'],
                "percentage": 200,
            },
        )
        await exam.finish_test()
        exam.check_summary()
