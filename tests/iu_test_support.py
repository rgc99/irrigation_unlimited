"""Irrigation Unlimited test support routines"""

import os
from unittest.mock import patch
import logging
from typing import Any
from datetime import datetime, timedelta, timezone
from homeassistant.const import SERVICE_RELOAD
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
from homeassistant.util.dt import parse_datetime, as_utc, as_local, UTC

from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
    IUController,
    IURun,
)
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    COORDINATOR,
)
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
logging.getLogger("custom_components.irrigation_unlimited").setLevel(logging.DEBUG)

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


logging.getLogger("custom_components.irrigation_unlimited").setLevel(logging.DEBUG)


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
        self._config_directory, self._config_file = os.path.split(config_file)
        if self._config_directory == "":
            self._config_directory = type(self).default_config_dir
        self._coordinator: IUCoordinator = None
        self._current_time: datetime = None
        self._last_stop: datetime = None
        self._core_config_changed = False
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
        return os.path.join(self._config_directory, self._config_file)

    @property
    def virtual_time(self) -> datetime:
        """Return the current virtual time"""
        return self._coordinator.tester.current_test.virtual_time(self._current_time)

    @property
    def last_stop(self) -> datetime:
        """Return the last run_until time"""
        return as_local(self._last_stop)

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

    def lvts(self, atime: datetime) -> str:
        """Return the actual time as virtual in local as a string"""
        ltime = self.lvt(atime)
        if ltime is not None:
            return fmt_local(ltime)
        return None

    def no_check(self, check_off: bool = True) -> None:
        """Disable checking results"""
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
        self._coordinator.history.finalise()
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
        self._last_stop = self._coordinator.tester.virtual_time(self._current_time)
        self._coordinator.clock.test_ticker_update(self._current_time)
        await self._hass.async_block_till_done()
        _LOGGER.debug("Starting test: %s", self._coordinator.tester.current_test.name)

    async def finish_test(self) -> None:
        """Finish a test"""

        await self.run_until(None)
        self.check_labyrinth()

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
        self._last_stop = stop_at
        if stop_at is not None:
            astop_at = self._coordinator.tester.actual_time(stop_at)
        else:
            astop_at = datetime.max.replace(tzinfo=timezone.utc)
        while self._coordinator.tester.is_testing and self._current_time <= astop_at:
            # Get next scheduled clock tick
            next_awakening = self._coordinator.clock.next_awakening(self._current_time)
            assert next_awakening != self._current_time, "Infinite loop detected"
            self._coordinator.clock.test_ticker_update(next_awakening)
            await self._hass.async_block_till_done()
            self._coordinator.tester.ticker = min(next_awakening, astop_at)
            if next_awakening <= astop_at:
                self._coordinator.timer(next_awakening)
                self._coordinator.clock.test_ticker_fired(next_awakening)
                await self._hass.async_block_till_done()
                self._current_time = next_awakening
            else:
                break

    async def run_for(self, duration: timedelta | str) -> None:
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
        await self._hass.async_block_till_done()
        self.check_labyrinth()

    async def reload(self, config: str) -> None:
        """Reload the specified config file"""
        self._config_file = config
        with patch(
            "homeassistant.core.Config.path",
            return_value=self.config_file_full,
        ):
            await self.call(SERVICE_RELOAD)

    def check_summary(self, config_file: str = None) -> None:
        """Check the test results"""
        # pylint: disable=logging-fstring-interpolation
        if config_file is None:
            config_file = self.config_file_full
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

    def check_labyrinth(self) -> None:
        """Check the run integrity between controller, zone and sequence runs"""

        def print_run(run: IURun) -> None:
            schedule = run.schedule.name if run.schedule else "manual"
            print(
                f"zone: {run.zone.id1}, "
                f"start: {fmt_local(run.start_time)}, "
                f"schedule: {schedule}"
            )

        def check_controller(controller: IUController) -> None:
            lst = list(controller.runs)
            controller_runs: set[IURun] = set(lst)
            assert len(lst) == len(controller_runs), "Controller runs not unique"

            lst = []
            for zone in controller.zones:
                lst.extend(zone.runs)
            zone_runs: set[IURun] = set(lst)
            assert len(lst) == len(zone_runs), "Zone runs not unique"

            lst = []
            for sequence in controller.sequences:
                for sqr in sequence.runs:
                    lst.extend(sqr.runs)
            sequence_runs: set[IURun] = set(lst)
            assert len(lst) == len(sequence_runs), "Sequence runs not unique"

            sqr = set(run for run in zone_runs if run.sequence is not None)
            if sequence_runs != sqr:
                if len(sequence_runs) > len(sqr):
                    print("Sequence contains more items than zone")
                else:
                    print("Zone contains more items than sequence")
                for run in sorted(
                    sqr.symmetric_difference(sequence_runs),
                    key=lambda run: run.start_time,
                ):
                    print_run(run)
                assert False, "Zone and sequence runs not identical"

            referred = set(
                run.master_run for run in zone_runs if run.master_run is not None
            )
            if controller_runs != referred:
                if len(controller_runs) > len(referred):
                    print("Controller contains more items than referred zone")
                else:
                    print("Referred zone contains more items than controller")
                for run in zone_runs:
                    print_run(run)
                for run in sorted(
                    referred.symmetric_difference(controller_runs),
                    key=lambda run: run.start_time,
                ):
                    print_run(run)
                assert False, "Controller and referred zone runs not identical"

            referrer = set(run for run in zone_runs if run.master_run is not None)
            if zone_runs != referrer:
                if len(zone_runs) > len(referrer):
                    print("Zone contains more items than referred zone")
                else:
                    print("Referred zone contains more items than zone")
                for run in sorted(
                    referrer.symmetric_difference(zone_runs),
                    key=lambda run: run.start_time,
                ):
                    print_run(run)
                assert False, "Zone and referred zone runs not identical"

            assert len(zone_runs) == len(
                controller_runs
            ), f"Controller ({len(controller_runs)}) and zones ({len(zone_runs)}) not identical"

        for controller in self._coordinator.controllers:
            check_controller(controller)

    def check_attr(self, fields: dict, attr: dict) -> None:
        """Check the specified fields in the attributes"""

        def check_field(field: str, expected, attribute) -> dict:
            result = {}
            if attribute != expected:
                if isinstance(expected, datetime):
                    expected = fmt_local(expected)
                if isinstance(attribute, datetime):
                    attribute = fmt_local(attribute)
                result[field] = {}
                result[field]["expected"] = expected
                result[field]["found"] = attribute
            return result

        bad = {}
        for field in fields:
            if field in attr:
                if isinstance(fields[field], list):
                    if len(fields[field]) < len(attr[field]):
                        bad[field] = "List has more items"
                    elif len(fields[field]) > len(attr[field]):
                        bad[field] = "List has fewer items"
                    else:
                        for count, item in enumerate(fields[field]):
                            if isinstance(item, dict):
                                self.check_attr(item, attr[field][count])
                            else:
                                bad |= check_field(field, item, attr[field][count])
                else:
                    bad |= check_field(field, fields[field], attr[field])
            else:
                bad[field] = "NOT FOUND"
        assert not bad, f"Attributes do not match {bad}"

    def check_iu_entity(self, iu_id: str, state: str, fields: dict) -> None:
        """Check the irrigation unlimited entity"""
        entity_id = "binary_sensor.irrigation_unlimited_" + iu_id
        entity = self._hass.states.get(entity_id)
        assert entity is not None, f"IU entity {entity_id} not found"
        assert (
            entity.state == state
        ), f"State does not match: expected: {state} found: {entity.state}"
        self.check_attr(fields, entity.attributes)

    def print_iu_entity(self, iu_id: str) -> None:
        """Print out the irrigation unlimited entity in a format compatible
        with check_iu_entity"""
        indent = "        "

        def output(level: int, data: str) -> None:
            print(f"{indent}{' ' * (level - 1) * 4}{data}")

        def print_value(value: Any) -> str:
            if isinstance(value, datetime):
                if value.tzinfo == UTC:
                    value = as_local(value)
                return f'mk_local("{value.strftime("%Y-%m-%d %H:%M:%S")}")'
            elif isinstance(value, str):
                return f'"{value}"'
            else:
                return f"{value}"

        def print_attrs(level: int, attrs: dict[str, Any]) -> None:
            output(level, "{")
            for key, value in attrs:
                if (
                    isinstance(value, list)
                    and len(value) > 0
                    and isinstance(value[0], dict)
                ):
                    # Assume a list of all one type
                    output(level + 1, f'"{key}": [')
                    for item in value:
                        if isinstance(item, dict):
                            print_attrs(level + 2, item.items())
                    output(level + 1, "],")
                else:
                    output(level + 1, f'"{key}": {print_value(value)},')
            output(level, "},")

        def print_entity(iu_id: str) -> None:
            entity_id = "binary_sensor.irrigation_unlimited_" + iu_id
            entity = self._hass.states.get(entity_id)
            assert entity is not None, f"IU entity {entity_id} not found"
            output(1, "exam.check_iu_entity(")
            output(2, f'"{iu_id}",')
            if entity.state == "on":
                output(2, "STATE_ON,")
            else:
                output(2, "STATE_OFF,")
            print_attrs(2, entity.attributes.items())
            output(1, ")")

        if isinstance(iu_id, str):
            iu_id = [iu_id]
        for ent in iu_id:
            print_entity(ent)


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


def fmt_local(adate: datetime) -> str:
    """Format the datetime into local format"""
    return as_local(adate).strftime("%Y-%m-%d %H:%M:%S")
