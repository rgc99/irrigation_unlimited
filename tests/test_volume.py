"""irrigation_unlimited volume test module"""

from unittest.mock import patch
from datetime import datetime
import asyncio
from collections.abc import Iterator
import pytest
import homeassistant.core as ha
from homeassistant.util import dt
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    EVENT_VALVE_ON,
    EVENT_VALVE_OFF,
    SERVICE_TIME_ADJUST,
)
from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IULogger,
    IUVolume,
)
from tests.iu_test_support import IUExam, mk_local

IUExam.quiet_mode()

# pylint: disable=unused-argument


async def set_sensor(hass: ha.HomeAssistant, entity_id: str, value: str) -> None:
    """Set the mock sensor"""
    await hass.services.async_call(
        "input_text",
        "set_value",
        {"entity_id": entity_id, "value": value},
        True,
    )


def read_data(file: str) -> Iterator[tuple[datetime, str, str]]:
    """Read data from the log file"""
    with open(file, encoding="utf-8") as fhd:
        for line in fhd:
            if line.startswith("#"):
                continue
            data = line.strip().split(";")
            data = [s.strip() for s in data]
            if len(data) >= 3:
                dts = dt.as_local(datetime.fromisoformat(data[0]))
                value = data[2]
                yield (dts, value, data[1])


async def test_volume_class(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test IUVolume class"""
    # pylint: disable=too-many-statements
    # pylint: disable=protected-access
    async with IUExam(hass, "test_volume.yaml") as exam:
        await exam.load_component("input_text")

        with patch.object(IULogger, "_format") as mock:
            await exam.begin_test(1)
            await set_sensor(hass, "input_text.dummy_sensor_1", "abc")
            await exam.run_until("2021-01-04 06:45")
            assert (
                sum(
                    (
                        1
                        for call in mock.call_args_list
                        if call.args[1] == "VOLUME_SENSOR"
                    )
                )
                == 1
            )
            assert (
                sum(
                    (
                        1
                        for call in mock.call_args_list
                        if call.args[1] == "VOLUME_VALUE"
                    )
                )
                == 1
            )
            await set_sensor(hass, "input_text.dummy_sensor_1", "123")
            await exam.finish_test()

        with patch.object(IULogger, "log_invalid_meter_id") as mock_meter_id:
            with patch.object(IULogger, "log_invalid_meter_value") as mock_meter_value:
                # Check bad entity_id in config is logged
                await exam.begin_test(2)
                await exam.run_until("2021-01-04 06:45")
                assert mock_meter_id.call_count == 1
                await exam.finish_test()

                # Sensor starts out with bad value
                await exam.begin_test(3)
                await set_sensor(hass, "input_text.dummy_sensor_1", "abc")
                await exam.run_until("2021-01-04 06:45")
                assert mock_meter_value.call_count == 1
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
                assert sta.attributes["volume"] is None
                await exam.finish_test()

                # Sensor has bad value mid stream but recovers
                await exam.begin_test(4)
                await set_sensor(hass, "input_text.dummy_sensor_1", "100.0")
                await exam.run_until("2021-01-04 06:07")
                await set_sensor(hass, "input_text.dummy_sensor_1", "zzz")
                await exam.run_until("2021-01-04 06:10")
                await set_sensor(hass, "input_text.dummy_sensor_1", "110.0")
                await exam.run_until("2021-01-04 06:45")
                assert mock_meter_value.call_count == 2
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
                assert sta.attributes["volume"] == 10.000
                await exam.finish_test()

                # Sensor ends with bad value
                await exam.begin_test(5)
                await set_sensor(hass, "input_text.dummy_sensor_1", "621.505")
                await exam.run_until("2021-01-04 06:10")
                await set_sensor(hass, "input_text.dummy_sensor_1", "zzz")
                await exam.run_until("2021-01-04 06:45")
                assert mock_meter_value.call_count == 3
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
                assert sta.attributes["volume"] is None
                await exam.finish_test()

                # Negative sensor value
                await exam.begin_test(6)
                await set_sensor(hass, "input_text.dummy_sensor_1", "-621.505")
                await exam.run_until("2021-01-04 06:45")
                assert mock_meter_value.call_count == 4
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
                assert sta.attributes["volume"] is None
                await exam.finish_test()

                # Sensor goes negative
                await exam.begin_test(7)
                await set_sensor(hass, "input_text.dummy_sensor_1", "621.505")
                await exam.run_until("2021-01-04 06:10")
                await set_sensor(hass, "input_text.dummy_sensor_1", "611.345")
                await exam.run_until("2021-01-04 06:45")
                assert mock_meter_value.call_count == 5
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
                assert sta.attributes["volume"] is None
                await exam.finish_test()

                # Sensor goes MIA
                calls_id = mock_meter_id.call_count
                await exam.begin_test(8)
                await set_sensor(hass, "input_text.dummy_sensor_1", "524.941")
                await exam.run_until("2021-01-04 06:09")
                old_id = exam.coordinator.controllers[0].zones[0].volume._sensor_id
                try:
                    exam.coordinator.controllers[0].zones[
                        0
                    ].volume._sensor_id = "input_text.does_not_exist"
                    await exam.run_until("2021-01-04 06:10")
                    assert mock_meter_id.call_count == calls_id
                    await set_sensor(hass, "input_text.dummy_sensor_1", "525.692")
                    await exam.run_until("2021-01-04 06:11:30")
                    assert mock_meter_id.call_count == calls_id + 1
                    await exam.run_until("2021-01-04 06:45")
                    sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
                    assert sta.attributes["volume"] is None
                finally:
                    exam.coordinator.controllers[0].zones[0].volume._sensor_id = old_id
                await exam.finish_test()

                # A good run
                calls_id = mock_meter_id.call_count
                await exam.begin_test(9)
                await set_sensor(hass, "input_text.dummy_sensor_1", "745.004")
                await set_sensor(hass, "input_text.dummy_sensor_2", "6.270")
                await exam.run_until("2021-01-04 06:07")
                await set_sensor(hass, "input_text.dummy_sensor_1", "756.002")
                await exam.run_until("2021-01-04 06:13")
                await set_sensor(hass, "input_text.dummy_sensor_2", "7.051")
                await exam.run_until("2021-01-04 06:15")
                await set_sensor(hass, "input_text.dummy_sensor_2", "8.25")
                await exam.run_until("2021-01-04 06:17")
                await set_sensor(hass, "input_text.dummy_sensor_2", "8.50")
                await exam.run_until("2021-01-04 06:18")
                assert exam.coordinator.controllers[0].zones[1].volume.total == 2.230
                await exam.run_until("2021-01-04 06:19")
                await set_sensor(hass, "input_text.dummy_sensor_2", "9.50")
                await exam.run_until("2021-01-04 06:21")
                await set_sensor(hass, "input_text.dummy_sensor_2", "10.02")
                await exam.run_until("2021-01-04 06:23")
                await set_sensor(hass, "input_text.dummy_sensor_2", "11.042")
                await exam.run_until("2021-01-04 06:45")
                assert mock_meter_value.call_count == 5
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
                assert sta.attributes["volume"] == 10.998
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
                assert sta.attributes["volume"] == 4.772
                assert mock_meter_id.call_count == calls_id + 1
                await exam.finish_test()

                with patch.object(IUVolume, "event_hook") as mock:
                    event_time: datetime = None

                    def state_change(event: ha.Event) -> ha.Event:
                        nonlocal event_time
                        event.time_fired_timestamp = event_time.timestamp()
                        return event

                    mock.side_effect = state_change

                    # Event time does not change
                    await exam.begin_test(10)
                    await set_sensor(hass, "input_text.dummy_sensor_1", "730.739")
                    await exam.run_until("2021-01-04 06:07")
                    event_time = mk_local("2021-01-04 06:07")
                    await set_sensor(hass, "input_text.dummy_sensor_1", "745.004")
                    await exam.run_until("2021-01-04 06:08")
                    await set_sensor(hass, "input_text.dummy_sensor_1", "756.002")
                    await exam.run_until("2021-01-04 06:45")
                    assert mock_meter_value.call_count == 6
                    await exam.finish_test()

                    # Event time goes backwards
                    await exam.begin_test(11)
                    await set_sensor(hass, "input_text.dummy_sensor_1", "730.739")
                    await exam.run_until("2021-01-04 06:07")
                    event_time = mk_local("2021-01-04 06:07")
                    await set_sensor(hass, "input_text.dummy_sensor_1", "745.004")
                    await exam.run_until("2021-01-04 06:08")
                    event_time = mk_local("2021-01-04 06:06")
                    await set_sensor(hass, "input_text.dummy_sensor_1", "756.002")
                    await exam.run_until("2021-01-04 06:45")
                    assert mock_meter_value.call_count == 7
                    await exam.finish_test()

        exam.check_summary()


async def test_volume_extensive(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test exhaustive volume class test."""

    async with IUExam(hass, "test_volume_extensive.yaml") as exam:

        valve_events: list[dict] = []

        def handle_valve_event(event: ha.Event):
            nonlocal valve_events
            valve_events.append(
                {
                    "event_type": event.event_type,
                    "event_time": exam.virtual_time,
                    "data": event.data,
                }
            )

        def valve_event_sorter(item: dict):
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

        hass.bus.async_listen(f"{DOMAIN}_{EVENT_VALVE_ON}", handle_valve_event)
        hass.bus.async_listen(f"{DOMAIN}_{EVENT_VALVE_OFF}", handle_valve_event)

        await exam.load_component("input_text")

        await exam.begin_test(1)
        # pylint: disable=unused-variable
        controller_volumes: list[float] = []
        controller_flows: list[float] = []
        zone_volumes: list[float] = []
        zone_flows: list[float] = []
        sequence_volumes: list[float] = []

        with patch.object(IUVolume, "event_hook") as mock:
            zone: int = None
            event_time: datetime = None
            trackers_processed: int = 0

            def state_change(event: ha.Event) -> ha.Event:
                nonlocal event_time, trackers_processed
                event.time_fired_timestamp = event_time.timestamp()
                trackers_processed += 1
                return event

            mock.side_effect = state_change
            for event_time, value, sensor in read_data("tests/logs/volume_sensor.log"):
                await exam.run_until(event_time)

                if value.endswith("%"):
                    await exam.call(
                        SERVICE_TIME_ADJUST,
                        {
                            "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                            "sequence_id": 1,
                            "percentage": value[-4:-1].strip(),
                        },
                    )

                    continue

                if value == "on":
                    zone = hass.states.get(
                        "binary_sensor.irrigation_unlimited_c1_m"
                    ).attributes["current_zone"]
                elif value == "off":
                    sta = hass.states.get(
                        f"binary_sensor.irrigation_unlimited_c1_z{zone}"
                    )
                    zone_volumes.append(sta.attributes["volume"])
                    zone_flows.append(sta.attributes["flow_rate"])
                    sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_s1")
                    sequence_volumes.append(sta.attributes["volume"])
                    sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
                    controller_volumes.append(sta.attributes["volume"])
                    controller_flows.append(sta.attributes["flow_rate"])
                else:
                    await set_sensor(hass, "input_text.dummy_sensor", value)
                    while trackers_processed < IUVolume.trackers:
                        await asyncio.sleep(0)
                    trackers_processed = 0

        assert controller_volumes == [
            0.128,
            0.121,
            0.060,
            0.071,
            0.030,
            0.058,
            0.095,
            0.056,
            0.134,
            0.045,
            0.031,
            0.072,
            0.671,
        ]

        assert zone_volumes == [
            128.0,
            121.0,
            60.0,
            71.0,
            30.0,
            58.0,
            95.0,
            56.0,
            134.0,
            45.0,
            31.0,
            72.0,
            671.0,
        ]

        assert sequence_volumes == [
            128.0,
            249.0,
            309.0,
            380.0,
            410.0,
            468.0,
            563.0,
            619.0,
            753.0,
            798.0,
            829.0,
            901.0,
            1572.0,
        ]

        assert controller_flows == [
            0.29,
            0.401,
            0.136,
            0.148,
            0.095,
            0.092,
            0.152,
            0.126,
            0.355,
            0.306,
            0.065,
            0.154,
            1.119,
        ]

        assert zone_flows == [
            4.8,
            6.7,
            2.3,
            2.5,
            1.6,
            1.5,
            2.5,
            2.1,
            5.9,
            5.1,
            1.1,
            2.6,
            18.7,
        ]

        await exam.finish_test()

        exam.check_summary()

        valve_events.sort(key=valve_event_sorter)
        assert valve_events == [
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-13 22:00:00"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 1620,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-13 22:00:00"),
                "data": {
                    "iu_id": "c1_z1",
                    "id": "1_1",
                    "type": 1,
                    "duration": 1620,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 0, "zone_id": "1", "name": "Café François"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-13 22:27:00"),
                "data": {
                    "iu_id": "c1_z1",
                    "id": "1_1",
                    "type": 1,
                    "duration": 0,
                    "volume": 128.0,
                    "flow_rate": 4.8,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 0, "zone_id": "1", "name": "Café François"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-13 22:27:00"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 0.128,
                    "flow_rate": 0.29,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-13 22:27:01"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 1080,
                    "volume": 0.128,
                    "flow_rate": 0.29,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-13 22:27:01"),
                "data": {
                    "iu_id": "c1_z2",
                    "id": "1_2",
                    "type": 1,
                    "duration": 1080,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 1, "zone_id": "2", "name": "Serre"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-13 22:45:01"),
                "data": {
                    "iu_id": "c1_z2",
                    "id": "1_2",
                    "type": 1,
                    "duration": 0,
                    "volume": 121.0,
                    "flow_rate": 6.7,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 1, "zone_id": "2", "name": "Serre"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-13 22:45:01"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 0.121,
                    "flow_rate": 0.401,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-13 22:45:02"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 1620,
                    "volume": 0.121,
                    "flow_rate": 0.401,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-13 22:45:02"),
                "data": {
                    "iu_id": "c1_z9",
                    "id": "1_9",
                    "type": 1,
                    "duration": 1620,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 8, "zone_id": "9", "name": "Pare-terre Julie"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-13 23:12:02"),
                "data": {
                    "iu_id": "c1_z9",
                    "id": "1_9",
                    "type": 1,
                    "duration": 0,
                    "volume": 60.0,
                    "flow_rate": 2.3,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 8, "zone_id": "9", "name": "Pare-terre Julie"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-13 23:12:02"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 0.06,
                    "flow_rate": 0.136,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-13 23:12:03"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 1620,
                    "volume": 0.06,
                    "flow_rate": 0.136,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-13 23:12:03"),
                "data": {
                    "iu_id": "c1_z4",
                    "id": "1_4",
                    "type": 1,
                    "duration": 1620,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 3, "zone_id": "4", "name": "Deux carrés"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-13 23:39:03"),
                "data": {
                    "iu_id": "c1_z4",
                    "id": "1_4",
                    "type": 1,
                    "duration": 0,
                    "volume": 71.0,
                    "flow_rate": 2.5,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 3, "zone_id": "4", "name": "Deux carrés"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-13 23:39:03"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 0.071,
                    "flow_rate": 0.148,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-13 23:39:04"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 1080,
                    "volume": 0.071,
                    "flow_rate": 0.148,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-13 23:39:04"),
                "data": {
                    "iu_id": "c1_z5",
                    "id": "1_5",
                    "type": 1,
                    "duration": 1080,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 4, "zone_id": "5", "name": "Un carré"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-13 23:57:04"),
                "data": {
                    "iu_id": "c1_z5",
                    "id": "1_5",
                    "type": 1,
                    "duration": 0,
                    "volume": 30.0,
                    "flow_rate": 1.6,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 4, "zone_id": "5", "name": "Un carré"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-13 23:57:04"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 0.03,
                    "flow_rate": 0.095,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-13 23:57:05"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 2160,
                    "volume": 0.03,
                    "flow_rate": 0.095,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-13 23:57:05"),
                "data": {
                    "iu_id": "c1_z6",
                    "id": "1_6",
                    "type": 1,
                    "duration": 2160,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 5, "zone_id": "6", "name": "Petits fruits"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 00:33:05"),
                "data": {
                    "iu_id": "c1_z6",
                    "id": "1_6",
                    "type": 1,
                    "duration": 0,
                    "volume": 58.0,
                    "flow_rate": 1.5,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 5, "zone_id": "6", "name": "Petits fruits"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 00:33:05"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 0.058,
                    "flow_rate": 0.092,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 00:33:06"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 2160,
                    "volume": 0.058,
                    "flow_rate": 0.092,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 00:33:06"),
                "data": {
                    "iu_id": "c1_z7",
                    "id": "1_7",
                    "type": 1,
                    "duration": 2160,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {
                        "index": 6,
                        "zone_id": "7",
                        "name": "Haie - Céanothe - Fleurs",
                    },
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 01:09:06"),
                "data": {
                    "iu_id": "c1_z7",
                    "id": "1_7",
                    "type": 1,
                    "duration": 0,
                    "volume": 95.0,
                    "flow_rate": 2.5,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {
                        "index": 6,
                        "zone_id": "7",
                        "name": "Haie - Céanothe - Fleurs",
                    },
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 01:09:06"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 0.095,
                    "flow_rate": 0.152,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 01:09:07"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 1620,
                    "volume": 0.095,
                    "flow_rate": 0.152,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 01:09:07"),
                "data": {
                    "iu_id": "c1_z8",
                    "id": "1_8",
                    "type": 1,
                    "duration": 1620,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 7, "zone_id": "8", "name": "Pommiers"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 01:36:07"),
                "data": {
                    "iu_id": "c1_z8",
                    "id": "1_8",
                    "type": 1,
                    "duration": 0,
                    "volume": 56.0,
                    "flow_rate": 2.1,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 7, "zone_id": "8", "name": "Pommiers"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 01:36:07"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 0.056,
                    "flow_rate": 0.126,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 01:36:08"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 1350,
                    "volume": 0.056,
                    "flow_rate": 0.126,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 01:36:08"),
                "data": {
                    "iu_id": "c1_z10",
                    "id": "1_10",
                    "type": 1,
                    "duration": 1350,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 9, "zone_id": "10", "name": "Haies pelouses"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 01:58:38"),
                "data": {
                    "iu_id": "c1_z10",
                    "id": "1_10",
                    "type": 1,
                    "duration": 0,
                    "volume": 134.0,
                    "flow_rate": 5.9,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 9, "zone_id": "10", "name": "Haies pelouses"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 01:58:38"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 0.134,
                    "flow_rate": 0.355,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 01:58:39"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 540,
                    "volume": 0.134,
                    "flow_rate": 0.355,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 01:58:39"),
                "data": {
                    "iu_id": "c1_z11",
                    "id": "1_11",
                    "type": 1,
                    "duration": 540,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 10, "zone_id": "11", "name": "If Cour carrée"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 02:07:39"),
                "data": {
                    "iu_id": "c1_z11",
                    "id": "1_11",
                    "type": 1,
                    "duration": 0,
                    "volume": 45.0,
                    "flow_rate": 5.1,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 10, "zone_id": "11", "name": "If Cour carrée"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 02:07:39"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 0.045,
                    "flow_rate": 0.306,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 02:07:40"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 1620,
                    "volume": 0.045,
                    "flow_rate": 0.306,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 02:07:40"),
                "data": {
                    "iu_id": "c1_z12",
                    "id": "1_12",
                    "type": 1,
                    "duration": 1620,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 11, "zone_id": "12", "name": "Haie du fond"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 02:34:40"),
                "data": {
                    "iu_id": "c1_z12",
                    "id": "1_12",
                    "type": 1,
                    "duration": 0,
                    "volume": 31.0,
                    "flow_rate": 1.1,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 11, "zone_id": "12", "name": "Haie du fond"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 02:34:40"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 0.031,
                    "flow_rate": 0.065,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 02:34:41"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 1620,
                    "volume": 0.031,
                    "flow_rate": 0.065,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 02:34:41"),
                "data": {
                    "iu_id": "c1_z13",
                    "id": "1_13",
                    "type": 1,
                    "duration": 1620,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 12, "zone_id": "13", "name": "Tilleul"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 03:01:41"),
                "data": {
                    "iu_id": "c1_z13",
                    "id": "1_13",
                    "type": 1,
                    "duration": 0,
                    "volume": 72.0,
                    "flow_rate": 2.6,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 12, "zone_id": "13", "name": "Tilleul"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 03:01:41"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 0.072,
                    "flow_rate": 0.154,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 03:01:42"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 2160,
                    "volume": 0.072,
                    "flow_rate": 0.154,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_on",
                "event_time": mk_local("2023-10-14 03:01:42"),
                "data": {
                    "iu_id": "c1_z3",
                    "id": "1_3",
                    "type": 1,
                    "duration": 2160,
                    "volume": None,
                    "flow_rate": None,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 2, "zone_id": "3", "name": "Pelouse"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 03:37:42"),
                "data": {
                    "iu_id": "c1_z3",
                    "id": "1_3",
                    "type": 1,
                    "duration": 0,
                    "volume": 671.0,
                    "flow_rate": 18.7,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": 2, "zone_id": "3", "name": "Pelouse"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2023-10-14 03:37:42"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 0.671,
                    "flow_rate": 1.119,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Controleur 1",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
        ]


@pytest.mark.skip
async def test_volume_limit(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test volume limit."""

    async with IUExam(hass, "test_volume_limit.yaml") as exam:
        await exam.load_component("input_text")

        await exam.begin_test(1)
        # pylint: disable=unused-variable
        controller_volumes: list[float] = []
        controller_flows: list[float] = []
        zone_volumes: list[float] = []
        zone_flows: list[float] = []
        sequence_volumes: list[float] = []

        with patch.object(IUVolume, "event_hook") as mock:
            zone: int = None
            event_time: datetime = None
            trackers_processed: int = 0

            def state_change(event: ha.Event) -> ha.Event:
                nonlocal event_time, trackers_processed
                event.time_fired_timestamp = event_time.timestamp()
                trackers_processed += 1
                return event

            mock.side_effect = state_change
            for event_time, value, sensor in read_data("tests/logs/volume_sensor.log"):
                await exam.run_until(event_time)

                if value.endswith("%"):
                    await exam.call(
                        SERVICE_TIME_ADJUST,
                        {
                            "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                            "sequence_id": 1,
                            "percentage": value[-4:-1].strip(),
                        },
                    )

                    continue

                if value == "on":
                    zone = hass.states.get(
                        "binary_sensor.irrigation_unlimited_c1_m"
                    ).attributes["current_zone"]
                elif value == "off":
                    sta = hass.states.get(
                        f"binary_sensor.irrigation_unlimited_c1_z{zone}"
                    )
                    zone_volumes.append(sta.attributes["volume"])
                    zone_flows.append(sta.attributes["flow_rate"])
                    sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_s1")
                    sequence_volumes.append(sta.attributes["volume"])
                    sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
                    controller_volumes.append(sta.attributes["volume"])
                    controller_flows.append(sta.attributes["flow_rate"])
                else:
                    await set_sensor(hass, "input_text.dummy_sensor", value)
                    while trackers_processed < IUVolume.trackers:
                        await asyncio.sleep(0)
                    trackers_processed = 0

        assert controller_volumes == [
            0.128,
            0.121,
            0.060,
            0.071,
            0.030,
            0.058,
            0.095,
            0.056,
            0.134,
            0.045,
            0.031,
            0.072,
            0.671,
        ]

        assert zone_volumes == [
            128.0,
            121.0,
            60.0,
            71.0,
            30.0,
            58.0,
            95.0,
            56.0,
            134.0,
            45.0,
            31.0,
            72.0,
            671.0,
        ]

        assert sequence_volumes == [
            128.0,
            249.0,
            309.0,
            380.0,
            410.0,
            468.0,
            563.0,
            619.0,
            753.0,
            798.0,
            829.0,
            901.0,
            1572.0,
        ]

        assert controller_flows == [
            0.29,
            0.401,
            0.136,
            0.148,
            0.095,
            0.092,
            0.152,
            0.126,
            0.355,
            0.306,
            0.065,
            0.154,
            1.119,
        ]

        assert zone_flows == [
            4.8,
            6.7,
            2.3,
            2.5,
            1.6,
            1.5,
            2.5,
            2.1,
            5.9,
            5.1,
            1.1,
            2.6,
            18.7,
        ]

        await exam.finish_test()

        exam.check_summary()
