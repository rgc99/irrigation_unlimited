"""irrigation_unlimited model test template"""
# pylint: disable=unused-import
from datetime import timedelta
import json
import pytest
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_TIME_ADJUST,
)
from tests.iu_test_support import IUExam, mk_utc, mk_local

IUExam.quiet_mode()

# Remove the following decorator to run test
# @pytest.mark.skip
async def test_model(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Model IUExam class."""
    # pylint: disable=unused-argument

    # Start an examination
    async with IUExam(hass, "test_model.yaml") as exam:

        # Prevent checking results. Helpful for just outputting
        # results when it is known the test will fail.
        # (set `output_events: true` in yaml)
        # exam.no_check()

        # Load any components required for the test
        # await exam.async_load_component("homeassistant")
        # await exam.async_load_component("input_boolean")

        # Load dependencies if required
        # await exam.load_dependencies()

        # Run all tests
        # await exam.run_all()

        # Run a single test
        # await exam.run_test(1)

        # Start a test and do something...
        await exam.begin_test(1)

        # Make a service call
        # await exam.call(
        #     SERVICE_TIME_ADJUST,
        #     {
        #         "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
        #         "sequence_id": 1,
        #         "zones": 0,
        #         "actual": "00:10",
        #     },
        # )

        # Run to a point in time
        # await exam.run_until(mk_utc("2021-01-04 06:02:00"))

        # Run for a period of time
        # await exam.run_for(timedelta(minutes=15))

        # Check some things
        #
        # Inspect a zone entity
        # sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        # print(sta.state)
        # print(sta.attributes)
        #
        # Raise an error if the "next_start" attribute is not a certain time
        # assert sta.attributes["next_start"] == mk_local("2021-01-04 06:03")
        #
        # Print out the configuration
        # print(json.dumps(exam.coordinator.as_dict(), default=str))
        #
        # Print out the virtual date and time
        # print(f"The date and time is {exam.virtual_time}")

        # Finish up the current test
        await exam.finish_test()

        # Check the exam results
        exam.check_summary()
