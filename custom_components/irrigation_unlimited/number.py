"""Number platform for irrigation_unlimited — manual run duration."""

from datetime import timedelta

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant

from .irrigation_unlimited import IUCoordinator, IUController, IUZone, IUSequence
from .const import (
    COORDINATOR,
    DOMAIN,
    NUMBER_ENTITIES,
)

_DEFAULT_MINUTES = 10
_MIN_MINUTES = 1
_MAX_MINUTES = 240


def _default_minutes(duration: timedelta | None) -> float:
    if duration is None:
        return float(_DEFAULT_MINUTES)
    return max(_MIN_MINUTES, duration.total_seconds() / 60)


def _build_entities(coordinator: IUCoordinator) -> list:
    entities = []
    for controller in coordinator.controllers:
        for zone in controller.zones:
            entities.append(IUZoneRunDuration(coordinator, controller, zone))
        for sequence in controller.sequences:
            entities.append(IUSequenceRunDuration(coordinator, controller, sequence))
    return entities


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None) -> None:
    """Setup number platform (YAML path)."""
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]
    entities = _build_entities(coordinator)
    hass.data[DOMAIN][NUMBER_ENTITIES] = {e.unique_id: e for e in entities}
    async_add_entities(entities)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Setup number platform (config entry / UI path)."""
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]
    entities = _build_entities(coordinator)
    hass.data[DOMAIN][NUMBER_ENTITIES] = {e.unique_id: e for e in entities}
    async_add_entities(entities)


class IUZoneRunDuration(NumberEntity):
    """Duration (minutes) used when manually running a zone."""

    def __init__(
        self,
        coordinator: IUCoordinator,
        controller: IUController,
        zone: IUZone,
    ):
        self._coordinator = coordinator
        self._controller = controller
        self._zone = zone
        self._attr_native_value = _default_minutes(zone._duration)

    @property
    def unique_id(self) -> str:
        return f"{self._zone.unique_id}_run_duration"

    @property
    def name(self) -> str:
        return f"{self._controller.name} {self._zone.name} Run Duration"

    @property
    def icon(self) -> str:
        return "mdi:timer-outline"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def native_min_value(self) -> float:
        return float(_MIN_MINUTES)

    @property
    def native_max_value(self) -> float:
        return float(_MAX_MINUTES)

    @property
    def native_step(self) -> float:
        return 1.0

    @property
    def native_unit_of_measurement(self) -> str:
        return "min"

    @property
    def mode(self) -> NumberMode:
        return NumberMode.BOX

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._zone.unique_id)},
            "name": self._zone.name,
            "manufacturer": "Irrigation Unlimited",
        }

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()


class IUSequenceRunDuration(NumberEntity):
    """Duration (minutes) used when manually running a sequence."""

    def __init__(
        self,
        coordinator: IUCoordinator,
        controller: IUController,
        sequence: IUSequence,
    ):
        self._coordinator = coordinator
        self._controller = controller
        self._sequence = sequence
        self._attr_native_value = _default_minutes(sequence.duration)

    @property
    def unique_id(self) -> str:
        return f"{self._sequence.unique_id}_run_duration"

    @property
    def name(self) -> str:
        return f"{self._controller.name} {self._sequence.name} Run Duration"

    @property
    def icon(self) -> str:
        return "mdi:timer-outline"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def native_min_value(self) -> float:
        return float(_MIN_MINUTES)

    @property
    def native_max_value(self) -> float:
        return float(_MAX_MINUTES)

    @property
    def native_step(self) -> float:
        return 1.0

    @property
    def native_unit_of_measurement(self) -> str:
        return "min"

    @property
    def mode(self) -> NumberMode:
        return NumberMode.BOX

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._sequence.unique_id)},
            "name": self._sequence.name,
            "manufacturer": "Irrigation Unlimited",
        }

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
