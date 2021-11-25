"""Irrigation Unlimited test support routines"""
import logging
from datetime import datetime, timedelta
import homeassistant.core as ha

from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
)

_LOGGER = logging.getLogger(__name__)

# pylint: disable=global-statement
TEST_CONFIG_DIR = "tests/configs/"

NO_CHECK: bool = False

# Shh, quiet now.
def quiet_mode() -> None:
    """Trun off a lot of noise"""
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("homeassistant.core").setLevel(logging.WARNING)
    logging.getLogger("homeassistant.components.recorder").setLevel(logging.WARNING)
    logging.getLogger("pytest_homeassistant_custom_component.common").setLevel(
        logging.WARNING
    )


# Turn off checking
def no_check(check_off: bool = True) -> None:
    """Disable checking results"""
    global NO_CHECK
    NO_CHECK = check_off
    if NO_CHECK:
        _LOGGER.debug("WARNING: Checks are disabled===================================")
    return


def check_summary(full_path: str, coordinator: IUCoordinator):
    """Check the test results"""
    if not NO_CHECK:
        assert (
            coordinator.tester.total_events
            == coordinator.tester.total_checks
            == coordinator.tester.total_results
        ), "Failed summary results"
        assert coordinator.tester.total_errors == 0, "Failed summary errors"

    _LOGGER.debug(
        "Finished: {0}, tests: {1}, events: {2}, checks: {3}, errors: {4}, time: {5:.2f}s".format(
            full_path,
            coordinator.tester.total_tests,
            coordinator.tester.total_events,
            coordinator.tester.total_checks,
            coordinator.tester.total_errors,
            coordinator.tester.total_time,
        )
    )
    return


async def run_until(
    hass: ha.HomeAssistant,
    coordinator: IUCoordinator,
    time: datetime,
    stop_at: datetime,
    block: bool,
) -> datetime:
    """Run until a point in time"""
    interval = coordinator.track_interval()
    while coordinator.tester.is_testing and (
        stop_at is None or coordinator.tester.current_test.virtual_time(time) < stop_at
    ):
        time += interval
        coordinator.timer(time)
        if block:
            await hass.async_block_till_done()
    return time


async def run_for(
    hass: ha.HomeAssistant,
    coordinator: IUCoordinator,
    time: datetime,
    duration: timedelta,
    block: bool,
) -> datetime:
    """Run for a period of time"""
    if duration is not None:
        stop_at = coordinator.tester.current_test.virtual_time(time) + duration
    else:
        stop_at = None
    return await run_until(hass, coordinator, time, stop_at, block)


async def run_for_1_tick(
    hass: ha.HomeAssistant, coordinator: IUCoordinator, time: datetime, block: bool
) -> datetime:
    """Run for 1 tick of the clock"""
    stop_at = (
        coordinator.tester.current_test.virtual_time(time)
        + coordinator.track_interval()
    )
    return await run_until(hass, coordinator, time, stop_at, block)


async def begin_test(test_no: int, coordinator: IUCoordinator) -> datetime:
    """Start a test"""
    coordinator.stop()
    start_time = coordinator.start_test(test_no)
    assert start_time is not None, f"Invalid test {test_no}"
    _LOGGER.debug("Starting test: %s", coordinator.tester.current_test.name)
    return start_time


async def finish_test(
    hass: ha.HomeAssistant, coordinator: IUCoordinator, time: datetime, block: bool
):
    """Finish a test"""
    await run_until(hass, coordinator, time, None, block)

    test = coordinator.tester.last_test
    if not NO_CHECK:
        assert test.errors == 0, f"Failed test {test.index + 1}, errors not zero"
        assert (
            test.events <= test.total_results
        ), f"Failed test {test.index + 1}, missing event"
        assert (
            test.events >= test.total_results
        ), f"Failed test {test.index + 1}, extra event"
    _LOGGER.debug("Finished test: %s, time: %.2fs", test.name, test.test_time)
    return
