"""Test irrigation_unlimited history."""
from unittest.mock import patch
from datetime import datetime
import pytest
import homeassistant.core as ha
from homeassistant.config import load_yaml_config_file
from homeassistant.setup import async_setup_component

from custom_components.irrigation_unlimited.irrigation_unlimited import IUCoordinator
from custom_components.irrigation_unlimited.const import COORDINATOR, DOMAIN
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA
from tests.iu_test_support import (
    begin_test,
    check_summary,
    finish_test,
    quiet_mode,
    run_for_1_tick,
    run_until,
    test_config_dir,
)

quiet_mode()


@pytest.fixture(name="mock_history")
def mock_history():
    with patch(
        "homeassistant.components.recorder.history.state_changes_during_period"
    ) as mock:
        mock.side_effect = hist_data
        yield


def hist_data(hass, start_time: datetime, end_time: datetime, entity_id: str):
    def s2dt(adate: str) -> datetime:
        return datetime.fromisoformat(adate + "+00:00")

    result = {}
    id = "binary_sensor.irrigation_unlimited_c1_z1"
    if entity_id == id:
        result[id] = []
        if start_time >= s2dt("2021-01-04 00:00:00") and end_time <= s2dt(
            "2021-01-04 23:59:59"
        ):
            result[id].append(ha.State(id, "on", None, s2dt("2021-01-04 04:30:00")))
            result[id].append(ha.State(id, "off", None, s2dt("2021-01-04 04:32:00")))
            result[id].append(ha.State(id, "on", None, s2dt("2021-01-04 05:30:00")))
            result[id].append(ha.State(id, "off", None, s2dt("2021-01-04 05:32:00")))
    id = "binary_sensor.irrigation_unlimited_c1_z2"
    if entity_id == id:
        result[id] = []
        if start_time >= s2dt("2021-01-04 00:00:00") and end_time <= s2dt(
            "2021-01-04 23:59:59"
        ):
            result[id].append(ha.State(id, "on", None, s2dt("2021-01-04 04:35:00")))
            result[id].append(ha.State(id, "off", None, s2dt("2021-01-04 04:38:00")))
            result[id].append(ha.State(id, "on", None, s2dt("2021-01-04 05:35:00")))
            result[id].append(ha.State(id, "off", None, s2dt("2021-01-04 05:38:00")))
            result[id].append(ha.State(id, "on", None, s2dt("2021-01-04 05:40:00")))
    return result


async def test_history(hass: ha.HomeAssistant, skip_dependencies, mock_history):

    full_path = test_config_dir + "test_history.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    start_time = await begin_test(1, coordinator)
    start_time = await run_for_1_tick(hass, coordinator, start_time, True)
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.attributes["today_total"] == 4.0
    await finish_test(hass, coordinator, start_time, True)

    # Midnight rollover
    start_time = await begin_test(2, coordinator)
    start_time = await run_for_1_tick(hass, coordinator, start_time, True)
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.attributes["today_total"] == 4.0
    start_time = await run_until(
        hass,
        coordinator,
        start_time,
        datetime.fromisoformat("2021-01-05 00:00:00+00:00"),
        True,
    )
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.attributes["today_total"] == 0.0
    await finish_test(hass, coordinator, start_time, True)

    check_summary(full_path, coordinator)
