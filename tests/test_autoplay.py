"""Test irrigation_unlimited autoplay operations."""
import asyncio
import homeassistant.core as ha
from tests.iu_test_support import IUExam

IUExam.quiet_mode()

# pylint: disable=unused-argument
async def test_autoplay(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test autoplay feature."""

    async with IUExam(hass, "test_autoplay.yaml") as exam:
        duration = exam.coordinator.tester.total_virtual_duration
        await asyncio.sleep(
            duration.total_seconds() + 10
        )  # Add a few seconds to allow tests to finish

        exam.check_summary()
