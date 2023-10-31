"""irrigation_unlimited volume test module"""
from unittest.mock import patch
from datetime import datetime
import homeassistant.core as ha
from homeassistant.util import dt
from custom_components.irrigation_unlimited.const import (
    SERVICE_TIME_ADJUST,
)
from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IULogger,
)
from tests.iu_test_support import IUExam

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
                assert mock_meter_value.call_count == 1
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
                assert sta.attributes["volume"] == 10.000
                await exam.finish_test()

                # Sensor ends with bad value
                await exam.begin_test(5)
                await set_sensor(hass, "input_text.dummy_sensor_1", "621.505")
                await exam.run_until("2021-01-04 06:10")
                await set_sensor(hass, "input_text.dummy_sensor_1", "zzz")
                await exam.run_until("2021-01-04 06:45")
                assert mock_meter_value.call_count == 2
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
                assert sta.attributes["volume"] is None
                await exam.finish_test()

                # Sensor goes MIA
                calls_id = mock_meter_id.call_count
                await exam.begin_test(6)
                await set_sensor(hass, "input_text.dummy_sensor_1", "524.941")
                await exam.run_until("2021-01-04 06:09")
                old_id = exam.coordinator.controllers[0].zones[0].volume._sensor_id
                try:
                    exam.coordinator.controllers[0].zones[
                        0
                    ].volume._sensor_id = "input_text.does_not_exist"
                    await exam.run_until("2021-01-04 06:10")
                    assert mock_meter_id.call_count == calls_id
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
                await exam.begin_test(7)
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
                assert mock_meter_value.call_count == 2
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
                assert sta.attributes["volume"] == 10.998
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
                assert sta.attributes["volume"] == 4.772
                assert mock_meter_id.call_count == calls_id + 1
                await exam.finish_test()

                exam.check_summary()


async def test_volume_extensive(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test exhaustive volume class test."""

    async with IUExam(hass, "test_volume_extensive.yaml") as exam:

        def read_data(file: str) -> tuple[datetime, str, str]:
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

        await exam.load_component("input_text")

        await exam.begin_test(1)
        # pylint: disable=unused-variable
        controller_volumes: list[float] = []
        controller_flows: list[float] = []
        zone_volumes: list[float] = []
        zone_flows: list[float] = []
        zone: int = None
        for dts, value, sensor in read_data("tests/logs/volume_sensor.log"):
            await exam.run_until(dts)

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
                sta = hass.states.get(f"binary_sensor.irrigation_unlimited_c1_z{zone}")
                zone_volumes.append(sta.attributes["volume"])
                zone_flows.append(sta.attributes["flow_rate"])
                sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
                controller_volumes.append(sta.attributes["volume"])
                controller_flows.append(sta.attributes["flow_rate"])
            else:
                await set_sensor(hass, "input_text.dummy_sensor", value)

        volume_results = [
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
        assert controller_volumes == volume_results
        assert zone_volumes == volume_results

        flow_results = [
            0.284,
            0.403,
            0.133,
            0.158,
            0.1,
            0.097,
            0.158,
            0.124,
            0.357,
            0.3,
            0.069,
            0.16,
            1.118,
        ]
        assert controller_flows == flow_results
        assert zone_flows == flow_results

        await exam.finish_test()

        exam.check_summary()
