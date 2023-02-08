"""irrigation_unlimited check_back tester"""
from datetime import datetime
from unittest.mock import patch
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    EVENT_SYNC_ERROR,
    EVENT_SWITCH_ERROR,
)
from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IULogger,
)
from tests.iu_test_support import IUExam, mk_utc

IUExam.quiet_mode()


async def test_check_back(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test IUCheckBack class."""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-statements

    async with IUExam(hass, "test_check_back.yaml") as exam:

        await exam.load_component("homeassistant")
        await exam.load_component("input_boolean")

        sync_event_errors: list[ha.Event] = []
        switch_event_errors: list[ha.Event] = []

        def handle_sync_events(event: ha.Event) -> None:
            nonlocal sync_event_errors
            sync_event_errors.append(event.data)

        def handle_switch_events(event: ha.Event) -> None:
            nonlocal switch_event_errors
            switch_event_errors.append(event.data)

        hass.bus.async_listen(f"{DOMAIN}_{EVENT_SYNC_ERROR}", handle_sync_events)
        hass.bus.async_listen(f"{DOMAIN}_{EVENT_SWITCH_ERROR}", handle_switch_events)

        async def kill_c1_m(atime: datetime) -> None:
            """Turn off dummy_switch_c1_m at the specified time"""
            await exam.run_until(atime)
            await hass.services.async_call(
                "homeassistant",
                "turn_off",
                {"entity_id": "input_boolean.dummy_switch_c1_m"},
                True,
            )

        async def kill_c1_z3(atime: datetime) -> None:
            """Turn off dummy_switch_c1_z3 at the specified time"""
            await exam.run_until(atime)
            await hass.services.async_call(
                "homeassistant",
                "turn_off",
                {"entity_id": "input_boolean.dummy_switch_c1_z3"},
                True,
            )

        # Regular run - no errors
        sync_event_errors.clear()
        switch_event_errors.clear()
        with patch.object(IULogger, "log_sync_error") as mock_sync_logger:
            with patch.object(IULogger, "log_switch_error") as mock_switch_logger:

                await exam.run_test(1)
                assert mock_sync_logger.call_count == 0
                assert mock_switch_logger.call_count == 0
                assert len(sync_event_errors) == 0
                assert len(switch_event_errors) == 0

        # Partial comms error on c1_z3
        sync_event_errors.clear()
        switch_event_errors.clear()
        with patch.object(IULogger, "log_sync_error") as mock_sync_logger:
            with patch.object(IULogger, "log_switch_error") as mock_switch_logger:

                await exam.begin_test(2)
                await kill_c1_z3(mk_utc("2021-01-04 07:12:15"))
                await kill_c1_z3(mk_utc("2021-01-04 07:12:45"))
                await exam.finish_test()
                assert mock_sync_logger.call_count == 2
                assert mock_switch_logger.call_count == 0
                assert len(switch_event_errors) == 0
                assert sync_event_errors == [
                    {
                        "expected": "on",
                        "entity_id": "input_boolean.dummy_switch_c1_z3",
                        "controller": {"index": 0, "name": "Test controller 1"},
                        "zone": {"index": 1, "name": "Zone 2"},
                    },
                    {
                        "expected": "on",
                        "entity_id": "input_boolean.dummy_switch_c1_z3",
                        "controller": {"index": 0, "name": "Test controller 1"},
                        "zone": {"index": 1, "name": "Zone 2"},
                    },
                ]

        # Full comms error on c1_z3
        sync_event_errors.clear()
        switch_event_errors.clear()
        with patch.object(IULogger, "log_sync_error") as mock_sync_logger:
            with patch.object(IULogger, "log_switch_error") as mock_switch_logger:

                await exam.begin_test(3)
                await kill_c1_z3(mk_utc("2021-01-04 07:12:15"))
                await kill_c1_z3(mk_utc("2021-01-04 07:12:45"))
                await kill_c1_z3(mk_utc("2021-01-04 07:13:15"))
                await kill_c1_z3(mk_utc("2021-01-04 07:13:45"))
                await exam.finish_test()
                assert mock_sync_logger.call_count == 3
                assert mock_switch_logger.call_count == 1
                assert len(sync_event_errors) == 3
                assert switch_event_errors == [
                    {
                        "expected": "on",
                        "entity_id": "input_boolean.dummy_switch_c1_z3",
                        "controller": {"index": 0, "name": "Test controller 1"},
                        "zone": {"index": 1, "name": "Zone 2"},
                    }
                ]

        # Full comms error on c1_m
        sync_event_errors.clear()
        switch_event_errors.clear()
        with patch.object(IULogger, "_output") as mock_logger:

            await exam.begin_test(4)
            await kill_c1_m(mk_utc("2021-01-04 07:12:15"))
            await kill_c1_m(mk_utc("2021-01-04 07:12:45"))
            await kill_c1_m(mk_utc("2021-01-04 07:13:15"))
            await kill_c1_m(mk_utc("2021-01-04 07:13:45"))
            await exam.finish_test()
            assert (
                mock_logger.call_count == 14
            )  # 8 EVENTS + 3 SYNC + 1 SWITCH + START + END

        # Check the exam results
        exam.check_summary()
