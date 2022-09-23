"""irrigation_unlimited model test template"""
# pylint: disable=unused-import
from datetime import timedelta
import json
import pytest
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_DISABLE,
    SERVICE_MANUAL_RUN,
)
from tests.iu_test_support import IUExam, mk_utc, mk_local

IUExam.quiet_mode()

# Remove the following decorator to run test
# @pytest.mark.skip
async def test_model(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Model IUExam class."""
    # pylint: disable=unused-argument

    # Start an examination
    async with IUExam(hass, "test_allow_manual.yaml") as exam:

        await exam.begin_test(1)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z1",
                "time": "00:10",
            },
        )
        await exam.finish_test()

        await exam.begin_test(2)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z2",
                "time": "00:10",
            },
        )
        await exam.finish_test()

        await exam.begin_test(3)
        await exam.call(
            SERVICE_DISABLE,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z3",
            },
        )
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_z3",
                "time": "00:10",
            },
        )
        await exam.finish_test()

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
