"""HA entity classes"""
import json
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import ServiceCall
from homeassistant.helpers.restore_state import RestoreEntity

from homeassistant.const import (
    STATE_OK,
)

from .irrigation_unlimited import (
    IUCoordinator,
    IUController,
    IUZone,
)

from .const import (
    ATTR_CONFIGURATION,
    ATTR_ENABLED,
    CONF_ENABLED,
    CONF_INDEX,
    CONF_SEQUENCE_ID,
    CONF_SEQUENCE_ZONES,
    CONF_SEQUENCES,
    CONF_ZONES,
    COORDINATOR,
    ICON,
    SERVICE_ENABLE,
    SERVICE_DISABLE,
    STATUS_INITIALISING,
)


class IUEntity(BinarySensorEntity, RestoreEntity):
    """Base class for entities"""

    def __init__(
        self,
        coordinator: IUCoordinator,
        controller: IUController,
        zone: IUZone,
    ):
        """Base entity class"""
        self._coordinator = coordinator
        self._controller = controller
        self._zone = zone  # This will be None if it belongs to a Master/Controller
        if self._zone is None:
            self.entity_id = self._controller.entity_id
        else:
            self.entity_id = self._zone.entity_id

    async def async_added_to_hass(self):
        self._coordinator.register_entity(self._controller, self._zone, self)
        state = await self.async_get_last_state()
        if state is None:
            return

        service = (
            SERVICE_ENABLE
            if state.attributes.get(ATTR_ENABLED, True)
            else SERVICE_DISABLE
        )
        self._coordinator.service_call(service, self._controller, self._zone, {})

        if self._zone is None and ATTR_CONFIGURATION in state.attributes:
            data = json.loads(state.attributes[ATTR_CONFIGURATION])
            for sequence in data[CONF_SEQUENCES]:
                service = (
                    SERVICE_ENABLE
                    if sequence.get(CONF_ENABLED, True)
                    else SERVICE_DISABLE
                )
                self._coordinator.service_call(
                    service,
                    self._controller,
                    self._zone,
                    {CONF_SEQUENCE_ID: sequence[CONF_INDEX] + 1},
                )

                for sequence_zone in sequence[CONF_SEQUENCE_ZONES]:
                    service = (
                        SERVICE_ENABLE
                        if sequence_zone.get(CONF_ENABLED, True)
                        else SERVICE_DISABLE
                    )
                    self._coordinator.service_call(
                        service,
                        self._controller,
                        self._zone,
                        {
                            CONF_SEQUENCE_ID: sequence[CONF_INDEX] + 1,
                            CONF_ZONES: [sequence_zone[CONF_INDEX] + 1],
                        },
                    )
        return

    async def async_will_remove_from_hass(self):
        self._coordinator.deregister_entity(self._controller, self._zone, self)
        return

    def dispatch(self, service: str, call: ServiceCall) -> None:
        """Dispatcher for service calls"""
        self._coordinator.service_call(service, self._controller, self._zone, call.data)


class IUComponent(RestoreEntity):
    """Representation of IrrigationUnlimitedCoordinator"""

    def __init__(self, coordinator: IUCoordinator):
        self._coordinator = coordinator
        self.entity_id = self._coordinator.entity_id

    async def async_added_to_hass(self):
        self._coordinator.register_entity(None, None, self)
        return

    async def async_will_remove_from_hass(self):
        self._coordinator.deregister_entity(None, None, self)
        return

    def dispatch(self, service: str, call: ServiceCall) -> None:
        """Service call dispatcher"""
        self._coordinator.service_call(service, None, None, call.data)

    @property
    def should_poll(self):
        """If entity should be polled"""
        return False

    @property
    def unique_id(self):
        """Return a unique ID."""
        return COORDINATOR

    @property
    def name(self):
        """Return the name of the integration."""
        return "Irrigation Unlimited Coordinator"

    @property
    def state(self):
        """Return the state of the entity."""
        if not self._coordinator.initialised:
            return STATUS_INITIALISING
        return STATE_OK

    @property
    def icon(self):
        """Return the icon to be used for this entity"""
        return ICON

    @property
    def state_attributes(self):
        """Return the state attributes."""
        attr = {}
        attr["configuration"] = json.dumps(self._coordinator.as_dict(), default=str)
        return attr
