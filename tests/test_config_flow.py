"""irrigation_unlimited config flow test"""

# pylint: disable=unused-import
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_EXPORT_CONFIG,
    SERVICE_ENABLE,
    SERVICE_DISABLE,
)
from tests.iu_test_support import IUExam, mk_utc, mk_local

IUExam.quiet_mode()


async def test_export_config(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test export_config action"""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_export_config.yaml") as exam:

        await exam.begin_test(1)
        data = await exam.call(
            SERVICE_EXPORT_CONFIG,
            None,
            True,
        )
        assert data == {
            "controllers": [
                {
                    "name": "Test controller 1",
                    "zones": [
                        {"name": "Zone 1", "zone_id": "1"},
                        {"name": "Zone 2", "zone_id": "2"},
                    ],
                    "sequences": [
                        {
                            "name": "Sequence 1",
                            "delay": "0:01:00",
                            "zones": [
                                {"zone_id": "1", "duration": "0:06:00"},
                                {"zone_id": "2", "duration": "0:12:00"},
                            ],
                            "schedules": [
                                {
                                    "name": "Schedule 1",
                                    "time": "{'sun': 'sunrise', 'before': datetime.timedelta(seconds=2)}",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        await exam.finish_test()
        exam.check_summary()


async def test_export_config_cycle(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test export_config serialises the cycle-and-soak block at the sequence
    and per-zone level."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_export_config_cycle.yaml") as exam:
        data = await exam.call(SERVICE_EXPORT_CONFIG, None, True)
        sequence = data["controllers"][0]["sequences"][0]
        assert sequence["cycle"] == {
            "max_duration": "0:15:00",
            "min_duration": "0:10:00",
            "min_soak": "1:00:00",
        }
        # Zone 2 overrides max_duration; the other zones carry no cycle block
        zones = sequence["zones"]
        assert "cycle" not in zones[0]
        assert zones[1]["cycle"] == {"max_duration": "0:08:00"}
        assert "cycle" not in zones[2]


async def test_helpers(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test helpers"""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_helper.yaml") as exam:

        await exam.begin_test(1)

        # Initial state should be on
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes["enabled"] is True
        assert hass.states.get("switch.zone_1_enabled").state == "on"

        # Disable zone 1
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes["enabled"] is False
        # assert hass.states.get("switch.zone_1_enabled").state == "off"

        # Reenable zone 1
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes["enabled"] is True
        assert hass.states.get("switch.zone_1_enabled").state == "on"

        # Disable zone 1 via helper
        await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.zone_1_enabled"}, True)
        await hass.async_block_till_done()
        assert hass.states.get("switch.zone_1_enabled").state == "off"
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes["enabled"] is False

        # Enable zone 1
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes["enabled"] is True
        # assert hass.states.get("switch.zone_1_enabled").state == "on"

        # Disable zone 1
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes["enabled"] is False
        assert hass.states.get("switch.zone_1_enabled").state == "off"

        # Enable zone 1 via helper
        await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.zone_1_enabled"}, True)
        await hass.async_block_till_done()
        assert hass.states.get("switch.zone_1_enabled").state == "on"
        assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes["enabled"] is True

        await exam.finish_test()
        exam.check_summary()
