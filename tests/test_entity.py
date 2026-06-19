"""Test irrigation_unlimited entity operations."""
from datetime import timedelta
import homeassistant.core as ha
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    STATE_OFF,
    STATE_ON,
)
from custom_components.irrigation_unlimited.const import (
    ATTR_ENABLED,
    ATTR_SUSPENDED,
    ATTR_INDEX,
    ATTR_STATUS,
    ATTR_ADJUSTMENT,
    ATTR_ZONE_COUNT,
    ATTR_CURRENT_ZONE,
    ATTR_NEXT_ZONE,
    ATTR_NEXT_NAME,
    ATTR_NEXT_START,
    ATTR_NEXT_DURATION,
    ATTR_PERCENT_COMPLETE,
    ATTR_SCHEDULE_COUNT,
    ATTR_CURRENT_NAME,
    ATTR_CURRENT_SCHEDULE,
    ATTR_CURRENT_START,
    ATTR_CURRENT_DURATION,
    ATTR_NEXT_SCHEDULE,
    ATTR_TIME_REMAINING,
    CONF_ZONE_ID,
)
from custom_components.irrigation_unlimited.binary_sensor import RES_NOT_RUNNING
from tests.iu_test_support import (
    IUExam,
    mk_local,
    mk_td,
)

IUExam.quiet_mode()


# pylint: disable=unused-argument
async def test_entity(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test entity."""
    # pylint: disable=too-many-statements

    async with IUExam(hass, "test_entity.yaml") as exam:
        await exam.begin_test(1)
        await exam.run_until("2021-01-04 06:02")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.state == STATE_OFF
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[ATTR_STATUS] == STATE_OFF
        assert sta.attributes[ATTR_ZONE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_ZONE] == RES_NOT_RUNNING
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 0
        assert sta.attributes[ATTR_NEXT_ZONE] == 1
        assert sta.attributes[ATTR_NEXT_NAME] == "First zone"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 06:03")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=14)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
        assert sta.attributes[ATTR_ICON] == "mdi:water-off"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.state == STATE_OFF
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[CONF_ZONE_ID] == "1"
        assert sta.attributes[ATTR_STATUS] == STATE_OFF
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_SCHEDULE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] is None
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 0
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 1
        assert sta.attributes[ATTR_NEXT_NAME] == "Morning 1"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 06:05")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=10)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "First zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-closed"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.state == STATE_OFF
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 1
        assert sta.attributes[CONF_ZONE_ID] == "2"
        assert sta.attributes[ATTR_STATUS] == STATE_OFF
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_SCHEDULE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] is None
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 0
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 1
        assert sta.attributes[ATTR_NEXT_NAME] == "Morning 2"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 06:10")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=12)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-closed"

        await exam.run_until("2021-01-04 06:04")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.state == STATE_ON
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_STATUS] == STATE_ON
        assert sta.attributes[ATTR_ZONE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_ZONE] == 1
        assert sta.attributes[ATTR_CURRENT_NAME] == "First zone"
        assert sta.attributes[ATTR_CURRENT_START] == mk_local("2021-01-04 06:03")
        assert mk_td(sta.attributes[ATTR_CURRENT_DURATION]) == timedelta(minutes=14)
        assert mk_td(sta.attributes[ATTR_TIME_REMAINING]) == timedelta(minutes=13)
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 7
        assert sta.attributes[ATTR_NEXT_ZONE] == 2
        assert sta.attributes[ATTR_NEXT_NAME] == "Second zone"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 06:08")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=16)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
        assert sta.attributes[ATTR_ICON] == "mdi:water"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.state == STATE_OFF
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[CONF_ZONE_ID] == "1"
        assert sta.attributes[ATTR_STATUS] == STATE_OFF
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_SCHEDULE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] is None
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 0
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 1
        assert sta.attributes[ATTR_NEXT_NAME] == "Morning 1"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 06:05")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=10)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "First zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-closed"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.state == STATE_OFF
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_INDEX] == 1
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[CONF_ZONE_ID] == "2"
        assert sta.attributes[ATTR_STATUS] == STATE_OFF
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_SCHEDULE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] is None
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 0
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 1
        assert sta.attributes[ATTR_NEXT_NAME] == "Morning 2"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 06:10")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=12)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-closed"

        await exam.run_until("2021-01-04 06:07")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.state == STATE_ON
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[ATTR_STATUS] == STATE_ON
        assert sta.attributes[ATTR_ZONE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_ZONE] == 1
        assert sta.attributes[ATTR_CURRENT_NAME] == "First zone"
        assert sta.attributes[ATTR_CURRENT_START] == mk_local("2021-01-04 06:03")
        assert mk_td(sta.attributes[ATTR_CURRENT_DURATION]) == timedelta(minutes=14)
        assert mk_td(sta.attributes[ATTR_TIME_REMAINING]) == timedelta(minutes=10)
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 28
        assert sta.attributes[ATTR_NEXT_ZONE] == 2
        assert sta.attributes[ATTR_NEXT_NAME] == "Second zone"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 06:08")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=16)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
        assert sta.attributes[ATTR_ICON] == "mdi:water"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.state == STATE_ON
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[CONF_ZONE_ID] == "1"
        assert sta.attributes[ATTR_STATUS] == STATE_ON
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] == 1
        assert sta.attributes[ATTR_CURRENT_NAME] == "Morning 1"
        assert sta.attributes[ATTR_CURRENT_START] == mk_local("2021-01-04 06:05")
        assert mk_td(sta.attributes[ATTR_CURRENT_DURATION]) == timedelta(minutes=10)
        assert mk_td(sta.attributes[ATTR_TIME_REMAINING]) == timedelta(minutes=8)
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 20
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 2
        assert sta.attributes[ATTR_NEXT_NAME] == "Afternoon 1"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 14:05")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=20)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "First zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-open"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.state == STATE_OFF
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 1
        assert sta.attributes[CONF_ZONE_ID] == "2"
        assert sta.attributes[ATTR_STATUS] == STATE_OFF
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] is None
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 0
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 1
        assert sta.attributes[ATTR_NEXT_NAME] == "Morning 2"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 06:10")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=12)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-closed"

        await exam.run_until("2021-01-04 06:12")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.state == STATE_ON
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_STATUS] == STATE_ON
        assert sta.attributes[ATTR_ZONE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_ZONE] == 1
        assert sta.attributes[ATTR_CURRENT_NAME] == "First zone"
        assert sta.attributes[ATTR_CURRENT_START] == mk_local("2021-01-04 06:03")
        assert mk_td(sta.attributes[ATTR_CURRENT_DURATION]) == timedelta(minutes=14)
        assert mk_td(sta.attributes[ATTR_TIME_REMAINING]) == timedelta(minutes=5)
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 64
        assert sta.attributes[ATTR_NEXT_ZONE] == 2
        assert sta.attributes[ATTR_NEXT_NAME] == "Second zone"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 06:08")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=16)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
        assert sta.attributes[ATTR_ICON] == "mdi:water"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.state == STATE_ON
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[CONF_ZONE_ID] == "1"
        assert sta.attributes[ATTR_STATUS] == STATE_ON
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] == 1
        assert sta.attributes[ATTR_CURRENT_NAME] == "Morning 1"
        assert sta.attributes[ATTR_CURRENT_START] == mk_local("2021-01-04 06:05")
        assert mk_td(sta.attributes[ATTR_CURRENT_DURATION]) == timedelta(minutes=10)
        assert mk_td(sta.attributes[ATTR_TIME_REMAINING]) == timedelta(minutes=3)
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 70
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 2
        assert sta.attributes[ATTR_NEXT_NAME] == "Afternoon 1"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 14:05")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=20)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "First zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-open"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.state == STATE_ON
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_INDEX] == 1
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[CONF_ZONE_ID] == "2"
        assert sta.attributes[ATTR_STATUS] == STATE_ON
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] == 1
        assert sta.attributes[ATTR_CURRENT_NAME] == "Morning 2"
        assert sta.attributes[ATTR_CURRENT_START] == mk_local("2021-01-04 06:10")
        assert mk_td(sta.attributes[ATTR_CURRENT_DURATION]) == timedelta(minutes=12)
        assert mk_td(sta.attributes[ATTR_TIME_REMAINING]) == timedelta(minutes=10)
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 16
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 2
        assert sta.attributes[ATTR_NEXT_NAME] == "Afternoon 2"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 14:10")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=22)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-open"

        await exam.run_until("2021-01-04 06:17")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.state == STATE_ON
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[ATTR_STATUS] == STATE_ON
        assert sta.attributes[ATTR_ZONE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_ZONE] == 2
        assert sta.attributes[ATTR_CURRENT_NAME] == "Second zone"
        assert sta.attributes[ATTR_CURRENT_START] == mk_local("2021-01-04 06:08")
        assert mk_td(sta.attributes[ATTR_CURRENT_DURATION]) == timedelta(minutes=16)
        assert mk_td(sta.attributes[ATTR_TIME_REMAINING]) == timedelta(minutes=7)
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 56
        assert sta.attributes[ATTR_NEXT_ZONE] == 1
        assert sta.attributes[ATTR_NEXT_NAME] == "First zone"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 14:03")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=24)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
        assert sta.attributes[ATTR_ICON] == "mdi:water"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.state == STATE_OFF
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[CONF_ZONE_ID] == "1"
        assert sta.attributes[ATTR_STATUS] == STATE_OFF
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_SCHEDULE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] is None
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 0
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 2
        assert sta.attributes[ATTR_NEXT_NAME] == "Afternoon 1"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 14:05")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=20)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "First zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-closed"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.state == STATE_ON
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 1
        assert sta.attributes[CONF_ZONE_ID] == "2"
        assert sta.attributes[ATTR_STATUS] == STATE_ON
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] == 1
        assert sta.attributes[ATTR_CURRENT_NAME] == "Morning 2"
        assert sta.attributes[ATTR_CURRENT_START] == mk_local("2021-01-04 06:10")
        assert mk_td(sta.attributes[ATTR_CURRENT_DURATION]) == timedelta(minutes=12)
        assert mk_td(sta.attributes[ATTR_TIME_REMAINING]) == timedelta(minutes=5)
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 58
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 2
        assert sta.attributes[ATTR_NEXT_NAME] == "Afternoon 2"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 14:10")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=22)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-open"

        await exam.run_until("2021-01-04 06:23")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.state == STATE_ON
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[ATTR_STATUS] == STATE_ON
        assert sta.attributes[ATTR_ZONE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_ZONE] == 2
        assert sta.attributes[ATTR_CURRENT_NAME] == "Second zone"
        assert sta.attributes[ATTR_CURRENT_START] == mk_local("2021-01-04 06:08")
        assert mk_td(sta.attributes[ATTR_CURRENT_DURATION]) == timedelta(minutes=16)
        assert mk_td(sta.attributes[ATTR_TIME_REMAINING]) == timedelta(minutes=1)
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 93
        assert sta.attributes[ATTR_NEXT_ZONE] == 1
        assert sta.attributes[ATTR_NEXT_NAME] == "First zone"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 14:03")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=24)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
        assert sta.attributes[ATTR_ICON] == "mdi:water"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.state == STATE_OFF
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[CONF_ZONE_ID] == "1"
        assert sta.attributes[ATTR_STATUS] == STATE_OFF
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_SCHEDULE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] is None
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 0
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 2
        assert sta.attributes[ATTR_NEXT_NAME] == "Afternoon 1"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 14:05")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=20)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "First zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-closed"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.state == STATE_OFF
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 1
        assert sta.attributes[ATTR_STATUS] == STATE_OFF
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_SCHEDULE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] is None
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 0
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 2
        assert sta.attributes[ATTR_NEXT_NAME] == "Afternoon 2"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 14:10")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=22)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-closed"

        await exam.run_until("2021-01-04 06:25")
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        assert sta.state == STATE_OFF
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[ATTR_STATUS] == STATE_OFF
        assert sta.attributes[ATTR_ZONE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_ZONE] == RES_NOT_RUNNING
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 0
        assert sta.attributes[ATTR_NEXT_ZONE] == 1
        assert sta.attributes[ATTR_NEXT_NAME] == "First zone"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 14:03")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=24)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Test controller 1"
        assert sta.attributes[ATTR_ICON] == "mdi:water-off"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.state == STATE_OFF
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 0
        assert sta.attributes[CONF_ZONE_ID] == "1"
        assert sta.attributes[ATTR_STATUS] == STATE_OFF
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_SCHEDULE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] is None
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 0
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 2
        assert sta.attributes[ATTR_NEXT_NAME] == "Afternoon 1"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 14:05")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=20)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "First zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-closed"

        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z2")
        assert sta.state == STATE_OFF
        assert sta.attributes[ATTR_ENABLED] is True
        assert sta.attributes[ATTR_SUSPENDED] is None
        assert sta.attributes[ATTR_INDEX] == 1
        assert sta.attributes[ATTR_STATUS] == STATE_OFF
        assert sta.attributes[ATTR_ADJUSTMENT] == ""
        assert sta.attributes[ATTR_SCHEDULE_COUNT] == 2
        assert sta.attributes[ATTR_CURRENT_SCHEDULE] is None
        assert sta.attributes[ATTR_PERCENT_COMPLETE] == 0
        assert sta.attributes[ATTR_NEXT_SCHEDULE] == 2
        assert sta.attributes[ATTR_NEXT_NAME] == "Afternoon 2"
        assert sta.attributes[ATTR_NEXT_START] == mk_local("2021-01-04 14:10")
        assert mk_td(sta.attributes[ATTR_NEXT_DURATION]) == timedelta(minutes=22)
        assert sta.attributes[ATTR_FRIENDLY_NAME] == "Second zone"
        assert sta.attributes[ATTR_ICON] == "mdi:valve-closed"

        await exam.finish_test()

        exam.check_summary()


async def test_entity_rename(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test renaming entities."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_entity_rename.yaml") as exam:
        assert exam.coordinator.rename_entities is True
        assert (
            hass.states.get("binary_sensor.irrigation_unlimited_my_garden") is not None
        )
        assert (
            hass.states.get("binary_sensor.irrigation_unlimited_my_garden_vege_patch")
            is not None
        )
        assert (
            hass.states.get("binary_sensor.irrigation_unlimited_my_garden_rose_bed")
            is not None
        )
        assert (
            hass.states.get("binary_sensor.irrigation_unlimited_my_garden_front_lawn")
            is not None
        )
