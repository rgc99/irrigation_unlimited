"""Test irrigation_unlimited history."""
from unittest.mock import patch
from datetime import datetime
from typing import List
import json
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

# pylint: disable=unused-argument
def hist_data(
    hass,
    start_time: datetime,
    end_time: datetime,
    entity_ids: List[str],
    significant_changes_only: bool,
) -> dict:
    """Return dummy history data"""

    def s2dt(adate: str) -> datetime:
        return datetime.fromisoformat(adate + "+00:00")

    result = {}
    idx = "binary_sensor.irrigation_unlimited_c1_z1"
    if idx in entity_ids:
        result[idx] = []
        if start_time >= s2dt("2020-12-28 00:00:00") and end_time <= s2dt(
            "2021-01-04 23:59:59"
        ):
            result[idx].append(ha.State(idx, "on", None, s2dt("2021-01-04T04:30:00")))
            result[idx].append(ha.State(idx, "off", None, s2dt("2021-01-04T04:32:00")))
            result[idx].append(ha.State(idx, "on", None, s2dt("2021-01-04T05:30:00")))
            result[idx].append(ha.State(idx, "off", None, s2dt("2021-01-04T05:32:00")))
    idx = "binary_sensor.irrigation_unlimited_c1_z2"
    if idx in entity_ids:
        result[idx] = []
        if start_time >= s2dt("2020-12-28 00:00:00") and end_time <= s2dt(
            "2021-01-04 23:59:59"
        ):
            result[idx].append(ha.State(idx, "on", None, s2dt("2021-01-04T04:35:00")))
            result[idx].append(ha.State(idx, "off", None, s2dt("2021-01-04T04:38:00")))
            result[idx].append(ha.State(idx, "on", None, s2dt("2021-01-04T05:35:00")))
            result[idx].append(ha.State(idx, "off", None, s2dt("2021-01-04T05:38:00")))
            result[idx].append(ha.State(idx, "on", None, s2dt("2021-01-04T05:40:00")))
            result[idx].append(ha.State(idx, "off", None, s2dt("2021-01-04T05:45:00")))
    return result


@pytest.fixture(name="mock_history")
def mock_history():
    """Patch HA history and return dummy data"""
    with patch(
        "homeassistant.components.recorder.history.get_significant_states"
    ) as mock:
        mock.side_effect = hist_data
        yield


async def test_history(hass: ha.HomeAssistant, skip_dependencies, mock_history):
    """Test out the history caching and timeline"""
    # pylint: disable=redefined-outer-name

    full_path = test_config_dir + "test_history.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    start_time = await begin_test(1, coordinator)
    start_time = await run_for_1_tick(hass, coordinator, start_time, True)

    state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert state.attributes["today_total"] == 4.0
    timeline = json.dumps(
        [
            {"start": "2021-01-04T04:30:00+00:00", "end": "2021-01-04T04:32:00+00:00"},
            {"start": "2021-01-04T05:30:00+00:00", "end": "2021-01-04T05:32:00+00:00"},
            {"start": "2021-01-04T06:05:00+00:00", "end": "2021-01-04T06:15:00+00:00"},
            {"start": "2021-01-05T06:05:00+00:00", "end": "2021-01-05T06:15:00+00:00"},
            {"start": "2021-01-06T06:05:00+00:00", "end": "2021-01-06T06:15:00+00:00"},
        ],
        default=str,
    )
    assert state.attributes["timeline"] == timeline

    state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
    assert state.attributes["today_total"] == 11.0
    timeline = json.dumps(
        [
            {"start": "2021-01-04T04:35:00+00:00", "end": "2021-01-04T04:38:00+00:00"},
            {"start": "2021-01-04T05:35:00+00:00", "end": "2021-01-04T05:38:00+00:00"},
            {"start": "2021-01-04T05:40:00+00:00", "end": "2021-01-04T05:45:00+00:00"},
            {"start": "2021-01-04T06:10:00+00:00", "end": "2021-01-04T06:20:00+00:00"},
            {"start": "2021-01-05T06:10:00+00:00", "end": "2021-01-05T06:20:00+00:00"},
            {"start": "2021-01-06T06:10:00+00:00", "end": "2021-01-06T06:20:00+00:00"},
        ],
        default=str,
    )
    assert state.attributes["timeline"] == timeline

    await finish_test(hass, coordinator, start_time, True)

    # Midnight rollover
    start_time = await begin_test(2, coordinator)
    start_time = await run_for_1_tick(hass, coordinator, start_time, True)

    state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert state.attributes["today_total"] == 4.0
    timeline = json.dumps(
        [
            {"start": "2021-01-04T04:30:00+00:00", "end": "2021-01-04T04:32:00+00:00"},
            {"start": "2021-01-04T05:30:00+00:00", "end": "2021-01-04T05:32:00+00:00"},
            {"start": "2021-01-05T06:05:00+00:00", "end": "2021-01-05T06:15:00+00:00"},
            {"start": "2021-01-06T06:05:00+00:00", "end": "2021-01-06T06:15:00+00:00"},
            {"start": "2021-01-07T06:05:00+00:00", "end": "2021-01-07T06:15:00+00:00"},
        ],
        default=str,
    )
    assert state.attributes["timeline"] == timeline

    state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
    assert state.attributes["today_total"] == 11.0
    timeline = json.dumps(
        [
            {"start": "2021-01-04T04:35:00+00:00", "end": "2021-01-04T04:38:00+00:00"},
            {"start": "2021-01-04T05:35:00+00:00", "end": "2021-01-04T05:38:00+00:00"},
            {"start": "2021-01-04T05:40:00+00:00", "end": "2021-01-04T05:45:00+00:00"},
            {"start": "2021-01-05T06:10:00+00:00", "end": "2021-01-05T06:20:00+00:00"},
            {"start": "2021-01-06T06:10:00+00:00", "end": "2021-01-06T06:20:00+00:00"},
            {"start": "2021-01-07T06:10:00+00:00", "end": "2021-01-07T06:20:00+00:00"},
        ],
        default=str,
    )
    assert state.attributes["timeline"] == timeline

    start_time = await run_until(
        hass,
        coordinator,
        start_time,
        datetime.fromisoformat("2021-01-05T00:00:00+00:00"),
        True,
    )
    state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert state.attributes["today_total"] == 0.0
    timeline = json.dumps(
        [
            {"start": "2021-01-05T06:05:00+00:00", "end": "2021-01-05T06:15:00+00:00"},
            {"start": "2021-01-06T06:05:00+00:00", "end": "2021-01-06T06:15:00+00:00"},
            {"start": "2021-01-07T06:05:00+00:00", "end": "2021-01-07T06:15:00+00:00"},
        ],
        default=str,
    )
    assert state.attributes["timeline"] == timeline

    state = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
    assert state.attributes["today_total"] == 0.0
    timeline = json.dumps(
        [
            {"start": "2021-01-05T06:10:00+00:00", "end": "2021-01-05T06:20:00+00:00"},
            {"start": "2021-01-06T06:10:00+00:00", "end": "2021-01-06T06:20:00+00:00"},
            {"start": "2021-01-07T06:10:00+00:00", "end": "2021-01-07T06:20:00+00:00"},
        ],
        default=str,
    )
    assert state.attributes["timeline"] == timeline

    await finish_test(hass, coordinator, start_time, True)

    check_summary(full_path, coordinator)
