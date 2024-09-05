"""Test integration_unlimited reload service calls."""

from datetime import timedelta
import pytest
import homeassistant.core as ha
from homeassistant.util import dt
from custom_components.irrigation_unlimited.const import (
    SERVICE_DISABLE,
    SERVICE_SUSPEND,
    SERVICE_TIME_ADJUST,
)
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


# pylint: disable=unused-argument
async def test_service_reload_basic(
    hass: ha.HomeAssistant,
    skip_dependencies,
    skip_history,
):
    """Test reload service call."""

    async with IUExam(hass, "mock_config.yaml") as exam:
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.attributes["friendly_name"] == "Controller 1"
        assert sta.attributes["zone_count"] == 1

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["friendly_name"] == "Zone 1"
        assert sta.attributes["schedule_count"] == 1

        await exam.reload("service_reload.yaml")

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.attributes["friendly_name"] == "The First Controller"
        assert sta.attributes["zone_count"] == 1

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["friendly_name"] == "The First Zone"
        assert sta.attributes["schedule_count"] == 2

        await exam.begin_test(1)
        await exam.finish_test()

        exam.check_summary()


async def test_service_reload_survival(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test reload preserves current state"""

    async with IUExam(hass, "mock_config.yaml") as exam:
        adate = dt.now().replace(microsecond=0)
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 1,
                "percentage": "15",
            },
        )
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 1,
            },
        )

        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 1,
                "until": adate + timedelta(hours=6),
            },
        )

        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "percentage": "25",
            },
        )
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
            },
        )

        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "until": adate + timedelta(hours=12),
            },
        )

        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "percentage": "50",
            },
        )
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
            },
        )

        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "until": adate + timedelta(hours=18),
            },
        )

        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
            },
        )
        await exam.call(
            SERVICE_SUSPEND,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "until": adate + timedelta(hours=24),
            },
        )
        await exam.reload("service_reload_survival.yaml")
        assert exam.coordinator.controllers[0].enabled is False
        assert exam.coordinator.controllers[0].suspended == adate + timedelta(hours=24)
        assert exam.coordinator.controllers[0].sequences[0].enabled is False
        assert exam.coordinator.controllers[0].sequences[
            0
        ].suspended == adate + timedelta(hours=12)
        assert str(exam.coordinator.controllers[0].sequences[0].adjustment) == "%25.0"
        assert exam.coordinator.controllers[0].sequences[0].zones[0].enabled is False
        assert exam.coordinator.controllers[0].sequences[0].zones[
            0
        ].suspended == adate + timedelta(hours=6)
        assert (
            str(exam.coordinator.controllers[0].sequences[0].zones[0].adjustment)
            == "%15.0"
        )
        assert exam.coordinator.controllers[0].zones[0].enabled is False
        assert exam.coordinator.controllers[0].zones[0].suspended == adate + timedelta(
            hours=18
        )
        assert str(exam.coordinator.controllers[0].zones[0].adjustment) == "%50.0"

        await exam.run_test(1)

        exam.check_summary()


async def test_service_reload_while_on(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Test reload while zone is on"""
    async with IUExam(hass, "mock_config.yaml") as exam:
        # Reload while entities are on.
        await exam.reload("service_reload_1.yaml")
        await exam.begin_test(1)
        await exam.run_until("2021-01-04 06:10:00")
        assert exam.coordinator.controllers[0].is_on is True
        assert exam.coordinator.controllers[0].zones[0].is_on is True
        await exam.reload("service_reload_1.yaml")
        assert exam.coordinator.controllers[0].is_on is False
        assert exam.coordinator.controllers[0].zones[0].is_on is False
        await exam.run_all()
        exam.check_summary()


async def test_service_reload_error(
    hass: ha.HomeAssistant,
    skip_dependencies,
    skip_history,
):
    """Test reload service call on a bad config file."""

    async with IUExam(hass, "mock_config.yaml") as exam:
        with pytest.raises(KeyError, match="controllers"):
            await exam.reload("service_reload_error.yaml")


async def test_service_reload_extend_shrink(
    hass: ha.HomeAssistant,
    skip_dependencies,
    skip_history,
):
    """Test reload service call expanding and reducing entities."""

    async with IUExam(hass, "mock_config.yaml") as exam:
        await exam.reload("service_reload_2.yaml")
        await exam.run_all()
        exam.check_summary()

        await exam.reload("service_reload_3.yaml")
        await exam.run_all()
        exam.check_summary()

        await exam.reload("service_reload_1.yaml")
        await exam.run_all()
        exam.check_summary()


async def test_service_reload_shrink_while_on(
    hass: ha.HomeAssistant,
    skip_dependencies,
    skip_history,
):
    """Test reload service call reducing entities while on."""

    async with IUExam(hass, "mock_config.yaml") as exam:
        # Reload while entities are on.
        await exam.reload("service_reload_while_on.yaml")
        await exam.begin_test(1)
        await exam.run_until("2021-01-04 06:16:00")

        await exam.reload("service_reload_1.yaml")
        # The reload mid stream has blown away our test and results. So
        # don't attempt to finish or check results, there are none.
        # await exam.finish_test()
        # check_summary(full_path)


async def test_service_reload_multi(hass: ha.HomeAssistant, skip_history):
    """Test reliablity on multiple reload calls"""

    async with IUExam(hass, "service_reload_multi.yaml") as exam:
        await exam.begin_test(1)
        await exam.finish_test()
        await exam.reload("service_reload_multi.yaml")
        assert exam.coordinator.controllers[0].master_sensor is not None
        assert exam.coordinator.controllers[0].zones[0].zone_sensor is not None
        await exam.reload("service_reload_multi.yaml")
        assert exam.coordinator.controllers[0].master_sensor is not None
        assert exam.coordinator.controllers[0].zones[0].zone_sensor is not None
        await exam.reload("service_reload_multi.yaml")
        assert exam.coordinator.controllers[0].master_sensor is not None
        assert exam.coordinator.controllers[0].zones[0].zone_sensor is not None
        await exam.reload("service_reload_multi.yaml")
        assert exam.coordinator.controllers[0].master_sensor is not None
        assert exam.coordinator.controllers[0].zones[0].zone_sensor is not None
        await exam.reload("service_reload_multi.yaml")
        assert exam.coordinator.controllers[0].master_sensor is not None
        assert exam.coordinator.controllers[0].zones[0].zone_sensor is not None
        await exam.reload("service_reload_multi.yaml")
        assert exam.coordinator.controllers[0].master_sensor is not None
        assert exam.coordinator.controllers[0].zones[0].zone_sensor is not None
        await exam.reload("service_reload_multi.yaml")
        assert exam.coordinator.controllers[0].master_sensor is not None
        assert exam.coordinator.controllers[0].zones[0].zone_sensor is not None
        await exam.reload("service_reload_multi.yaml")
        assert exam.coordinator.controllers[0].master_sensor is not None
        assert exam.coordinator.controllers[0].zones[0].zone_sensor is not None
        await exam.reload("service_reload_multi.yaml")
        assert exam.coordinator.controllers[0].master_sensor is not None
        assert exam.coordinator.controllers[0].zones[0].zone_sensor is not None
        await exam.reload("service_reload_multi.yaml")
        assert exam.coordinator.controllers[0].master_sensor is not None
        assert exam.coordinator.controllers[0].zones[0].zone_sensor is not None
        # exam.check_summary()
