"""Irrigation Unlimited test support routines"""
import logging
from datetime import datetime, timedelta
import homeassistant.core as ha
from homeassistant.config import (
    load_yaml_config_file,
    async_process_ha_core_config,
)
from homeassistant.setup import async_setup_component

from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
)
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    COORDINATOR,
)
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA

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


async def reset_hass_config(hass: ha.HomeAssistant) -> None:
    """Reset the home assistant configuration"""
    config = {
        "unit_system": "metric",
        "time_zone": "UTC",
        "name": "Home",
        "latitude": 0,
        "longitude": 0,
        "elevation": 0,
    }
    await async_process_ha_core_config(hass, config)


class IUExam:
    """Class for running tests"""

    default_config_dir = TEST_CONFIG_DIR

    def __init__(self, hass: ha.HomeAssistant, config_file: str) -> None:
        self._hass = hass
        self._config_file = config_file
        self._coordinator: IUCoordinator = None
        self._current_time: datetime = None
        self._core_config_changed = False
        self._config_directory = type(self).default_config_dir
        self._no_check = False

    @property
    def coordinator(self) -> IUCoordinator:
        """Return the coordinator"""
        return self._coordinator

    @property
    def config_directory(self) -> str:
        """Return the config directory"""
        return self._config_directory

    @config_directory.setter
    def config_directory(self, value: str) -> None:
        """Set the config directory"""
        self._config_directory = value

    @staticmethod
    def quiet_mode() -> None:
        """Trun off a lot of noise"""
        quiet_mode()

    def no_check(self, check_off: bool = True) -> None:
        """Disable checking results"""
        self._no_check = check_off
        no_check(check_off)

    async def setup(self) -> None:
        """Setup the hass environment"""
        config = CONFIG_SCHEMA(
            load_yaml_config_file(self._config_directory + self._config_file)
        )
        if ha.DOMAIN in config:
            await async_process_ha_core_config(self._hass, config[ha.DOMAIN])
            self._core_config_changed = True

        if DOMAIN not in self._hass.config.components:
            await async_setup_component(self._hass, DOMAIN, config)
            await self._hass.async_block_till_done()
            self._coordinator: IUCoordinator = self._hass.data[DOMAIN][COORDINATOR]
        else:
            self._coordinator: IUCoordinator = self._hass.data[DOMAIN][COORDINATOR]
            self._coordinator.load(config[DOMAIN])

    async def restore(self) -> None:
        """Reset home assistant parameters"""
        if self._core_config_changed:
            await reset_hass_config(self._hass)
            self._core_config_changed = False

    async def __aenter__(self):
        await self.setup()
        return self

    async def __aexit__(self, *args):
        await self.restore()

    async def begin_test(self, test_no: int) -> None:
        """Start a test"""
        self._current_time = await begin_test(test_no, self._coordinator)

    async def finish_test(self) -> None:
        """Finish a test"""
        await finish_test(self._hass, self._coordinator, self._current_time, True)

    async def run_until(self, stop_at: datetime) -> None:
        """Run until a point in time"""
        self._current_time = await run_until(
            self._hass, self._coordinator, self._current_time, stop_at, True
        )

    async def run_for(self, duration: timedelta) -> None:
        """Run for a period of time"""
        self._current_time = await run_for(
            self._hass, self._coordinator, self._current_time, duration, True
        )

    async def run_for_1_tick(self) -> None:
        """Run for 1 tick of the clock"""
        self._current_time = await run_for_1_tick(
            self._hass, self._coordinator, self._current_time, True
        )

    async def run_all(self) -> None:
        """Run all tests"""
        for test in range(self._coordinator.tester.total_tests):
            self._current_time = await begin_test(test + 1, self._coordinator)
            await finish_test(self._hass, self._coordinator, self._current_time, True)

    def check_summary(self) -> None:
        """Check the test results"""
        check_summary(self._config_directory + self._config_file, self._coordinator)
