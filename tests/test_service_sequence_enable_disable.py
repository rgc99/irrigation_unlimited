"""irrigation_unlimited service enable/disable/toggle tester"""
from unittest.mock import patch
import json
import homeassistant.core as ha
from tests.iu_test_support import IUExam
from custom_components.irrigation_unlimited.const import (
    SERVICE_ENABLE,
    SERVICE_DISABLE,
    SERVICE_TOGGLE,
)
from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IULogger,
)

IUExam.quiet_mode()


# pylint: disable=unused-argument,too-many-statements
async def test_service_sequence_enable_disable_by_controller(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test enable/disable on sequence service call."""

    async with IUExam(hass, "service_enable_disable_sequence.yaml") as exam:
        # Sequence 1 off
        await exam.begin_test(1)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
            },
        )
        await exam.finish_test()

        # Sequence 1 on
        await exam.begin_test(2)
        await exam.call(
            SERVICE_ENABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
            },
        )
        await exam.finish_test()

        # Sequence 1 off, sequence 2 on
        await exam.begin_test(3)
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
            },
        )
        await exam.finish_test()

        # Double toggle: sequence 1 on, sequence 2 off
        await exam.begin_test(4)
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
            },
        )
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
            },
        )
        await exam.finish_test()

        # All off
        await exam.begin_test(5)
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
            },
        )
        await exam.finish_test()

        # All back on
        await exam.begin_test(6)
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
            },
        )
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
            },
        )
        await exam.finish_test()

        # Disable sequence 1, zone 1
        await exam.begin_test(7)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 1,
            },
        )
        await exam.finish_test()

        # Disable sequence 1, zone 2
        await exam.begin_test(8)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 2,
            },
        )
        await exam.finish_test()

        # Disable sequence 1, zone 3
        await exam.begin_test(9)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 3,
            },
        )
        await exam.finish_test()

        # Disable sequence 2, all zones (All off)
        await exam.begin_test(10)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
                "zones": 0,
            },
        )
        await exam.finish_test()

        # Toggle sequence 1 zones 1 and 3
        await exam.begin_test(11)
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": [1, 3],
            },
        )
        await exam.finish_test()

        # Enable sequence 1 zone 2 and sequence 2
        await exam.begin_test(12)
        await exam.call(
            SERVICE_ENABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 2,
            },
        )
        await exam.call(
            SERVICE_ENABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 2,
                "zones": [1, 2, 3],
            },
        )
        await exam.finish_test()

        # At this stage all sequences and zones are enabled
        # Disable all sequences
        await exam.begin_test(13)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
            },
        )
        if exam.coordinator.show_config:
            sta = hass.states.get("irrigation_unlimited.coordinator")
            data = json.loads(sta.attributes["configuration"])
            assert data["controllers"][0]["sequences"][0]["enabled"] is False
            assert data["controllers"][0]["sequences"][1]["enabled"] is False
        exam.check_iu_entity('c1_s1', "off", {"enabled": False})
        exam.check_iu_entity('c1_s2', "off", {"enabled": False})
        await exam.finish_test()

        # Enable all sequences
        await exam.begin_test(14)
        await exam.call(
            SERVICE_ENABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
            },
        )
        if exam.coordinator.show_config:
            sta = hass.states.get("irrigation_unlimited.coordinator")
            data = json.loads(sta.attributes["configuration"])
            assert data["controllers"][0]["sequences"][0]["enabled"] is True
            assert data["controllers"][0]["sequences"][1]["enabled"] is True
        exam.check_iu_entity('c1_s1', "off", {"enabled": True})
        exam.check_iu_entity('c1_s2', "off", {"enabled": True})
        await exam.finish_test()

        # Disable non existant sequence
        with patch.object(IULogger, "_format") as mock:
            await exam.begin_test(15)
            await exam.call(
                SERVICE_DISABLE,
                {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                    "sequence_id": 3,
                },
            )
            await exam.finish_test()
            assert (
                sum(1 for call in mock.call_args_list if call.args[1] == "SEQUENCE_ID")
                == 1
            )

        exam.check_summary()


async def test_service_sequence_enable_disable_by_sequence(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test enable/disable on sequence service call."""

    async with IUExam(hass, "service_enable_disable_sequence.yaml") as exam:
        # Sequence 1 off
        await exam.begin_test(1)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        # Sequence 1 on
        await exam.begin_test(2)
        await exam.call(
            SERVICE_ENABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        # Sequence 1 off, sequence 2 on
        await exam.begin_test(3)
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        # Double toggle: sequence 1 on, sequence 2 off
        await exam.begin_test(4)
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        await exam.finish_test()

        # All off
        await exam.begin_test(5)
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.finish_test()

        # All back on
        await exam.begin_test(6)
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
            },
        )
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
            },
        )
        await exam.finish_test()

        # Disable sequence 1, zone 1
        await exam.begin_test(7)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "zones": 1,
            },
        )
        await exam.finish_test()

        # Disable sequence 1, zone 2
        await exam.begin_test(8)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "zones": 2,
            },
        )
        await exam.finish_test()

        # Disable sequence 1, zone 3
        await exam.begin_test(9)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "zones": 3,
            },
        )
        await exam.finish_test()

        # Disable sequence 2, all zones (All off)
        await exam.begin_test(10)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
                "zones": 0,
            },
        )
        await exam.finish_test()

        # Toggle sequence 1 zones 1 and 3
        await exam.begin_test(11)
        await exam.call(
            SERVICE_TOGGLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "zones": [1, 3],
            },
        )
        await exam.finish_test()

        # Enable sequence 1 zone 2 and sequence 2
        await exam.begin_test(12)
        await exam.call(
            SERVICE_ENABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "zones": 2,
            },
        )
        await exam.call(
            SERVICE_ENABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
                "zones": [1, 2, 3],
            },
        )
        await exam.finish_test()

        # At this stage all sequences and zones are enabled
        # Disable all sequences
        await exam.begin_test(13)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
            },
        )
        if exam.coordinator.show_config:
            sta = hass.states.get("irrigation_unlimited.coordinator")
            data = json.loads(sta.attributes["configuration"])
            assert data["controllers"][0]["sequences"][0]["enabled"] is False
            assert data["controllers"][0]["sequences"][1]["enabled"] is False
        exam.check_iu_entity('c1_s1', "off", {"enabled": False})
        exam.check_iu_entity('c1_s2', "off", {"enabled": False})
        await exam.finish_test()

        # Enable all sequences
        await exam.begin_test(14)
        await exam.call(
            SERVICE_ENABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 0,
            },
        )
        if exam.coordinator.show_config:
            sta = hass.states.get("irrigation_unlimited.coordinator")
            data = json.loads(sta.attributes["configuration"])
            assert data["controllers"][0]["sequences"][0]["enabled"] is True
            assert data["controllers"][0]["sequences"][1]["enabled"] is True
        exam.check_iu_entity('c1_s1', "off", {"enabled": True})
        exam.check_iu_entity('c1_s2', "off", {"enabled": True})
        await exam.finish_test()

        # Disable non existant sequence
        with patch.object(IULogger, "_format") as mock:
            await exam.begin_test(15)
            await exam.call(
                SERVICE_DISABLE,
                {
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                    "sequence_id": 3,
                },
            )
            await exam.finish_test()
            assert (
                sum(1 for call in mock.call_args_list if call.args[1] == "SEQUENCE_ID")
                == 1
            )

        exam.check_summary()
