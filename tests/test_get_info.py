"""Test integration_unlimited get_config service call."""

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
async def test_service_get_config(
    hass: ha.HomeAssistant,
    skip_dependencies,
    skip_history,
):
    """Test get_info service call."""

    async with IUExam(hass, "service_get_info.yaml") as exam:
        await exam.begin_test(1)
        data = await hass.services.async_call(
            "irrigation_unlimited", "get_info", None, True, return_response=True
        )
        assert data == {
            "version": "1.0.0",
            "controllers": [
                {
                    "index": 0,
                    "controller_id": "controller_1",
                    "name": "Test Controller 1",
                    "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                    "zones": [
                        {
                            "index": 0,
                            "zone_id": "zone_1",
                            "name": "Zone 1",
                            "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                        },
                        {
                            "index": 1,
                            "zone_id": "2",
                            "name": "Zone 2",
                            "entity_id": "binary_sensor.irrigation_unlimited_c1_z2",
                        },
                        {
                            "index": 2,
                            "zone_id": "3",
                            "name": "Zone 3",
                            "entity_id": "binary_sensor.irrigation_unlimited_c1_z3",
                        },
                        {
                            "index": 3,
                            "zone_id": "zone_4",
                            "name": "Zone 4",
                            "entity_id": "binary_sensor.irrigation_unlimited_c1_z4",
                        },
                    ],
                    "sequences": [
                        {
                            "index": 0,
                            "name": "Seq 1",
                            "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                            "zones": [
                                {"index": 0, "zone_ids": ["zone_1"]},
                                {"index": 1, "zone_ids": ["2", "3"]},
                                {"index": 2, "zone_ids": ["zone_4"]},
                            ],
                        }
                    ],
                }
            ],
        }
        await exam.finish_test()
        exam.check_summary()
