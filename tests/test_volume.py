"""irrigation_unlimited volume test module"""

from unittest.mock import patch
from datetime import datetime
import copy
import asyncio
from collections.abc import Iterator
import homeassistant.core as ha
from homeassistant.util import dt
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    EVENT_FINISH,
    EVENT_VALVE_ON,
    EVENT_VALVE_OFF,
    SERVICE_TIME_ADJUST,
)
from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IULogger,
    IUVolume,
    wash_dt,
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


async def test_volume_class(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test IUVolume class"""
    # pylint: disable=too-many-statements
    # pylint: disable=protected-access

    async with IUExam(hass, "test_volume.yaml") as exam:

        async def fake_event(ctl: int, zone: int) -> None:
            event = ha.Event(
                "state_changed", time_fired_timestamp=exam.virtual_time.timestamp()
            )
            await exam.coordinator.controllers[ctl - 1].zones[
                zone - 1
            ].volume.sensor_state_change(event)
            return

        await exam.load_component("input_text")

        with patch.object(IULogger, "_format") as mock:
            await exam.begin_test(1)
            await set_sensor(hass, "input_text.dummy_sensor_1", "abc")
            await fake_event(1, 1)
            await fake_event(1, 2)
            await fake_event(1, 3)
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
                await fake_event(1, 3)
                assert mock_meter_id.call_count == 1
                await exam.finish_test()

                # Sensor starts out with bad value
                await exam.begin_test(3)
                await exam.run_until("2021-01-04 06:06")
                await set_sensor(hass, "input_text.dummy_sensor_1", "abc")
                await exam.run_until("2021-01-04 06:45")
                assert mock_meter_value.call_count == 1
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
                assert sta.attributes["volume"] is None
                await exam.finish_test()

                # Sensor has bad value mid stream but recovers
                await exam.begin_test(4)
                await exam.run_until("2021-01-04 06:06")
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
                await exam.run_until("2021-01-04 06:06")
                await set_sensor(hass, "input_text.dummy_sensor_1", "-621.505")
                await exam.run_until("2021-01-04 06:45")
                assert mock_meter_value.call_count == 4
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
                assert sta.attributes["volume"] is None
                await exam.finish_test()

                # Sensor goes negative
                await exam.begin_test(7)
                await exam.run_until("2021-01-04 06:06")
                await set_sensor(hass, "input_text.dummy_sensor_1", "621.505")
                await exam.run_until("2021-01-04 06:10")
                await set_sensor(hass, "input_text.dummy_sensor_1", "611.345")
                await exam.run_until("2021-01-04 06:45")
                assert mock_meter_value.call_count == 5
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
                assert sta.attributes["volume"] == 0
                await exam.finish_test()

                # Sensor goes MIA
                calls_id = mock_meter_id.call_count
                await exam.begin_test(8)
                await exam.run_until("2021-01-04 06:06")
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
                    assert sta.attributes["volume"] == 0.0
                finally:
                    exam.coordinator.controllers[0].zones[0].volume._sensor_id = old_id
                await exam.finish_test()

                # A good run
                calls_id = mock_meter_id.call_count
                await exam.begin_test(9)
                await exam.run_until("2021-01-04 06:06")
                await set_sensor(hass, "input_text.dummy_sensor_1", "745.004")
                await exam.run_until("2021-01-04 06:07")
                await set_sensor(hass, "input_text.dummy_sensor_1", "756.002")
                await exam.run_until("2021-01-04 06:13")
                await set_sensor(hass, "input_text.dummy_sensor_2", "6.270")
                await exam.run_until("2021-01-04 06:14")
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
                assert mock_meter_id.call_count == calls_id
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
                    await exam.run_until("2021-01-04 06:06")
                    event_time = mk_local("2021-01-04 06:06")
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
                    await exam.run_until("2021-01-04 06:06")
                    event_time = mk_local("2021-01-04 06:06")
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
            0.127,
            0.12,
            0.059,
            0.07,
            0.029,
            0.057,
            0.094,
            0.055,
            0.133,
            0.044,
            0.03,
            0.071,
            0.67,
        ]

        assert zone_volumes == [
            127.0,
            120.0,
            59.0,
            70.0,
            29.0,
            57.0,
            94.0,
            55.0,
            133.0,
            44.0,
            30.0,
            71.0,
            670.0,
        ]

        assert sequence_volumes == [
            127.0,
            247.0,
            306.0,
            376.0,
            405.0,
            462.0,
            556.0,
            611.0,
            744.0,
            788.0,
            818.0,
            889.0,
            1559.0,
        ]

        assert controller_flows == [
            0.282,
            0.4,
            0.131,
            0.156,
            0.097,
            0.095,
            0.157,
            0.122,
            0.355,
            0.293,
            0.067,
            0.158,
            1.117,
        ]

        assert zone_flows == [
            4.7,
            6.7,
            2.2,
            2.6,
            1.6,
            1.6,
            2.6,
            2.0,
            5.9,
            4.9,
            1.1,
            2.6,
            18.6,
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
                    "volume": 127.0,
                    "flow_rate": 4.7,
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
                    "volume": 0.127,
                    "flow_rate": 0.284,
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
                    "volume": 0.127,
                    "flow_rate": 0.282,
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
                    "volume": 120.0,
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
                    "volume": 0.12,
                    "flow_rate": 0.404,
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
                    "volume": 0.12,
                    "flow_rate": 0.4,
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
                    "volume": 59.0,
                    "flow_rate": 2.2,
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
                    "volume": 0.059,
                    "flow_rate": 0.133,
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
                    "volume": 0.059,
                    "flow_rate": 0.131,
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
                    "volume": 70.0,
                    "flow_rate": 2.6,
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
                    "volume": 0.07,
                    "flow_rate": 0.156,
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
                    "volume": 0.07,
                    "flow_rate": 0.156,
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
                    "volume": 29.0,
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
                    "volume": 0.029,
                    "flow_rate": 0.099,
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
                    "volume": 0.029,
                    "flow_rate": 0.097,
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
                    "volume": 57.0,
                    "flow_rate": 1.6,
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
                    "volume": 0.057,
                    "flow_rate": 0.097,
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
                    "volume": 0.057,
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
                    "volume": 94.0,
                    "flow_rate": 2.6,
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
                    "volume": 0.094,
                    "flow_rate": 0.157,
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
                    "volume": 0.094,
                    "flow_rate": 0.157,
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
                    "volume": 55.0,
                    "flow_rate": 2.0,
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
                    "volume": 0.055,
                    "flow_rate": 0.123,
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
                    "volume": 0.055,
                    "flow_rate": 0.122,
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
                    "volume": 133.0,
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
                    "volume": 0.133,
                    "flow_rate": 0.356,
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
                    "volume": 0.133,
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
                    "volume": 44.0,
                    "flow_rate": 4.9,
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
                    "volume": 0.044,
                    "flow_rate": 0.307,
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
                    "volume": 0.044,
                    "flow_rate": 0.293,
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
                    "volume": 30.0,
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
                    "volume": 0.03,
                    "flow_rate": 0.067,
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
                    "volume": 0.03,
                    "flow_rate": 0.067,
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
                    "volume": 71.0,
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
                    "volume": 0.071,
                    "flow_rate": 0.16,
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
                    "volume": 0.071,
                    "flow_rate": 0.158,
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
                    "volume": 670.0,
                    "flow_rate": 18.6,
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
                    "volume": 0.67,
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


async def test_volume_fault(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test volume where the sensor stops reporting after 3 minutes. This is
    simulating a blockage"""

    def read_data(
        file: str,
    ) -> Iterator[tuple[int, datetime, str, str]]:
        """Read data from the log file"""
        with open(file, encoding="utf-8") as fhd:
            for line in fhd:
                if line.startswith("#"):
                    continue
                data = line.strip().split(";")
                data = [s.strip() for s in data]
                if len(data) >= 6:
                    op = int(data[0])
                    dts = dt.as_local(datetime.fromisoformat(data[1]))
                    adjustment = data[4]
                    volume = data[5]
                    yield (op, dts, adjustment, volume)

    def event_sorter(item: dict):
        """Sort by time"""
        return item["event_time"]

    async with IUExam(hass, "test_volume_fault.yaml") as exam:
        await exam.load_component("input_text")

        event_data: list[dict] = []

        def handle_valve_event(event: ha.Event):
            nonlocal event_data
            event_data.append(
                {
                    "event_type": event.event_type,
                    "event_time": exam.virtual_time,
                    "data": event.data,
                }
            )
            if event.data["iu_id"].startswith("c1_z"):
                zone_volumes.append(event.data["volume"])
                zone_flows.append(event.data["flow_rate"])
            elif event.data["iu_id"] == "c1_m":
                controller_volumes.append(event.data["volume"])
                controller_flows.append(event.data["flow_rate"])

        hass.bus.async_listen(f"{DOMAIN}_{EVENT_VALVE_OFF}", handle_valve_event)

        def handle_finish_event(event: ha.Event):
            nonlocal event_data
            event_data.append(
                {
                    "event_type": event.event_type,
                    "event_time": exam.virtual_time,
                    "data": event.data,
                }
            )
            sta = hass.states.get(event.data["entity_id"])
            sequence_volumes.append(sta.attributes["volume"])

        hass.bus.async_listen(f"{DOMAIN}_{EVENT_FINISH}", handle_finish_event)

        await exam.begin_test(1)
        # pylint: disable=unused-variable
        controller_volumes: list[float] = []
        controller_flows: list[float] = []
        zone_volumes: list[float] = []
        zone_flows: list[float] = []
        sequence_volumes: list[float] = []

        with patch.object(IUVolume, "event_hook") as mock:
            event_time: datetime = None
            trackers_processed: int = 0

            def state_change(event: ha.Event) -> ha.Event:
                nonlocal event_time, trackers_processed
                event.time_fired_timestamp = event_time.timestamp()
                trackers_processed += 1
                return event

            mock.side_effect = state_change
            for op, event_time, adjustment, volume in read_data(
                "tests/logs/volume_fault_sensor.log"
            ):
                await exam.run_until(wash_dt(event_time))

                if op == 0:
                    await set_sensor(hass, "input_text.dummy_sensor", volume)
                    await exam.call(
                        SERVICE_TIME_ADJUST,
                        {
                            "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                            "sequence_id": [1, 2],
                            "percentage": adjustment,
                        },
                    )
                    continue
                elif op == 2:
                    await set_sensor(hass, "input_text.dummy_sensor", volume)
                    while trackers_processed < IUVolume.trackers:
                        await asyncio.sleep(0)
                    trackers_processed = 0
                else:
                    continue

        assert controller_volumes == [147.182, 1.34]
        assert controller_flows == [239.136, 321.705]
        assert zone_volumes == [20.475, 125.644, 1.34]
        assert zone_flows == [1.113, 6.828, 1.608]
        assert sequence_volumes == [143.263, 1.34]

        await exam.finish_test()

        exam.check_summary()

        event_data.sort(key=event_sorter)
        assert event_data == [
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-10-31 05:03:24"),
                "data": {
                    "iu_id": "c1_z3",
                    "id": "1_upper_beds",
                    "type": 1,
                    "duration": 0,
                    "volume": 20.475,
                    "flow_rate": 1.113,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Green House",
                    },
                    "zone": {"index": 2, "zone_id": "upper_beds", "name": "Upper Beds"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_finish",
                "event_time": mk_local("2025-10-31 05:21:58"),
                "data": {
                    "iu_id": "c1_s2",
                    "id": "1_vege_beds",
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_s2",
                    "volume": 146.119,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Green House",
                    },
                    "sequence": {
                        "index": 1,
                        "sequence_id": "vege_beds",
                        "name": "Vege Beds",
                    },
                    "zones": [
                        {
                            "index": 2,
                            "zone_id": "upper_beds",
                            "name": "Upper Beds",
                            "duration": 1104,
                            "volume": 20.475,
                        },
                        {
                            "index": 3,
                            "zone_id": "lower_beds",
                            "name": "Lower Beds",
                            "duration": 1104,
                            "volume": 125.644,
                        },
                    ],
                    "run": {"duration": 2218},
                    "zone_ids": ["lower_beds", "upper_beds"],
                    "schedule": {
                        "index": 0,
                        "schedule_id": "vege_beds_dawn",
                        "name": "Dawn",
                    },
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-10-31 05:21:58"),
                "data": {
                    "iu_id": "c1_z4",
                    "id": "1_lower_beds",
                    "type": 1,
                    "duration": 0,
                    "volume": 125.644,
                    "flow_rate": 6.828,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Green House",
                    },
                    "zone": {"index": 3, "zone_id": "lower_beds", "name": "Lower Beds"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-10-31 05:22:08"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 147.182,
                    "flow_rate": 239.136,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Green House",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_finish",
                "event_time": mk_local("2025-10-31 05:46:14"),
                "data": {
                    "iu_id": "c1_s1",
                    "id": "1_pots",
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                    "volume": 1.34,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Green House",
                    },
                    "sequence": {"index": 0, "sequence_id": "pots", "name": "Pots"},
                    "zones": [
                        {
                            "index": 0,
                            "zone_id": "pot_plants",
                            "name": "Pot Plants",
                            "duration": 50,
                            "volume": 1.34,
                        }
                    ],
                    "run": {"duration": 50},
                    "zone_ids": ["pot_plants"],
                    "schedule": {
                        "index": 0,
                        "schedule_id": "pots_dawn",
                        "name": "Dawn",
                    },
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-10-31 05:46:14"),
                "data": {
                    "iu_id": "c1_z1",
                    "id": "1_pot_plants",
                    "type": 1,
                    "duration": 0,
                    "volume": 1.34,
                    "flow_rate": 1.608,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Green House",
                    },
                    "zone": {"index": 0, "zone_id": "pot_plants", "name": "Pot Plants"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-10-31 05:46:24"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 1.34,
                    "flow_rate": 321.705,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Green House",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
        ]


async def test_volume_limit(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test volume limit"""

    def read_data(
        file: str,
    ) -> Iterator[tuple[int, datetime, str, str]]:
        """Read data from the log file"""
        with open(file, encoding="utf-8") as fhd:
            for line in fhd:
                if line.startswith("#"):
                    continue
                data = line.strip().split(";")
                data = [s.strip() for s in data]
                if len(data) >= 6:
                    op = int(data[0])
                    dts = dt.as_local(datetime.fromisoformat(data[1]))
                    adjustment = data[4]
                    volume = data[5]
                    yield (op, dts, adjustment, volume)

    async with IUExam(hass, "test_volume_limit.yaml") as exam:
        await exam.load_component("input_text")

        event_data: list[dict] = []

        def handle_valve_event(event: ha.Event):
            nonlocal event_data
            event_data.append(
                {
                    "event_type": event.event_type,
                    "event_time": exam.virtual_time,
                    "data": event.data,
                }
            )
            if event.data["iu_id"].startswith("c1_z"):
                zone_volumes.append(event.data["volume"])
                zone_flows.append(event.data["flow_rate"])
            elif event.data["iu_id"] == "c1_m":
                controller_volumes.append(event.data["volume"])
                controller_flows.append(event.data["flow_rate"])

        hass.bus.async_listen(f"{DOMAIN}_{EVENT_VALVE_OFF}", handle_valve_event)

        def handle_finish_event(event: ha.Event):
            nonlocal event_data
            event_data.append(
                {
                    "event_type": event.event_type,
                    "event_time": exam.virtual_time,
                    "data": event.data,
                }
            )
            sequence_volumes.append(event.data["volume"])

        hass.bus.async_listen(f"{DOMAIN}_{EVENT_FINISH}", handle_finish_event)

        await exam.begin_test(1)
        # pylint: disable=unused-variable
        controller_volumes: list[float] = []
        controller_flows: list[float] = []
        zone_volumes: list[float] = []
        zone_flows: list[float] = []
        sequence_volumes: list[float] = []

        with patch.object(IUVolume, "event_hook") as mock:
            event_time: datetime = None
            trackers_processed: int = 0

            def state_change(event: ha.Event) -> ha.Event:
                nonlocal event_time, trackers_processed
                event.time_fired_timestamp = event_time.timestamp()
                trackers_processed += 1
                return event

            mock.side_effect = state_change

            for op, event_time, adjustment, volume in read_data(
                "tests/logs/volume_limit_sensor.log"
            ):

                await exam.run_until(event_time)

                if op == 0:
                    await set_sensor(hass, "input_text.dummy_sensor", volume)
                    await exam.call(
                        SERVICE_TIME_ADJUST,
                        {
                            "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                            "sequence_id": [1, 2],
                            "percentage": adjustment,
                        },
                    )
                    continue
                elif op == 2:
                    await set_sensor(hass, "input_text.dummy_sensor", volume)
                    while trackers_processed < IUVolume.trackers:
                        await asyncio.sleep(0)
                    trackers_processed = 0
                    await exam.run_until(event_time)
                else:
                    continue

        assert controller_volumes == [238.248]
        assert controller_flows == [399.709]
        assert zone_volumes == [100.036, 136.307]
        assert zone_flows == [6.517, 6.815]
        assert sequence_volumes == [236.343]

        await exam.finish_test()

        exam.check_summary()

        event_data.sort(key=lambda x: x["event_time"])
        assert event_data == [
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-11-04 11:15:21"),
                "data": {
                    "iu_id": "c1_z1",
                    "id": "1_upper_beds",
                    "type": 1,
                    "duration": 0,
                    "volume": 100.036,
                    "flow_rate": 6.517,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Green House",
                    },
                    "zone": {"index": 0, "zone_id": "upper_beds", "name": "Upper Beds"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_finish",
                "event_time": mk_local("2025-11-04 11:35:31"),
                "data": {
                    "iu_id": "c1_s1",
                    "id": "1_vege_beds",
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                    "volume": 236.343,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Green House",
                    },
                    "sequence": {
                        "index": 0,
                        "sequence_id": "vege_beds",
                        "name": "Vege Beds",
                    },
                    "zones": [
                        {
                            "index": 0,
                            "zone_id": "upper_beds",
                            "name": "Upper Beds",
                            "duration": 921,
                            "volume": 100.036,
                        },
                        {
                            "index": 1,
                            "zone_id": "lower_beds",
                            "name": "Lower Beds",
                            "duration": 1200,
                            "volume": 136.307,
                        },
                    ],
                    "run": {"duration": 2131},
                    "zone_ids": ["lower_beds", "upper_beds"],
                    "schedule": {
                        "index": 0,
                        "schedule_id": "vege_beds_dawn",
                        "name": "Dawn",
                    },
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-11-04 11:35:31"),
                "data": {
                    "iu_id": "c1_z2",
                    "id": "1_lower_beds",
                    "type": 1,
                    "duration": 0,
                    "volume": 136.307,
                    "flow_rate": 6.815,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Green House",
                    },
                    "zone": {"index": 1, "zone_id": "lower_beds", "name": "Lower Beds"},
                    "entity_id": None,
                },
            },
            {
                "event_type": "irrigation_unlimited_valve_off",
                "event_time": mk_local("2025-11-04 11:35:41"),
                "data": {
                    "iu_id": "c1_m",
                    "id": "1",
                    "type": 1,
                    "duration": 0,
                    "volume": 238.248,
                    "flow_rate": 399.709,
                    "controller": {
                        "index": 0,
                        "controller_id": "1",
                        "name": "Green House",
                    },
                    "zone": {"index": None, "zone_id": None, "name": None},
                    "entity_id": None,
                },
            },
        ]


async def test_volume_live_history(hass: ha.HomeAssistant, allow_memory_db):
    """Test volume with live history"""

    def read_data(
        file: str,
    ) -> Iterator[tuple[int, datetime, str, str]]:
        """Read data from the log file"""
        with open(file, encoding="utf-8") as fhd:
            for line in fhd:
                if line.startswith("#"):
                    continue
                data = line.strip().split(";")
                data = [s.strip() for s in data]
                if len(data) >= 6:
                    op = int(data[0])
                    dts = dt.as_local(datetime.fromisoformat(data[1]))
                    adjustment = data[4]
                    volume = data[5]
                    yield (op, dts, adjustment, volume)

    async with IUExam(hass, "test_volume_live_history.yaml") as exam:
        await exam.load_dependencies()
        await exam.load_component("input_text")

        await exam.begin_test(1)
        with patch.object(IUVolume, "event_hook") as mock:
            event_time: datetime = None
            trackers_processed: int = 0

            def state_change(event: ha.Event) -> ha.Event:
                nonlocal event_time, trackers_processed
                event.time_fired_timestamp = event_time.timestamp()
                trackers_processed += 1
                return event

            mock.side_effect = state_change

            for op, event_time, adjustment, volume in read_data(
                "tests/logs/volume_live_history_sensor.log"
            ):
                await exam.run_until(event_time)

                if op == 0:
                    await set_sensor(hass, "input_text.dummy_sensor", volume)
                    await exam.call(
                        SERVICE_TIME_ADJUST,
                        {
                            "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                            "sequence_id": [1],
                            "percentage": adjustment,
                        },
                    )
                    continue
                elif op == 2:
                    await set_sensor(hass, "input_text.dummy_sensor", volume)
                    while trackers_processed < IUVolume.trackers:
                        await asyncio.sleep(0)
                    trackers_processed = 0
                else:
                    continue

        await exam.run_until("2025-11-16 20:05:00")
        d = dt.utcnow()
        exam.coordinator.history.muster(d, True)
        await exam.coordinator.history._async_update_history(d)

        # Strip dates and duration from history
        hist = copy.deepcopy(exam.coordinator.history._cache)
        for entity, history in hist.items():
            for id, timeline in enumerate(history["timeline"]):
                del hist[entity]["timeline"][id]["start"]
                del hist[entity]["timeline"][id]["end"]
            history["today_on"] = history["today_on"].volume
        assert hist == {
            "binary_sensor.irrigation_unlimited_c1_m": {
                "timeline": [
                    {
                        "schedule": None,
                        "schedule_name": "Pot Plants",
                        "adjustment": "",
                        "volume": 1.133,
                        "flow_rate": 50.985,
                    },
                    {
                        "schedule": None,
                        "schedule_name": "Pot Plants",
                        "adjustment": "",
                        "volume": 1.21,
                        "flow_rate": 55.139,
                    },
                ],
                "today_on": 2.343,
            },
            "binary_sensor.irrigation_unlimited_c1_z1": {
                "timeline": [
                    {
                        "schedule": 1,
                        "schedule_name": "Dawn",
                        "adjustment": "%100.0",
                        "volume": 1.133,
                        "flow_rate": 1.133,
                    },
                    {
                        "schedule": 2,
                        "schedule_name": "Dusk",
                        "adjustment": "%99.0",
                        "volume": 1.21,
                        "flow_rate": 1.231,
                    },
                ],
                "today_on": 2.343,
            },
            "binary_sensor.irrigation_unlimited_c1_s1": {
                "timeline": [
                    {
                        "schedule": 1,
                        "schedule_name": "Dawn",
                        "adjustment": "",
                        "volume": 1.133,
                        "flow_rate": None,
                    },
                    {
                        "schedule": 2,
                        "schedule_name": "Dusk",
                        "adjustment": "",
                        "volume": 1.21,
                        "flow_rate": None,
                    },
                ],
                "today_on": 2.343,
            },
        }
        assert (
            exam.coordinator.history.today_total_volume(
                "binary_sensor.irrigation_unlimited_c1_m"
            )
            == 2.343
        )
        assert (
            exam.coordinator.history.today_total_volume(
                "binary_sensor.irrigation_unlimited_c1_z1"
            )
            == 2.343
        )
        assert (
            exam.coordinator.history.today_total_volume(
                "binary_sensor.irrigation_unlimited_c1_s1"
            )
            == 2.343
        )

        await exam.finish_test()

        exam.check_summary()
