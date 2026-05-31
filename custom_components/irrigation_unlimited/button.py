"""Button platform for irrigation_unlimited."""

from datetime import timedelta

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant

from .irrigation_unlimited import IUCoordinator, IUController, IUZone, IUSequence
from .const import (
    BUTTON,
    CONF_TIME,
    COORDINATOR,
    DOMAIN,
    NUMBER_ENTITIES,
    SERVICE_MANUAL_RUN,
)


def _build_entities(coordinator: IUCoordinator) -> list:
    """Build run-now button entities for all zones and sequences."""
    entities = []
    for controller in coordinator.controllers:
        for zone in controller.zones:
            entities.append(IUZoneRunButton(coordinator, controller, zone))
        for sequence in controller.sequences:
            entities.append(IUSequenceRunButton(coordinator, controller, sequence))
    return entities


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None) -> None:
    """Setup button platform (YAML path)."""
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]
    async_add_entities(_build_entities(coordinator))


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Setup button platform (config entry / UI path)."""
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]
    async_add_entities(_build_entities(coordinator))


class IUZoneRunButton(ButtonEntity):
    """Button to run a zone now."""

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
        return f"{self._zone.unique_id}_run"

    @property
    def name(self) -> str:
        return f"{self._controller.name} {self._zone.name} Run"

    @property
    def icon(self) -> str:
        return "mdi:play-circle"

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

    async def async_press(self) -> None:
        """Run the zone now using the configured run duration."""
        data = {}
        num_uid = f"{self._zone.unique_id}_run_duration"
        num_entity = self.hass.data[DOMAIN].get(NUMBER_ENTITIES, {}).get(num_uid)
        if num_entity is not None and num_entity.native_value:
            data = {CONF_TIME: timedelta(minutes=num_entity.native_value)}
        self._coordinator.service_call(
            SERVICE_MANUAL_RUN,
            self._controller,
            self._zone,
            None,
            data,
        )


class IUSequenceRunButton(ButtonEntity):
    """Button to run a sequence now."""

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
        return f"{self._sequence.unique_id}_run"

    @property
    def name(self) -> str:
        return f"{self._controller.name} {self._sequence.name} Run"

    @property
    def icon(self) -> str:
        return "mdi:play-circle"

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

    async def async_press(self) -> None:
        """Run the sequence now using the configured run duration."""
        data = {}
        num_uid = f"{self._sequence.unique_id}_run_duration"
        num_entity = self.hass.data[DOMAIN].get(NUMBER_ENTITIES, {}).get(num_uid)
        if num_entity is not None and num_entity.native_value:
            data = {CONF_TIME: timedelta(minutes=num_entity.native_value)}
        self._coordinator.service_call(
            SERVICE_MANUAL_RUN,
            self._controller,
            None,
            self._sequence,
            data,
        )
