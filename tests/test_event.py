"""Test irrigation_unlimited events."""
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    EVENT_FINISH,
    EVENT_START,
)
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_events(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test events."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_event.yaml") as exam:

        event_data: list[ha.Event] = []

        def handle_event(event: ha.Event):
            nonlocal event_data
            event_data.append(event.data)

        hass.bus.async_listen(f"{DOMAIN}_{EVENT_START}", handle_event)
        hass.bus.async_listen(f"{DOMAIN}_{EVENT_FINISH}", handle_event)

        await exam.run_all()

        exam.check_summary()

        assert event_data == [
            {
                "controller": {"index": 0, "name": "Test controller 1"},
                "sequence": {"index": 0, "name": "Seq 1"},
                "run": {"duration": 5460},
                "schedule": {"index": 0, "name": "Schedule 1"},
            },
            {
                "controller": {"index": 0, "name": "Test controller 1"},
                "sequence": {"index": 0, "name": "Seq 1"},
                "run": {"duration": 5460},
                "schedule": {"index": 0, "name": "Schedule 1"},
            },
            {
                "controller": {"index": 0, "name": "Test controller 1"},
                "sequence": {"index": 1, "name": "Seq 2"},
                "run": {"duration": 2280},
                "schedule": {"index": 0, "name": "Schedule 1"},
            },
            {
                "controller": {"index": 0, "name": "Test controller 1"},
                "sequence": {"index": 1, "name": "Seq 2"},
                "run": {"duration": 2280},
                "schedule": {"index": 0, "name": "Schedule 1"},
            },
        ]
