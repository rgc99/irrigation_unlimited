"""Test irrigation_unlimited user configurations. Not exactly a test
   but a place to check if configuration files are valid and possibly
   debug them."""
# pylint: disable=unused-import
from datetime import timedelta, datetime
import json
import pytest
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_TIME_ADJUST,
    DOMAIN,
    COORDINATOR,
    EVENT_FINISH,
    EVENT_START,
)
from tests.iu_test_support import IUExam, mk_utc

IUExam.quiet_mode()

# Remove the following decorator to run test
# @pytest.mark.skip
async def test_config(hass: ha.HomeAssistant, skip_history):
    """Test loading of a config."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_config.yaml") as exam:

        # """Prevent checking results. Helpful for just outputting results"""
        # exam.no_check()

        # Load dependencies if required
        # await exam.load_dependencies()

        # Load any components
        # await exam.async_load_component("homeassistant")

        # Run all tests
        await exam.run_all()

        # Run a single test
        # await exam.begin_test(1)

        # Make a service call
        # await exam.call(
        #     SERVICE_TIME_ADJUST,
        #     {
        #         "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
        #         "sequence_id": 1,
        #         "percentage": 47.5,
        #     },
        # )

        # Run to a point in time
        # await exam.run_until(mk_utc("2021-01-04 06:02"))
        # await exam.run_until(mk_utc("2022-05-11 06:30:00"))

        # Run for a period of time
        # await exam.run_for(timedelta(minutes=15))

        # Print out the configuration
        # print(json.dumps(exam.coordinator.as_dict(), default=str))

        # print out the attributes of an entity
        # sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        # print(sta.attributes)

        # Complete the current test
        # await exam.finish_test()

        # Finish up and check test results
        exam.check_summary()
