"""irrigation_unlimited check_back tester"""
from datetime import datetime, timedelta
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
from tests.iu_test_support import IUExam, parse_utc

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
            data = event.data
            data["vtime"] = exam.virtual_time
            sync_event_errors.append(data)

        def handle_switch_events(event: ha.Event) -> None:
            nonlocal switch_event_errors
            data = event.data
            data["vtime"] = exam.virtual_time
            switch_event_errors.append(data)

        hass.bus.async_listen(f"{DOMAIN}_{EVENT_SYNC_ERROR}", handle_sync_events)
        hass.bus.async_listen(f"{DOMAIN}_{EVENT_SWITCH_ERROR}", handle_switch_events)

        async def kill_m(atime: datetime) -> None:
            """Turn off dummy_switch_m at the specified time"""
            await exam.run_until(atime)
            await hass.services.async_call(
                "homeassistant",
                "turn_off",
                {"entity_id": "input_boolean.dummy_switch_m"},
                True,
            )

        async def kill_z1(atime: datetime) -> None:
            """Turn off dummy_switch_z1 at the specified time"""
            await exam.run_until(atime)
            await hass.services.async_call(
                "homeassistant",
                "turn_off",
                {"entity_id": "input_boolean.dummy_switch_z1"},
                True,
            )

        async def kill_z3(atime: datetime) -> None:
            """Turn off dummy_switch_z3 at the specified time"""
            await exam.run_until(atime)
            await hass.services.async_call(
                "homeassistant",
                "turn_off",
                {"entity_id": "input_boolean.dummy_switch_z3"},
                True,
            )

        async def change_check_back_switch(state: bool) -> None:
            """Turn on/off dummy_switch_call_back_switch"""
            await hass.services.async_call(
                "homeassistant",
                "turn_on" if state else "turn_off",
                {"entity_id": "input_boolean.dummy_check_back_switch"},
                True,
            )

        # Basic check
        # pylint: disable=protected-access
        assert exam.coordinator.controllers[2].zones[
            0
        ]._switch._check_back_delay == timedelta(seconds=15)
        assert exam.coordinator.controllers[2].zones[0]._switch._check_back_retries == 5

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

        # Check switch gets turned back on
        sync_event_errors.clear()
        switch_event_errors.clear()
        with patch.object(IULogger, "log_sync_error") as mock_sync_logger:
            with patch.object(IULogger, "log_switch_error") as mock_switch_logger:
                await exam.begin_test(2)
                await kill_m("2021-01-04 07:05:15")
                assert hass.states.get("input_boolean.dummy_switch_m").state == "off"
                await exam.run_until("2021-01-04 07:05:45")
                assert hass.states.get("input_boolean.dummy_switch_m").state == "on"
                await kill_z3("2021-01-04 07:12:15")
                assert hass.states.get("input_boolean.dummy_switch_z3").state == "off"
                await exam.run_until("2021-01-04 07:12:45")
                assert hass.states.get("input_boolean.dummy_switch_z3").state == "on"
                await exam.finish_test()
                assert mock_sync_logger.call_count == 2
                assert mock_switch_logger.call_count == 0
                assert len(sync_event_errors) == 2
                assert len(switch_event_errors) == 0

        # Partial comms error on c1_z3
        sync_event_errors.clear()
        switch_event_errors.clear()
        with patch.object(IULogger, "log_sync_error") as mock_sync_logger:
            with patch.object(IULogger, "log_switch_error") as mock_switch_logger:
                await exam.begin_test(3)
                await kill_z3("2021-01-04 07:12:15")
                await kill_z3("2021-01-04 07:12:45")
                await exam.finish_test()
                assert mock_sync_logger.call_count == 2
                assert mock_switch_logger.call_count == 0
                assert len(switch_event_errors) == 0
                assert sync_event_errors == [
                    {
                        "vtime": parse_utc("2021-01-04 15:12:00"),
                        "expected": "on",
                        "entity_id": "input_boolean.dummy_switch_z3",
                        "controller": {"index": 0, "name": "Test controller 1"},
                        "zone": {"index": 1, "name": "Zone 2"},
                    },
                    {
                        "vtime": parse_utc("2021-01-04 15:12:30"),
                        "expected": "on",
                        "entity_id": "input_boolean.dummy_switch_z3",
                        "controller": {"index": 0, "name": "Test controller 1"},
                        "zone": {"index": 1, "name": "Zone 2"},
                    },
                ]

        # Full comms error on c1_z3
        sync_event_errors.clear()
        switch_event_errors.clear()
        with patch.object(IULogger, "log_sync_error") as mock_sync_logger:
            with patch.object(IULogger, "log_switch_error") as mock_switch_logger:
                await exam.begin_test(4)
                await kill_z3("2021-01-04 07:12:15")
                await kill_z3("2021-01-04 07:12:45")
                await kill_z3("2021-01-04 07:13:15")
                await kill_z3("2021-01-04 07:13:45")
                await exam.finish_test()
                assert mock_sync_logger.call_count == 3
                assert mock_switch_logger.call_count == 1
                assert sync_event_errors == [
                    {
                        "vtime": parse_utc("2021-01-04 15:12:00"),
                        "expected": "on",
                        "entity_id": "input_boolean.dummy_switch_z3",
                        "controller": {"index": 0, "name": "Test controller 1"},
                        "zone": {"index": 1, "name": "Zone 2"},
                    },
                    {
                        "vtime": parse_utc("2021-01-04 15:12:30"),
                        "expected": "on",
                        "entity_id": "input_boolean.dummy_switch_z3",
                        "controller": {"index": 0, "name": "Test controller 1"},
                        "zone": {"index": 1, "name": "Zone 2"},
                    },
                    {
                        "vtime": parse_utc("2021-01-04 15:13:00"),
                        "expected": "on",
                        "entity_id": "input_boolean.dummy_switch_z3",
                        "controller": {"index": 0, "name": "Test controller 1"},
                        "zone": {"index": 1, "name": "Zone 2"},
                    },
                ]
                assert switch_event_errors == [
                    {
                        "vtime": parse_utc("2021-01-04 15:13:30"),
                        "expected": "on",
                        "entity_id": "input_boolean.dummy_switch_z3",
                        "controller": {"index": 0, "name": "Test controller 1"},
                        "zone": {"index": 1, "name": "Zone 2"},
                    }
                ]

        # Full comms error on c1_m
        sync_event_errors.clear()
        switch_event_errors.clear()
        with patch.object(IULogger, "_output") as mock_logger:
            await exam.begin_test(5)
            await kill_m("2021-01-04 07:12:15")
            await kill_m("2021-01-04 07:12:45")
            await kill_m("2021-01-04 07:13:15")
            await kill_m("2021-01-04 07:13:45")
            await exam.finish_test()
            assert (
                mock_logger.call_count == 14
            )  # 8 EVENTS + 3 SYNC + 1 SWITCH + START + END

        # Change switch state before check back completed
        sync_event_errors.clear()
        switch_event_errors.clear()
        with patch.object(IULogger, "log_sync_error") as mock_sync_logger:
            with patch.object(IULogger, "log_switch_error") as mock_switch_logger:
                await exam.begin_test(6)
                await kill_z3("2021-01-04 19:06:20")
                await exam.finish_test()
                assert len(sync_event_errors) == 1
                assert len(switch_event_errors) == 0

        # Read state from other entity
        sync_event_errors.clear()
        switch_event_errors.clear()
        with patch.object(IULogger, "log_sync_error") as mock_sync_logger:
            with patch.object(IULogger, "log_switch_error") as mock_switch_logger:
                await change_check_back_switch(False)
                await exam.begin_test(7)
                await kill_m("2021-01-04 20:05:05")
                await kill_z1("2021-01-04 20:05:05")
                await change_check_back_switch(True)
                await exam.run_until("2021-01-04 20:11:05")
                await change_check_back_switch(False)
                await kill_z3("2021-01-04 20:12:05")
                await change_check_back_switch(True)
                await exam.run_until("2021-01-04 20:24:05")
                await change_check_back_switch(False)
                await exam.finish_test()
                assert mock_sync_logger.call_count == 0
                assert mock_switch_logger.call_count == 0
                assert len(sync_event_errors) == 0
                assert len(switch_event_errors) == 0

        sync_event_errors.clear()
        switch_event_errors.clear()
        with patch.object(IULogger, "log_sync_error") as mock_sync_logger:
            with patch.object(IULogger, "log_switch_error") as mock_switch_logger:
                await change_check_back_switch(False)
                await exam.begin_test(8)
                await kill_z1("2021-01-04 20:05:05")
                assert hass.states.get("input_boolean.dummy_switch_z1").state == "off"
                assert (
                    hass.states.get("input_boolean.dummy_check_back_switch").state
                    == "off"
                )
                await exam.run_until("2021-01-04 20:05:20")
                assert hass.states.get("input_boolean.dummy_switch_z1").state == "on"
                assert (
                    hass.states.get("input_boolean.dummy_check_back_switch").state
                    == "off"
                )
                await kill_z3("2021-01-04 20:12:05")
                assert hass.states.get("input_boolean.dummy_switch_z3").state == "off"
                assert (
                    hass.states.get("input_boolean.dummy_check_back_switch").state
                    == "off"
                )
                await exam.run_until("2021-01-04 20:24:20")
                # Check no attempt to resync on group switch
                assert hass.states.get("input_boolean.dummy_switch_z3").state == "off"
                assert (
                    hass.states.get("input_boolean.dummy_check_back_switch").state
                    == "off"
                )
                await exam.finish_test()
                assert mock_sync_logger.call_count == 10
                assert mock_switch_logger.call_count == 2
                assert len(sync_event_errors) == 10
                assert len(switch_event_errors) == 2

        # Check the exam results
        exam.check_summary()
