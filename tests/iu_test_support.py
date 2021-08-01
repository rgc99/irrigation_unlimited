import logging
from datetime import datetime, timedelta
import homeassistant.core as ha

from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
)

_LOGGER = logging.getLogger(__name__)

test_config_dir = "tests/configs/"

# Shh, quiet now.
def quiet_mode():
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("homeassistant.core").setLevel(logging.WARNING)
    logging.getLogger("homeassistant.components.recorder").setLevel(logging.WARNING)
    logging.getLogger("pytest_homeassistant_custom_component.common").setLevel(
        logging.WARNING
)

def check_summary(full_path: str, coordinator: IUCoordinator):
    assert (
        coordinator.tester.total_events
        == coordinator.tester.total_checks
        == coordinator.tester.total_results
    )
    assert coordinator.tester.total_errors == 0
    print(
        "Finished: {0}; tests: {1}; events: {2}; checks: {3}; errors: {4}; time: {5:.2f}s".format(
            full_path,
            coordinator.tester.total_tests,
            coordinator.tester.total_events,
            coordinator.tester.total_checks,
            coordinator.tester.total_errors,
            coordinator.tester.total_time,
        )
    )
    return

async def run_until(hass: ha.HomeAssistant, coordinator: IUCoordinator, time: datetime, stop_at: datetime, block: bool) -> datetime:
    interval = coordinator.track_interval()
    while coordinator.tester.is_testing and (
        stop_at is None or coordinator.tester.current_test.virtual_time(time) < stop_at):
        time += interval
        coordinator.timer(time)
        if block:
            await hass.async_block_till_done()
    return time

async def run_for(hass: ha.HomeAssistant, coordinator: IUCoordinator, time: datetime, duration: timedelta, block: bool) -> datetime:
    if duration is not None:
        stop_at = coordinator.tester.current_test.virtual_time(time) + duration
    else:
        stop_at = None
    return await run_until(hass, coordinator, time, stop_at, block)

async def begin_test(test_no: int, coordinator: IUCoordinator) -> datetime:
    coordinator.stop()
    start_time = coordinator.start_test(test_no)
    _LOGGER.debug("Starting test %s", coordinator.tester.current_test.name)
    return start_time

async def finish_test(
    hass: ha.HomeAssistant, coordinator: IUCoordinator, time: datetime, block: bool
):
    await run_until(hass, coordinator, time, None, block)

    test = coordinator.tester.last_test
    assert test.errors == 0, f"Failed test {test.index + 1}"
    assert test.events == test.total_results, f"Failed test {test.index + 1}"
    _LOGGER.debug("Finished test %s time: %.2fs", test.name, test.test_time)
    return


