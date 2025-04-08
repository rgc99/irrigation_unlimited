"""irrigation_unlimited service adjust_time tester"""
import json
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_TIME_ADJUST,
)
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


# pylint: disable=unused-argument,too-many-statements
async def test_service_sequence_adjust_time_by_controller(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test adjust_time service call on a sequence."""

    async with IUExam(hass, "service_adjust_time_sequence.yaml") as exam:
        await exam.begin_test(1)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "percentage": 50,
            },
        )
        await exam.run_until("2021-01-04 06:06:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%50.0"
        await exam.run_until("2021-01-04 06:12:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%50.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%50.0"
        await exam.run_until("2021-01-04 06:20:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%50.0"
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "percentage": 200,
            },
        )
        await exam.run_until("2021-01-04 06:11:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%200.0"
        await exam.run_until("2021-01-04 06:30:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%200.0"
        await exam.run_until("2021-01-04 07:01:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%200.0"
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "percentage": 0,
            },
        )
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "actual": "00:30",
            },
        )
        await exam.run_until("2021-01-04 06:07:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "=0:30:00"
        await exam.run_until("2021-01-04 06:16:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "=0:30:00"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "=0:30:00"
        await exam.run_until("2021-01-04 06:29:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "=0:30:00"
        await exam.finish_test()

        await exam.begin_test(5)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "increase": "00:05",
            },
        )
        await exam.run_until("2021-01-04 06:08:20")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "+0:05:00"
        await exam.run_until("2021-01-04 06:19:40")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "+0:05:00"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "+0:05:00"
        await exam.run_until("2021-01-04 06:35:45")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "+0:05:00"
        await exam.finish_test()

        await exam.begin_test(6)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "decrease": "00:05",
            },
        )
        await exam.run_until("2021-01-04 06:07:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "-0:05:00"
        await exam.run_until("2021-01-04 06:16:20")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "-0:05:00"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "-0:05:00"
        await exam.run_until("2021-01-04 06:29:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "-0:05:00"
        await exam.finish_test()

        await exam.begin_test(7)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "reset": None,
            },
        )
        await exam.run_until("2021-01-04 06:10:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == ""
        await exam.run_until("2021-01-04 06:21:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == ""
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == ""
        await exam.run_until("2021-01-04 06:32:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(8)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "percentage": 100,
                "minimum": "00:50",
            },
        )
        await exam.run_until("2021-01-04 06:09:10")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        await exam.run_until("2021-01-04 06:22:40")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        await exam.run_until("2021-01-04 06:49:50")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        await exam.finish_test()

        await exam.begin_test(9)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "percentage": 100,
                "maximum": "00:20",
            },
        )
        await exam.run_until("2021-01-04 06:07:40")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        await exam.run_until("2021-01-04 06:12:40")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        await exam.run_until("2021-01-04 06:22:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        await exam.finish_test()

        await exam.begin_test(10)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "percentage": 50,
            },
        )
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "percentage": 200,
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == "%200.0"
        await exam.run_until("2021-01-04 06:06:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%50.0"
        await exam.run_until("2021-01-04 06:12:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%50.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%50.0"
        await exam.run_until("2021-01-04 06:20:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%50.0"
        await exam.finish_test()

        # Test follows on from above. Timing should be 200% after sequence reset
        await exam.begin_test(11)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "reset": None,
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == "%200.0"
        await exam.run_until("2021-01-04 06:11:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%200.0"
        await exam.run_until("2021-01-04 06:30:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%200.0"
        await exam.run_until("2021-01-04 07:01:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%200.0"
        await exam.finish_test()

        # Reset zone adjustments. Test 'all' sequence_id (0) to %50
        await exam.begin_test(12)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "reset": None,
            },
        )
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
                "percentage": 50,
            },
        )
        if exam.coordinator.show_config:
            sta = hass.states.get("irrigation_unlimited.coordinator")
            data = json.loads(sta.attributes["configuration"])
            assert data["controllers"][0]["sequences"][0]["adjustment"] == "%50.0"
            assert data["controllers"][0]["sequences"][1]["adjustment"] == "%50.0"
        exam.check_iu_entity('c1_s1', "off", {"adjustment": "%50.0"})
        exam.check_iu_entity('c1_s2', "off", {"adjustment": "%50.0"})
        await exam.finish_test()

        # Reset zone adjustments. Test 'all' sequence_id (0) reset
        # Split the reset to check refresh correct
        await exam.begin_test(13)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
                "reset": None,
            },
        )
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
                "reset": None,
            },
        )
        if exam.coordinator.show_config:
            sta = hass.states.get("irrigation_unlimited.coordinator")
            data = json.loads(sta.attributes["configuration"])
            assert data["controllers"][0]["sequences"][0]["adjustment"] == ""
            assert data["controllers"][0]["sequences"][1]["adjustment"] == ""
        exam.check_iu_entity('c1_s1', "off", {"adjustment": ""})
        exam.check_iu_entity('c1_s2', "off", {"adjustment": ""})
        await exam.finish_test()

        exam.check_summary()


async def test_service_sequence_zone_adjust_time_by_controller(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test adjust_time service call on a sequence zone."""

    async with IUExam(hass, "service_adjust_time_sequence_zone.yaml") as exam:
        await exam.begin_test(1)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 1,
                "percentage": 50,
            },
        )
        await exam.run_until("2021-01-04 06:06:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["current_adjustment"] == ",%50.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["next_adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": [2, 3],
                "percentage": 50,
            },
        )
        await exam.run_until("2021-01-04 06:06:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["current_adjustment"] == ",%50.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["next_adjustment"] == ",%50.0"
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "percentage": 200,
            },
        )
        await exam.run_until("2021-01-04 06:06:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["current_adjustment"] == "%200.0,%50.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["next_adjustment"] == "%200.0,%50.0"
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "reset": None,
            },
        )
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 0,
                "reset": None,
            },
        )
        await exam.finish_test()

        await exam.begin_test(5)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
                "zones": 1,
                "percentage": 50,
            },
        )
        await exam.finish_test()

        await exam.begin_test(6)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
                "zones": [2, 3],
                "percentage": 50,
            },
        )
        await exam.finish_test()

        await exam.begin_test(7)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
                "percentage": 200,
            },
        )
        await exam.finish_test()

        await exam.begin_test(8)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
                "reset": None,
            },
        )
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
                "zones": 0,
                "reset": None,
            },
        )
        await exam.finish_test()

        exam.check_summary()


async def test_service_sequence_adjust_time_bad_by_controller(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test adjust_time service call on a zone entity with a sequence."""

    async with IUExam(hass, "service_adjust_time_sequence_bad.yaml") as exam:
        # Service call for sequence but targetting a zone entity
        await exam.begin_test(1)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "sequence_id": 1,
                "reset": None,
            },
        )
        await exam.finish_test()

        # Service call for sequence with a bad sequence_id
        await exam.begin_test(1)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 999,
                "reset": None,
            },
        )
        await exam.finish_test()


async def test_service_sequence_adjust_time_by_sequence(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test adjust_time service call on a sequence."""

    async with IUExam(hass, "service_adjust_time_sequence.yaml") as exam:
        await exam.begin_test(1)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "percentage": 50,
            },
        )
        await exam.run_until("2021-01-04 06:06:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%50.0"
        await exam.run_until("2021-01-04 06:12:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%50.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%50.0"
        await exam.run_until("2021-01-04 06:20:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%50.0"
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "percentage": 200,
            },
        )
        await exam.run_until("2021-01-04 06:11:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%200.0"
        await exam.run_until("2021-01-04 06:30:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%200.0"
        await exam.run_until("2021-01-04 07:01:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%200.0"
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "percentage": 0,
            },
        )
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "actual": "00:30",
            },
        )
        await exam.run_until("2021-01-04 06:07:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "=0:30:00"
        await exam.run_until("2021-01-04 06:16:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "=0:30:00"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "=0:30:00"
        await exam.run_until("2021-01-04 06:29:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "=0:30:00"
        await exam.finish_test()

        await exam.begin_test(5)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "increase": "00:05",
            },
        )
        await exam.run_until("2021-01-04 06:08:20")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "+0:05:00"
        await exam.run_until("2021-01-04 06:19:40")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "+0:05:00"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "+0:05:00"
        await exam.run_until("2021-01-04 06:35:45")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "+0:05:00"
        await exam.finish_test()

        await exam.begin_test(6)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "decrease": "00:05",
            },
        )
        await exam.run_until("2021-01-04 06:07:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "-0:05:00"
        await exam.run_until("2021-01-04 06:16:20")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "-0:05:00"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "-0:05:00"
        await exam.run_until("2021-01-04 06:29:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "-0:05:00"
        await exam.finish_test()

        await exam.begin_test(7)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "reset": None,
            },
        )
        await exam.run_until("2021-01-04 06:10:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == ""
        await exam.run_until("2021-01-04 06:21:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == ""
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == ""
        await exam.run_until("2021-01-04 06:32:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(8)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "percentage": 100,
                "minimum": "00:50",
            },
        )
        await exam.run_until("2021-01-04 06:09:10")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        await exam.run_until("2021-01-04 06:22:40")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        await exam.run_until("2021-01-04 06:49:50")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        await exam.finish_test()

        await exam.begin_test(9)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "percentage": 100,
                "maximum": "00:20",
            },
        )
        await exam.run_until("2021-01-04 06:07:40")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        await exam.run_until("2021-01-04 06:12:40")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        await exam.run_until("2021-01-04 06:22:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == ""
        assert sta.attributes["current_adjustment"] == "%100.0"
        await exam.finish_test()

        await exam.begin_test(10)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "percentage": 50,
            },
        )
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "percentage": 200,
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == "%200.0"
        await exam.run_until("2021-01-04 06:06:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%50.0"
        await exam.run_until("2021-01-04 06:12:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%50.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%50.0"
        await exam.run_until("2021-01-04 06:20:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%50.0"
        await exam.finish_test()

        # Test follows on from above. Timing should be 200% after sequence reset
        await exam.begin_test(11)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "reset": None,
            },
        )
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == "%200.0"
        await exam.run_until("2021-01-04 06:11:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%200.0"
        await exam.run_until("2021-01-04 06:30:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%200.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z3")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%200.0"
        await exam.run_until("2021-01-04 07:01:00")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["adjustment"] == "%200.0"
        assert sta.attributes["current_adjustment"] == "%200.0"
        await exam.finish_test()

        # Reset zone adjustments. Test 'all' sequence_id (0) to %50
        await exam.begin_test(12)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "reset": None,
            },
        )
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
                "percentage": 50,
            },
        )
        if exam.coordinator.show_config:
            sta = hass.states.get("irrigation_unlimited.coordinator")
            data = json.loads(sta.attributes["configuration"])
            assert data["controllers"][0]["sequences"][0]["adjustment"] == "%50.0"
            assert data["controllers"][0]["sequences"][1]["adjustment"] == "%50.0"
        exam.check_iu_entity('c1_s1', "off", {"adjustment": "%50.0"})
        exam.check_iu_entity('c1_s2', "off", {"adjustment": "%50.0"})
        await exam.finish_test()

        # Reset zone adjustments. Test 'all' sequence_id (0) reset
        # Split the reset to check refresh correct
        await exam.begin_test(13)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
                "reset": None,
            },
        )
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
                "reset": None,
            },
        )
        if exam.coordinator.show_config:
            sta = hass.states.get("irrigation_unlimited.coordinator")
            data = json.loads(sta.attributes["configuration"])
            assert data["controllers"][0]["sequences"][0]["adjustment"] == ""
            assert data["controllers"][0]["sequences"][1]["adjustment"] == ""
        exam.check_iu_entity('c1_s1', "off", {"adjustment": ""})
        exam.check_iu_entity('c1_s2', "off", {"adjustment": ""})
        await exam.finish_test()

        exam.check_summary()


async def test_service_sequence_zone_adjust_time_by_sequence(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test adjust_time service call on a sequence zone."""

    async with IUExam(hass, "service_adjust_time_sequence_zone.yaml") as exam:
        await exam.begin_test(1)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "zones": 1,
                "percentage": 50,
            },
        )
        await exam.run_until("2021-01-04 06:06:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["current_adjustment"] == ",%50.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["next_adjustment"] == ""
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "zones": [2, 3],
                "percentage": 50,
            },
        )
        await exam.run_until("2021-01-04 06:06:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["current_adjustment"] == ",%50.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["next_adjustment"] == ",%50.0"
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "percentage": 200,
            },
        )
        await exam.run_until("2021-01-04 06:06:30")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["current_adjustment"] == "%200.0,%50.0"
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.attributes["next_adjustment"] == "%200.0,%50.0"
        await exam.finish_test()

        await exam.begin_test(4)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "reset": None,
            },
        )
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "zones": 0,
                "reset": None,
            },
        )
        await exam.finish_test()

        await exam.begin_test(5)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
                "zones": 1,
                "percentage": 50,
            },
        )
        await exam.finish_test()

        await exam.begin_test(6)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
                "zones": [2, 3],
                "percentage": 50,
            },
        )
        await exam.finish_test()

        await exam.begin_test(7)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
                "percentage": 200,
            },
        )
        await exam.finish_test()

        await exam.begin_test(8)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
                "reset": None,
            },
        )
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
                "zones": 0,
                "reset": None,
            },
        )
        await exam.finish_test()

        exam.check_summary()
