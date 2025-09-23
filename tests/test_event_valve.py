"""Test irrigation_unlimited valve events."""

import homeassistant.core as ha
from homeassistant.const import (
    STATE_ON,
)
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    EVENT_VALVE_ON,
    EVENT_VALVE_OFF,
)
from tests.iu_test_support import IUExam, mk_local

IUExam.quiet_mode()


def event_sorter(item: dict):
    """Sort by time then zone. Master should turn on before zone and
    turn off after zone"""
    if (zone := item["data"]["zone"]["index"]) is not None:
        zone += 1
    else:
        if item["event_type"] == "irrigation_unlimited_valve_on":
            zone = 0
        else:
            zone = 999
    return (item["event_time"], zone)


async def test_event_valve_basic(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test valve events."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_event_valve_basic.yaml") as exam:

        event_data: list[dict] = []

        def handle_event(event: ha.Event):
            nonlocal event_data
            event_data.append(
                {
                    "event_type": event.event_type,
                    "event_time": exam.virtual_time,
                    "data": event.data,
                }
            )

        hass.bus.async_listen(f"{DOMAIN}_{EVENT_VALVE_ON}", handle_event)
        hass.bus.async_listen(f"{DOMAIN}_{EVENT_VALVE_OFF}", handle_event)

        await exam.run_test(1)

        exam.check_summary()

        # HA seems to deliver the events out of order on some occasions? Sort the list
        # to make testing consistent
        event_data.sort(key=event_sorter)
        assert event_data == [
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:05:00"),
                "data": {
                    "type": 1,
                    "duration": 360,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:05:00"),
                "data": {
                    "type": 1,
                    "duration": 360,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 0, "zone_id": "1", "name": "Zone 1"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:11:00"),
                "data": {
                    "type": 3,
                    "duration": 720,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:11:00"),
                "data": {
                    "type": 1,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 0, "zone_id": "1", "name": "Zone 1"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:11:00"),
                "data": {
                    "type": 1,
                    "duration": 720,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 1, "zone_id": "2", "name": "Zone 2"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:11:00"),
                "data": {
                    "type": 1,
                    "duration": 720,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 2, "zone_id": "3", "name": "Zone 3"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:23:00"),
                "data": {
                    "type": 3,
                    "duration": 1080,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:23:00"),
                "data": {
                    "type": 1,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 1, "zone_id": "2", "name": "Zone 2"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:23:00"),
                "data": {
                    "type": 1,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 2, "zone_id": "3", "name": "Zone 3"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:23:00"),
                "data": {
                    "type": 1,
                    "duration": 1080,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 3, "zone_id": "4", "name": "Zone 4"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:41:00"),
                "data": {
                    "controller": {
                        "controller_id": "1",
                        "index": 0,
                        "name": "Test controller 1",
                    },
                    "duration": 600,
                    "entity_id": None,
                    "type": 3,
                    "zone": {"index": None, "name": None, "zone_id": None},
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:51:00"),
                "data": {
                    "type": 1,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 3, "zone_id": "4", "name": "Zone 4"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:51:00"),
                "data": {
                    "type": 1,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
        ]


async def test_event_valve_extended(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test valve events."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_event_valve_extended.yaml") as exam:

        event_data: list[dict] = []

        def handle_event(event: ha.Event):
            nonlocal event_data
            event_data.append(
                {
                    "event_type": event.event_type,
                    "event_time": exam.virtual_time,
                    "data": event.data,
                }
            )

            # Relay on event for zone 2
            if (
                event.event_type == "irrigation_unlimited_valve_on"
                and event.data["entity_id"] == "input_boolean.dummy_switch_c1_z2"
            ):
                hass.states.async_set(event.data["entity_id"], STATE_ON)

        await exam.load_component("homeassistant")
        await exam.load_component("input_boolean")

        hass.bus.async_listen(f"{DOMAIN}_{EVENT_VALVE_ON}", handle_event)
        hass.bus.async_listen(f"{DOMAIN}_{EVENT_VALVE_OFF}", handle_event)

        await exam.begin_test(1)

        await exam.run_until("2025-09-21 06:15:00")
        hass.states.async_set("input_boolean.dummy_switch_c1_z3", STATE_ON)

        await exam.finish_test()

        exam.check_summary()

        event_data.sort(key=event_sorter)

        assert event_data == [
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:05:00"),
                "data": {
                    "type": 1,
                    "duration": 360,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": "input_boolean.dummy_switch_c1_m",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:05:00"),
                "data": {
                    "type": 1,
                    "duration": 360,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 0, "zone_id": "1", "name": "Zone 1"},
                    "entity_id": "input_boolean.dummy_switch_c1_z1",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:11:00"),
                "data": {
                    "type": 3,
                    "duration": 720,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": "input_boolean.dummy_switch_c1_m",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:11:00"),
                "data": {
                    "type": 1,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 0, "zone_id": "1", "name": "Zone 1"},
                    "entity_id": "input_boolean.dummy_switch_c1_z1",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:11:00"),
                "data": {
                    "type": 1,
                    "duration": 720,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 1, "zone_id": "2", "name": "Zone 2"},
                    "entity_id": "input_boolean.dummy_switch_c1_z2",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:11:00"),
                "data": {
                    "type": 1,
                    "duration": 720,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 2, "zone_id": "3", "name": "Zone 3"},
                    "entity_id": "input_boolean.dummy_switch_c1_z3",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:11:30"),
                "data": {
                    "type": 2,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 0, "zone_id": "1", "name": "Zone 1"},
                    "entity_id": "input_boolean.dummy_switch_c1_z1",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:11:30"),
                "data": {
                    "type": 2,
                    "duration": 690,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 2, "zone_id": "3", "name": "Zone 3"},
                    "entity_id": "input_boolean.dummy_switch_c1_z3",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:12:00"),
                "data": {
                    "type": 2,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 0, "zone_id": "1", "name": "Zone 1"},
                    "entity_id": "input_boolean.dummy_switch_c1_z1",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:12:00"),
                "data": {
                    "type": 2,
                    "duration": 660,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 2, "zone_id": "3", "name": "Zone 3"},
                    "entity_id": "input_boolean.dummy_switch_c1_z3",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:12:30"),
                "data": {
                    "type": 2,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 0, "zone_id": "1", "name": "Zone 1"},
                    "entity_id": "input_boolean.dummy_switch_c1_z1",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:12:30"),
                "data": {
                    "type": 2,
                    "duration": 630,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 2, "zone_id": "3", "name": "Zone 3"},
                    "entity_id": "input_boolean.dummy_switch_c1_z3",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:23:00"),
                "data": {
                    "type": 3,
                    "duration": 1080,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": "input_boolean.dummy_switch_c1_m",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:23:00"),
                "data": {
                    "type": 1,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 1, "zone_id": "2", "name": "Zone 2"},
                    "entity_id": "input_boolean.dummy_switch_c1_z2",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:23:00"),
                "data": {
                    "type": 1,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 2, "zone_id": "3", "name": "Zone 3"},
                    "entity_id": "input_boolean.dummy_switch_c1_z3",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:23:00"),
                "data": {
                    "type": 1,
                    "duration": 1080,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 3, "zone_id": "4", "name": "Zone 4"},
                    "entity_id": "input_boolean.dummy_switch_c1_z4",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:23:30"),
                "data": {
                    "type": 2,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 2, "zone_id": "3", "name": "Zone 3"},
                    "entity_id": "input_boolean.dummy_switch_c1_z3",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:24:00"),
                "data": {
                    "type": 2,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 2, "zone_id": "3", "name": "Zone 3"},
                    "entity_id": "input_boolean.dummy_switch_c1_z3",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:24:30"),
                "data": {
                    "type": 2,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 2, "zone_id": "3", "name": "Zone 3"},
                    "entity_id": "input_boolean.dummy_switch_c1_z3",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2025-09-21 06:41:00"),
                "data": {
                    "type": 3,
                    "duration": 600,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": "input_boolean.dummy_switch_c1_m",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:51:00"),
                "data": {
                    "type": 1,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 3, "zone_id": "4", "name": "Zone 4"},
                    "entity_id": "input_boolean.dummy_switch_c1_z4",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:51:00"),
                "data": {
                    "type": 1,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": "input_boolean.dummy_switch_c1_m",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:51:30"),
                "data": {
                    "type": 2,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 3, "zone_id": "4", "name": "Zone 4"},
                    "entity_id": "input_boolean.dummy_switch_c1_z4",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:52:00"),
                "data": {
                    "type": 2,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 3, "zone_id": "4", "name": "Zone 4"},
                    "entity_id": "input_boolean.dummy_switch_c1_z4",
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-09-21 06:52:30"),
                "data": {
                    "type": 2,
                    "duration": 0,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Test controller 1",
                    },
                    "zone": {"index": 3, "zone_id": "4", "name": "Zone 4"},
                    "entity_id": "input_boolean.dummy_switch_c1_z4",
                },
            },
        ]
