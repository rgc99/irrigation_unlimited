"""Irrigation Unlimited test support routines"""
import logging
from typing import Any
from datetime import datetime, timedelta, timezone
import homeassistant.core as ha
from homeassistant.config import (
    load_yaml_config_file,
    async_process_ha_core_config,
)
from homeassistant.setup import async_setup_component
from homeassistant.helpers.recorder import (
    async_initialize_recorder,
    async_wait_recorder,
)
from homeassistant.helpers.typing import ConfigType
from homeassistant.util.dt import parse_datetime, as_utc, as_local

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
    logging.getLogger("homeassistant.loader").setLevel(logging.ERROR)


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

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

    default_config_dir = TEST_CONFIG_DIR

    def __init__(self, hass: ha.HomeAssistant, config_file: str) -> None:
        self._hass = hass
        self._config_file = config_file
        self._coordinator: IUCoordinator = None
        self._current_time: datetime = None
        self._core_config_changed = False
        self._config_directory = type(self).default_config_dir
        self._no_check = False
        self._config: ConfigType = None

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

    @property
    def config_file(self) -> str:
        """Return the config filename"""
        return self._config_file

    @property
    def config_file_full(self) -> str:
        """Return the full path to the config file"""
        return self._config_directory + self._config_file

    @property
    def virtual_time(self) -> datetime:
        """Return the current virtual time"""
        return self._coordinator.tester.current_test.virtual_time(self._current_time)

    @property
    def config(self) -> ConfigType:
        """Return the processed config file"""
        return self._config

    @staticmethod
    def quiet_mode() -> None:
        """Trun off a lot of noise"""
        quiet_mode()

    def lvt(self, atime: datetime) -> datetime:
        """Return the actual time as virtual in local"""
        if atime is not None:
            return as_local(self._coordinator.tester.virtual_time(as_utc(atime)))
        return None

    def no_check(self, check_off: bool = True) -> None:
        """Disable checking results"""
        # pylint: disable=no-self-use
        global NO_CHECK
        NO_CHECK = check_off
        if NO_CHECK:
            _LOGGER.debug(
                "WARNING: Checks are disabled==================================="
            )

    async def load_component(self, domain: str, config: ConfigType = None) -> None:
        """Load a domain"""
        if config is None:
            config = self._config
        await async_setup_component(self._hass, domain, config)
        await self._hass.async_block_till_done()

    async def load_dependencies(self) -> None:
        """Load IU dependencies"""
        async_initialize_recorder(self._hass)
        await self.load_component("http", {})
        await self.load_component(
            "recorder",
            {"recorder": {"db_url": "sqlite:///:memory:"}},
        )
        await async_wait_recorder(self._hass)
        await self.load_component("history", {})

    async def setup(self) -> None:
        """Setup the hass environment"""
        _LOGGER.debug("Starting exam: %s", self.config_file_full)
        self._config = CONFIG_SCHEMA(load_yaml_config_file(self.config_file_full))
        if ha.DOMAIN in self._config:
            await async_process_ha_core_config(self._hass, self._config[ha.DOMAIN])
            self._core_config_changed = True

        if DOMAIN not in self._hass.config.components:
            await self.load_component(DOMAIN)
            self._coordinator: IUCoordinator = self._hass.data[DOMAIN][COORDINATOR]
        else:
            self._coordinator: IUCoordinator = self._hass.data[DOMAIN][COORDINATOR]
            self._coordinator.load(self._config[DOMAIN])

    async def restore(self) -> None:
        """Reset home assistant parameters"""
        if self._core_config_changed:
            await reset_hass_config(self._hass)
            self._core_config_changed = False
        _LOGGER.debug("Finished exam: %s", self.config_file_full)

    async def __aenter__(self):
        self._no_check = NO_CHECK
        await self.setup()
        return self

    async def __aexit__(self, *args):
        global NO_CHECK
        NO_CHECK = self._no_check
        self._coordinator._clock.stop()
        await self.restore()

    async def begin_test(self, test_no: int) -> None:
        """Start a test"""
        self._coordinator.clock.stop()
        self._current_time = self._coordinator.start_test(test_no)
        assert self._current_time is not None, f"Invalid test {test_no}"
        self._coordinator.clock.test_ticker_update(self._current_time)
        _LOGGER.debug("Starting test: %s", self._coordinator.tester.current_test.name)
        await self._hass.async_block_till_done()

    async def finish_test(self) -> None:
        """Finish a test"""

        await self.run_until(None)

        test = self._coordinator.tester.last_test
        try:
            if not NO_CHECK:
                assert (
                    test.errors == 0
                ), f"Failed test {test.index + 1}, errors not zero"
                assert (
                    test.events <= test.total_results
                ), f"Failed test {test.index + 1}, missing event"
                assert (
                    test.events >= test.total_results
                ), f"Failed test {test.index + 1}, extra event"
        finally:
            _LOGGER.debug(
                "Finished test: %s, time: %.2fs, events: %d, results: %d, errors: %d, no_check: %s",
                test.name,
                test.test_time,
                test.events,
                test.total_results,
                test.errors,
                NO_CHECK,
            )

    async def run_until(self, stop_at: datetime | str) -> None:
        """Run until a point in time"""
        if isinstance(stop_at, str):
            stop_at = mk_utc(stop_at)
        if stop_at is not None:
            astop_at = self._coordinator.tester.actual_time(stop_at)
        else:
            astop_at = datetime.max.replace(tzinfo=timezone.utc)
        while self._coordinator.tester.is_testing and self._current_time <= astop_at:
            # Get next scheduled clock tick
            next_awakening = self._coordinator.clock.next_awakening(self._current_time)
            if self._coordinator.clock.test_ticker_update(next_awakening):
                await self._hass.async_block_till_done()
            self._coordinator.tester.ticker = min(next_awakening, astop_at)
            if next_awakening <= astop_at:
                self._coordinator.timer(next_awakening)
                self._coordinator.clock.test_ticker_fired(next_awakening)
                await self._hass.async_block_till_done()
                self._current_time = next_awakening
            else:
                break

    async def run_for(self, duration: timedelta) -> None:
        """Run for a period of time"""
        if isinstance(duration, str):
            duration = mk_td(duration)
        if duration is not None:
            stop_at = (
                self._coordinator.tester.current_test.virtual_time(self._current_time)
                + duration
            )
        else:
            stop_at = None
        await self.run_until(stop_at)

    async def run_test(self, test_no: int) -> None:
        """Run a single test"""
        await self.begin_test(test_no)
        await self.finish_test()

    async def run_all(self) -> None:
        """Run all tests"""
        for test in range(self._coordinator.tester.total_tests):
            await self.run_test(test + 1)

    async def call(self, service: str, data: dict[str, Any] = None) -> None:
        """Call IU service"""
        await self._hass.services.async_call(DOMAIN, service, data, True)

    def check_summary(self, config_file: str = None) -> None:
        """Check the test results"""
        # pylint: disable=logging-fstring-interpolation
        if config_file is None:
            config_file = self._config_directory + self._config_file
        tester = self._coordinator.tester
        try:
            if not NO_CHECK:
                assert (
                    tester.total_events == tester.total_checks == tester.total_results
                ), "Failed summary results"
                assert (
                    tester.tests_completed == tester.total_tests
                ), "Not all tests have been run"
                assert tester.total_errors == 0, "Failed summary errors"
        finally:
            _LOGGER.debug(
                f"Summary: {config_file}, "
                f"tests: {tester.total_tests}, "
                f"events: {tester.total_events}, "
                f"checks: {tester.total_checks}, "
                f"errors: {tester.total_errors}, "
                f"time: {tester.total_time:.2f}s"
            )


def mk_utc(adate: str) -> datetime:
    """Parse a datetime string assumed to be in local format
    and return in UTC"""
    return as_utc(parse_datetime(adate))


def mk_local(adate: str) -> datetime:
    """Parse a datetime string assumed to be in local format"""
    return as_local(parse_datetime(adate))


def mk_td(time_str: str) -> timedelta:
    """Convert time string to timedelta"""
    tstr = datetime.strptime(time_str, "%H:%M:%S")
    return timedelta(hours=tstr.hour, minutes=tstr.minute, seconds=tstr.second)


def parse_utc(adate: str) -> datetime:
    """Parse a datetime string assumed to be in UTC"""
    dte = parse_datetime(adate)
    if dte.tzinfo is None:
        dte = dte.replace(tzinfo=timezone.utc)
    return dte
