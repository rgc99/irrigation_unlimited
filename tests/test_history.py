"""Test irrigation_unlimited history."""
from unittest.mock import patch
from datetime import datetime
from homeassistant.components.recorder.models import LazyState
import pytest
import json
import homeassistant.core as ha
from homeassistant.config import (
    load_yaml_config_file,
    async_process_ha_core_config,
)
from homeassistant.setup import async_setup_component

from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
)
from custom_components.irrigation_unlimited.const import DOMAIN, COORDINATOR
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA
from tests.iu_test_support import quiet_mode, test_config_dir

quiet_mode()


@pytest.fixture(name="mock_history")
def mock_history():
    with patch(
        "homeassistant.components.recorder.history.state_changes_during_period"
    ) as mock:

        def s2dt(adate: str) -> datetime:
            return datetime.fromisoformat(adate + "+00:00")

        result = {}
        id = "binary_sensor.irrigation_unlimited_c1_z1"
        result[id] = []
        result[id].append(ha.State(id, "on", [], s2dt("2021-01-04 04:30:00")))
        result[id].append(ha.State(id, "off", [], s2dt("2021-01-04 04:32:00")))
        result[id].append(ha.State(id, "on", [], s2dt("2021-01-04 05:30:00")))
        result[id].append(ha.State(id, "off", [], s2dt("2021-01-04 05:32:00")))
        id = "binary_sensor.irrigation_unlimited_c1_z2"
        result[id] = []
        result[id].append(ha.State(id, "on", [], s2dt("2021-01-04 04:35:00")))
        result[id].append(ha.State(id, "off", [], s2dt("2021-01-04 04:38:00")))
        result[id].append(ha.State(id, "on", [], s2dt("2021-01-04 05:35:00")))
        result[id].append(ha.State(id, "off", [], s2dt("2021-01-04 05:38:00")))
        result[id].append(ha.State(id, "on", [], s2dt("2021-01-04 05:40:00")))
        mock.return_value = result
        yield


async def test_history(hass: ha.HomeAssistant, mock_history):

    full_path = test_config_dir + "test_history.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    if ha.DOMAIN in config:
        await async_process_ha_core_config(hass, config[ha.DOMAIN])
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.attributes["today_total"] == 4.0
