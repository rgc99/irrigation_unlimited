"""Test irrigation_unlimited tester for the tester"""
import pytest
import homeassistant.core as ha
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


# pylint: disable=unused-argument
async def test_tester(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test the testing object"""

    async with IUExam(hass, "test_tester.yaml") as exam:
        assert len(exam.coordinator.tester.tests) == 2
        await exam.begin_test(1)
        assert exam.coordinator.tester.last_test is None
        await exam.finish_test()
        assert exam.coordinator.tester.last_test == exam.coordinator.tester.tests[0]


async def test_test_1(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test the testing unit. Parameter show_log=False"""

    async with IUExam(hass, "test_test_1.yaml") as exam:
        with pytest.raises(AssertionError, match="Invalid test 999"):
            await exam.begin_test(999)

        await exam.begin_test(1)
        with pytest.raises(AssertionError, match="Failed test 1, errors not zero"):
            await exam.finish_test()

        await exam.begin_test(2)
        with pytest.raises(AssertionError, match="Failed test 2, missing event"):
            await exam.finish_test()

        await exam.begin_test(3)
        with pytest.raises(AssertionError, match="Failed test 3, extra event"):
            await exam.finish_test()

        with pytest.raises(AssertionError, match="Failed summary results"):
            exam.check_summary()


async def test_test_2(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test the testing unit. Parameter show_log=True"""

    async with IUExam(hass, "test_test_2.yaml") as exam:
        with pytest.raises(AssertionError, match="Invalid test 999"):
            await exam.begin_test(999)

        await exam.begin_test(1)
        with pytest.raises(AssertionError, match="Failed test 1, errors not zero"):
            await exam.finish_test()

        await exam.begin_test(2)
        with pytest.raises(AssertionError, match="Failed test 2, missing event"):
            await exam.finish_test()

        await exam.begin_test(3)
        with pytest.raises(AssertionError, match="Failed test 3, extra event"):
            await exam.finish_test()

        with pytest.raises(AssertionError, match="Failed summary results"):
            exam.check_summary()
