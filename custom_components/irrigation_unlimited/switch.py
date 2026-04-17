"""Switch platform for irrigation_unlimited."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant

from .irrigation_unlimited import (
    IUCoordinator,
    IUController,
    IUZone,
    IUSequence,
    IUSchedule,
)
from .const import (
    COORDINATOR,
    DOMAIN,
    SERVICE_CANCEL,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_MANUAL_RUN,
)


def _build_entities(coordinator: IUCoordinator) -> list:
    """Build enable/disable switch entities for zones, sequences, and schedules."""
    entities = []
    for controller in coordinator.controllers:
        if controller.master_sensor is not None:
            entities.append(IUControllerManualSwitch(coordinator, controller))
        for zone in controller.zones:
            entities.append(IUZoneEnableSwitch(coordinator, controller, zone))
            for schedule in zone.schedules:
                entities.append(
                    IUZoneScheduleEnableSwitch(coordinator, controller, zone, schedule)
                )
        for sequence in controller.sequences:
            entities.append(
                IUSequenceEnableSwitch(coordinator, controller, sequence)
            )
            for schedule in sequence.schedules:
                entities.append(
                    IUSequenceScheduleEnableSwitch(
                        coordinator, controller, sequence, schedule
                    )
                )
    return entities


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None) -> None:
    """Setup switch platform (YAML path)."""
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]
    async_add_entities(_build_entities(coordinator))


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Setup switch platform (config entry / UI path)."""
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]
    async_add_entities(_build_entities(coordinator))


class IUControllerManualSwitch(SwitchEntity):
    """Switch to manually turn the master valve on (run all zones) or off (cancel)."""

    def __init__(
        self,
        coordinator: IUCoordinator,
        controller: IUController,
    ):
        self._coordinator = coordinator
        self._controller = controller

    @property
    def unique_id(self) -> str:
        return f"{self._controller.unique_id}_manual"

    @property
    def name(self) -> str:
        return f"{self._controller.name} Manual"

    @property
    def icon(self) -> str:
        return "mdi:valve"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._controller.unique_id)},
            "name": self._controller.name,
            "manufacturer": "Irrigation Unlimited",
        }

    @property
    def is_on(self) -> bool:
        return self._controller.is_on

    async def async_turn_on(self, **kwargs) -> None:
        self._coordinator.service_call(
            SERVICE_MANUAL_RUN, self._controller, None, None, {}
        )
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._coordinator.service_call(
            SERVICE_CANCEL, self._controller, None, None, {}
        )
        self.async_write_ha_state()


class IUZoneEnableSwitch(SwitchEntity):
    """Switch to enable/disable a zone."""

    def __init__(
        self,
        coordinator: IUCoordinator,
        controller: IUController,
        zone: IUZone,
    ):
        self._coordinator = coordinator
        self._controller = controller
        self._zone = zone

    @property
    def unique_id(self) -> str:
        return f"{self._zone.unique_id}_enabled"

    @property
    def name(self) -> str:
        return f"{self._zone.name} Enabled"

    @property
    def icon(self) -> str:
        return "mdi:toggle-switch"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._zone.unique_id)},
            "name": self._zone.name,
            "manufacturer": "Irrigation Unlimited",
        }

    @property
    def is_on(self) -> bool:
        return self._zone.enabled

    async def async_turn_on(self, **kwargs) -> None:
        self._coordinator.service_call(
            SERVICE_ENABLE, self._controller, self._zone, None, {}
        )
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._coordinator.service_call(
            SERVICE_DISABLE, self._controller, self._zone, None, {}
        )
        self.async_write_ha_state()


class IUSequenceEnableSwitch(SwitchEntity):
    """Switch to enable/disable a sequence."""

    def __init__(
        self,
        coordinator: IUCoordinator,
        controller: IUController,
        sequence: IUSequence,
    ):
        self._coordinator = coordinator
        self._controller = controller
        self._sequence = sequence

    @property
    def unique_id(self) -> str:
        return f"{self._sequence.unique_id}_enabled"

    @property
    def name(self) -> str:
        return f"{self._sequence.name} Enabled"

    @property
    def icon(self) -> str:
        return "mdi:toggle-switch"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._sequence.unique_id)},
            "name": self._sequence.name,
            "manufacturer": "Irrigation Unlimited",
        }

    @property
    def is_on(self) -> bool:
        return self._sequence.enabled

    async def async_turn_on(self, **kwargs) -> None:
        self._coordinator.service_call(
            SERVICE_ENABLE, self._controller, None, self._sequence, {}
        )
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._coordinator.service_call(
            SERVICE_DISABLE, self._controller, None, self._sequence, {}
        )
        self.async_write_ha_state()


class IUZoneScheduleEnableSwitch(SwitchEntity):
    """Switch to enable/disable a zone schedule."""

    def __init__(
        self,
        coordinator: IUCoordinator,
        controller: IUController,
        zone: IUZone,
        schedule: IUSchedule,
    ):
        self._coordinator = coordinator
        self._controller = controller
        self._zone = zone
        self._schedule = schedule

    @property
    def unique_id(self) -> str:
        return f"{self._zone.unique_id}_s{self._schedule.index + 1}_enabled"

    @property
    def name(self) -> str:
        sname = self._schedule.name or f"Schedule {self._schedule.index + 1}"
        return f"{self._zone.name} {sname} Enabled"

    @property
    def icon(self) -> str:
        return "mdi:calendar-clock"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def is_on(self) -> bool:
        return self._schedule.enabled

    async def async_turn_on(self, **kwargs) -> None:
        self._schedule.enabled = True
        self._coordinator.remuster()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._schedule.enabled = False
        self._coordinator.remuster()
        self.async_write_ha_state()


class IUSequenceScheduleEnableSwitch(SwitchEntity):
    """Switch to enable/disable a sequence schedule."""

    def __init__(
        self,
        coordinator: IUCoordinator,
        controller: IUController,
        sequence: IUSequence,
        schedule: IUSchedule,
    ):
        self._coordinator = coordinator
        self._controller = controller
        self._sequence = sequence
        self._schedule = schedule

    @property
    def unique_id(self) -> str:
        return f"{self._sequence.unique_id}_s{self._schedule.index + 1}_enabled"

    @property
    def name(self) -> str:
        sname = self._schedule.name or f"Schedule {self._schedule.index + 1}"
        return f"{self._sequence.name} {sname} Enabled"

    @property
    def icon(self) -> str:
        return "mdi:calendar-clock"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def is_on(self) -> bool:
        return self._schedule.enabled

    async def async_turn_on(self, **kwargs) -> None:
        self._schedule.enabled = True
        self._coordinator.remuster()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._schedule.enabled = False
        self._coordinator.remuster()
        self.async_write_ha_state()
