"""Test irrigation_unlimited entity operations."""
import pytest
from datetime import datetime, timedelta
import homeassistant.core as ha
from homeassistant.config import (
    load_yaml_config_file,
    async_process_ha_core_config,
)
from homeassistant.setup import async_setup_component
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    STATE_OFF,
    STATE_ON,
)

from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
)
from custom_components.irrigation_unlimited.const import (
    ATTR_ENABLED,
    ATTR_INDEX,
    DOMAIN,
    COORDINATOR,
)
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA
from custom_components.irrigation_unlimited.binary_sensor import RES_NOT_RUNNING
from tests.iu_test_support import (
    quiet_mode,
    begin_test,
    run_until,
    finish_test,
    test_config_dir,
    check_summary,
)

quiet_mode()


def hms_to_td(time: str) -> timedelta:
    t = datetime.strptime(time, "%H:%M:%S")
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)


async def test_entity(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test entity."""

    full_path = test_config_dir + "test_entity.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    if ha.DOMAIN in config:
        await async_process_ha_core_config(hass, config[ha.DOMAIN])
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    start_time = await begin_test(1, coordinator)

    next_time = await run_until(
        hass,
        coordinator,
        start_time,
        datetime.fromisoformat("2021-01-04 06:02:00+00:00"),
        True,
    )
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
    assert s.state == STATE_OFF
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["status"] == STATE_OFF
    assert s.attributes["zone_count"] == 2
    assert s.attributes["current_zone"] == RES_NOT_RUNNING
    assert s.attributes["percent_complete"] == 0
    assert s.attributes["next_zone"] == 1
    assert s.attributes["next_name"] == "First zone"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 06:03:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=14)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
    assert s.attributes[ATTR_ICON] == "mdi:water-off"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.state == STATE_OFF
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["zone_id"] == "1"
    assert s.attributes["status"] == STATE_OFF
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["schedule_count"] == 2
    assert s.attributes["current_schedule"] == RES_NOT_RUNNING
    assert s.attributes["percent_complete"] == 0
    assert s.attributes["next_schedule"] == 1
    assert s.attributes["next_name"] == "Morning 1"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 06:05:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=10)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "First zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-closed"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
    assert s.state == STATE_OFF
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 1
    assert s.attributes["zone_id"] == "2"
    assert s.attributes["status"] == STATE_OFF
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["schedule_count"] == 2
    assert s.attributes["current_schedule"] == RES_NOT_RUNNING
    assert s.attributes["percent_complete"] == 0
    assert s.attributes["next_schedule"] == 1
    assert s.attributes["next_name"] == "Morning 2"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 06:10:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=12)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-closed"

    next_time = await run_until(
        hass,
        coordinator,
        start_time,
        datetime.fromisoformat("2021-01-04 06:04:00+00:00"),
        True,
    )
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
    assert s.state == STATE_ON
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["status"] == STATE_ON
    assert s.attributes["zone_count"] == 2
    assert s.attributes["current_zone"] == 1
    assert s.attributes["current_name"] == "First zone"
    assert s.attributes["current_start"] == datetime.fromisoformat(
        "2021-01-04 06:03:00+00:00"
    )
    assert hms_to_td(s.attributes["current_duration"]) == timedelta(minutes=14)
    assert hms_to_td(s.attributes["time_remaining"]) == timedelta(minutes=13)
    assert s.attributes["percent_complete"] == 7
    assert s.attributes["next_zone"] == 2
    assert s.attributes["next_name"] == "Second zone"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 06:08:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=16)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
    assert s.attributes[ATTR_ICON] == "mdi:water"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.state == STATE_OFF
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["zone_id"] == "1"
    assert s.attributes["status"] == STATE_OFF
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["schedule_count"] == 2
    assert s.attributes["current_schedule"] == RES_NOT_RUNNING
    assert s.attributes["percent_complete"] == 0
    assert s.attributes["next_schedule"] == 1
    assert s.attributes["next_name"] == "Morning 1"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 06:05:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=10)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "First zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-closed"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
    assert s.state == STATE_OFF
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 1
    assert s.attributes["zone_id"] == "2"
    assert s.attributes["status"] == STATE_OFF
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["schedule_count"] == 2
    assert s.attributes["current_schedule"] == RES_NOT_RUNNING
    assert s.attributes["percent_complete"] == 0
    assert s.attributes["next_schedule"] == 1
    assert s.attributes["next_name"] == "Morning 2"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 06:10:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=12)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-closed"

    next_time = await run_until(
        hass,
        coordinator,
        next_time,
        datetime.fromisoformat("2021-01-04 06:07:00+00:00"),
        True,
    )
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
    assert s.state == STATE_ON
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["status"] == STATE_ON
    assert s.attributes["zone_count"] == 2
    assert s.attributes["current_zone"] == 1
    assert s.attributes["current_name"] == "First zone"
    assert s.attributes["current_start"] == datetime.fromisoformat(
        "2021-01-04 06:03:00+00:00"
    )
    assert hms_to_td(s.attributes["current_duration"]) == timedelta(minutes=14)
    assert hms_to_td(s.attributes["time_remaining"]) == timedelta(minutes=10)
    assert s.attributes["percent_complete"] == 28
    assert s.attributes["next_zone"] == 2
    assert s.attributes["next_name"] == "Second zone"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 06:08:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=16)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
    assert s.attributes[ATTR_ICON] == "mdi:water"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.state == STATE_ON
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["zone_id"] == "1"
    assert s.attributes["status"] == STATE_ON
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["current_schedule"] == 1
    assert s.attributes["current_name"] == "Morning 1"
    assert s.attributes["current_start"] == datetime.fromisoformat(
        "2021-01-04 06:05:00+00:00"
    )
    assert hms_to_td(s.attributes["current_duration"]) == timedelta(minutes=10)
    assert hms_to_td(s.attributes["time_remaining"]) == timedelta(minutes=8)
    assert s.attributes["percent_complete"] == 20
    assert s.attributes["next_schedule"] == 2
    assert s.attributes["next_name"] == "Afternoon 1"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 14:05:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=20)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "First zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-open"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
    assert s.state == STATE_OFF
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 1
    assert s.attributes["zone_id"] == "2"
    assert s.attributes["status"] == STATE_OFF
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["current_schedule"] == RES_NOT_RUNNING
    assert s.attributes["percent_complete"] == 0
    assert s.attributes["next_schedule"] == 1
    assert s.attributes["next_name"] == "Morning 2"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 06:10:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=12)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-closed"

    next_time = await run_until(
        hass,
        coordinator,
        start_time,
        datetime.fromisoformat("2021-01-04 06:12:00+00:00"),
        True,
    )
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
    assert s.state == STATE_ON
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["status"] == STATE_ON
    assert s.attributes["zone_count"] == 2
    assert s.attributes["current_zone"] == 1
    assert s.attributes["current_name"] == "First zone"
    assert s.attributes["current_start"] == datetime.fromisoformat(
        "2021-01-04 06:03:00+00:00"
    )
    assert hms_to_td(s.attributes["current_duration"]) == timedelta(minutes=14)
    assert hms_to_td(s.attributes["time_remaining"]) == timedelta(minutes=5)
    assert s.attributes["percent_complete"] == 64
    assert s.attributes["next_zone"] == 2
    assert s.attributes["next_name"] == "Second zone"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 06:08:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=16)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
    assert s.attributes[ATTR_ICON] == "mdi:water"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.state == STATE_ON
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["zone_id"] == "1"
    assert s.attributes["status"] == STATE_ON
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["current_schedule"] == 1
    assert s.attributes["current_name"] == "Morning 1"
    assert s.attributes["current_start"] == datetime.fromisoformat(
        "2021-01-04 06:05:00+00:00"
    )
    assert hms_to_td(s.attributes["current_duration"]) == timedelta(minutes=10)
    assert hms_to_td(s.attributes["time_remaining"]) == timedelta(minutes=3)
    assert s.attributes["percent_complete"] == 70
    assert s.attributes["next_schedule"] == 2
    assert s.attributes["next_name"] == "Afternoon 1"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 14:05:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=20)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "First zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-open"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
    assert s.state == STATE_ON
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 1
    assert s.attributes["zone_id"] == "2"
    assert s.attributes["status"] == STATE_ON
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["current_schedule"] == 1
    assert s.attributes["current_name"] == "Morning 2"
    assert s.attributes["current_start"] == datetime.fromisoformat(
        "2021-01-04 06:10:00+00:00"
    )
    assert hms_to_td(s.attributes["current_duration"]) == timedelta(minutes=12)
    assert hms_to_td(s.attributes["time_remaining"]) == timedelta(minutes=10)
    assert s.attributes["percent_complete"] == 16
    assert s.attributes["next_schedule"] == 2
    assert s.attributes["next_name"] == "Afternoon 2"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 14:10:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=22)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-open"

    next_time = await run_until(
        hass,
        coordinator,
        start_time,
        datetime.fromisoformat("2021-01-04 06:17:00+00:00"),
        True,
    )
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
    assert s.state == STATE_ON
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["status"] == STATE_ON
    assert s.attributes["zone_count"] == 2
    assert s.attributes["current_zone"] == 2
    assert s.attributes["current_name"] == "Second zone"
    assert s.attributes["current_start"] == datetime.fromisoformat(
        "2021-01-04 06:08:00+00:00"
    )
    assert hms_to_td(s.attributes["current_duration"]) == timedelta(minutes=16)
    assert hms_to_td(s.attributes["time_remaining"]) == timedelta(minutes=7)
    assert s.attributes["percent_complete"] == 56
    assert s.attributes["next_zone"] == 1
    assert s.attributes["next_name"] == "First zone"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 14:03:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=24)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
    assert s.attributes[ATTR_ICON] == "mdi:water"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.state == STATE_OFF
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["zone_id"] == "1"
    assert s.attributes["status"] == STATE_OFF
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["schedule_count"] == 2
    assert s.attributes["current_schedule"] == RES_NOT_RUNNING
    assert s.attributes["percent_complete"] == 0
    assert s.attributes["next_schedule"] == 2
    assert s.attributes["next_name"] == "Afternoon 1"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 14:05:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=20)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "First zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-closed"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
    assert s.state == STATE_ON
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 1
    assert s.attributes["zone_id"] == "2"
    assert s.attributes["status"] == STATE_ON
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["current_schedule"] == 1
    assert s.attributes["current_name"] == "Morning 2"
    assert s.attributes["current_start"] == datetime.fromisoformat(
        "2021-01-04 06:10:00+00:00"
    )
    assert hms_to_td(s.attributes["current_duration"]) == timedelta(minutes=12)
    assert hms_to_td(s.attributes["time_remaining"]) == timedelta(minutes=5)
    assert s.attributes["percent_complete"] == 58
    assert s.attributes["next_schedule"] == 2
    assert s.attributes["next_name"] == "Afternoon 2"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 14:10:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=22)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-open"

    next_time = await run_until(
        hass,
        coordinator,
        start_time,
        datetime.fromisoformat("2021-01-04 06:23:00+00:00"),
        True,
    )
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
    assert s.state == STATE_ON
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["status"] == STATE_ON
    assert s.attributes["zone_count"] == 2
    assert s.attributes["current_zone"] == 2
    assert s.attributes["current_name"] == "Second zone"
    assert s.attributes["current_start"] == datetime.fromisoformat(
        "2021-01-04 06:08:00+00:00"
    )
    assert hms_to_td(s.attributes["current_duration"]) == timedelta(minutes=16)
    assert hms_to_td(s.attributes["time_remaining"]) == timedelta(minutes=1)
    assert s.attributes["percent_complete"] == 93
    assert s.attributes["next_zone"] == 1
    assert s.attributes["next_name"] == "First zone"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 14:03:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=24)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
    assert s.attributes[ATTR_ICON] == "mdi:water"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.state == STATE_OFF
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["zone_id"] == "1"
    assert s.attributes["status"] == STATE_OFF
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["schedule_count"] == 2
    assert s.attributes["current_schedule"] == RES_NOT_RUNNING
    assert s.attributes["percent_complete"] == 0
    assert s.attributes["next_schedule"] == 2
    assert s.attributes["next_name"] == "Afternoon 1"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 14:05:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=20)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "First zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-closed"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
    assert s.state == STATE_OFF
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 1
    assert s.attributes["status"] == STATE_OFF
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["schedule_count"] == 2
    assert s.attributes["current_schedule"] == RES_NOT_RUNNING
    assert s.attributes["percent_complete"] == 0
    assert s.attributes["next_schedule"] == 2
    assert s.attributes["next_name"] == "Afternoon 2"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 14:10:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=22)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-closed"

    next_time = await run_until(
        hass,
        coordinator,
        next_time,
        datetime.fromisoformat("2021-01-04 06:25:00+00:00"),
        True,
    )
    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
    assert s.state == STATE_OFF
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["status"] == STATE_OFF
    assert s.attributes["zone_count"] == 2
    assert s.attributes["current_zone"] == RES_NOT_RUNNING
    assert s.attributes["percent_complete"] == 0
    assert s.attributes["next_zone"] == 1
    assert s.attributes["next_name"] == "First zone"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 14:03:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=24)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
    assert s.attributes[ATTR_ICON] == "mdi:water-off"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
    assert s.state == STATE_OFF
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 0
    assert s.attributes["zone_id"] == "1"
    assert s.attributes["status"] == STATE_OFF
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["schedule_count"] == 2
    assert s.attributes["current_schedule"] == RES_NOT_RUNNING
    assert s.attributes["percent_complete"] == 0
    assert s.attributes["next_schedule"] == 2
    assert s.attributes["next_name"] == "Afternoon 1"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 14:05:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=20)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "First zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-closed"

    s = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
    assert s.state == STATE_OFF
    assert s.attributes[ATTR_ENABLED] == True
    assert s.attributes[ATTR_INDEX] == 1
    assert s.attributes["status"] == STATE_OFF
    assert s.attributes["adjustment"] == "None"
    assert s.attributes["schedule_count"] == 2
    assert s.attributes["current_schedule"] == RES_NOT_RUNNING
    assert s.attributes["percent_complete"] == 0
    assert s.attributes["next_schedule"] == 2
    assert s.attributes["next_name"] == "Afternoon 2"
    assert s.attributes["next_start"] == datetime.fromisoformat(
        "2021-01-04 14:10:00+00:00"
    )
    assert hms_to_td(s.attributes["next_duration"]) == timedelta(minutes=22)
    assert s.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
    assert s.attributes[ATTR_ICON] == "mdi:valve-closed"

    await finish_test(hass, coordinator, next_time, True)

    check_summary(full_path, coordinator)
