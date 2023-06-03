"""Test integration_unlimited reload service calls."""
from unittest.mock import patch
import pytest
import homeassistant.core as ha
from homeassistant.const import SERVICE_RELOAD
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


# pylint: disable=unused-argument
async def test_service_reload(
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

        full_path = exam.config_directory + "service_reload.yaml"
        with patch(
            "homeassistant.core.Config.path",
            return_value=full_path,
        ):
            await exam.call(SERVICE_RELOAD)
            sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
            assert sta.attributes["friendly_name"] == "The First Controller"
            assert sta.attributes["zone_count"] == 1

            sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
            assert sta.attributes["friendly_name"] == "The First Zone"
            assert sta.attributes["schedule_count"] == 2

            await exam.begin_test(1)
            await exam.finish_test()

            exam.check_summary(full_path)


async def test_service_reload_error(
    hass: ha.HomeAssistant,
    skip_dependencies,
    skip_history,
):
    """Test reload service call on a bad config file."""

    async with IUExam(hass, "mock_config.yaml") as exam:
        with patch(
            "homeassistant.core.Config.path",
            return_value=exam.config_directory + "service_reload_error.yaml",
        ):
            with pytest.raises(KeyError, match="controllers"):
                await exam.call(SERVICE_RELOAD)


async def test_service_reload_extend_shrink(
    hass: ha.HomeAssistant,
    skip_dependencies,
    skip_history,
):
    """Test reload service call expanding and reducing entities."""

    async with IUExam(hass, "mock_config.yaml") as exam:
        full_path = exam.config_directory + "service_reload_2.yaml"
        with patch(
            "homeassistant.core.Config.path",
            return_value=full_path,
        ):
            await exam.call(SERVICE_RELOAD)
            await exam.begin_test(1)
            await exam.finish_test()
            exam.check_summary(full_path)

        full_path = exam.config_directory + "service_reload_3.yaml"
        with patch(
            "homeassistant.core.Config.path",
            return_value=full_path,
        ):
            await exam.call(SERVICE_RELOAD)
            await exam.begin_test(1)
            await exam.finish_test()
            exam.check_summary(full_path)

        full_path = exam.config_directory + "service_reload_1.yaml"
        with patch(
            "homeassistant.core.Config.path",
            return_value=full_path,
        ):
            await exam.call(SERVICE_RELOAD)
            await exam.begin_test(1)
            await exam.finish_test()
            exam.check_summary(full_path)


async def test_service_reload_shrink_while_on(
    hass: ha.HomeAssistant,
    skip_dependencies,
    skip_history,
):
    """Test reload service call reducing entities while on."""

    async with IUExam(hass, "mock_config.yaml") as exam:
        full_path = exam.config_directory + "service_reload_while_on.yaml"
        with patch(
            "homeassistant.core.Config.path",
            return_value=full_path,
        ):
            await exam.call(SERVICE_RELOAD)

            # Reload while entities are on.
            await exam.begin_test(1)
            await exam.run_until("2021-01-04 06:16:00")

        full_path = exam.config_directory + "service_reload_1.yaml"
        with patch(
            "homeassistant.core.Config.path",
            return_value=full_path,
        ):
            await exam.call(SERVICE_RELOAD)

            # The reload mid stream has blown away our test and results. So
            # don't attempt to finish or check results, there are none.
            # await exam.finish_test()
            # check_summary(full_path)
