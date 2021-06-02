from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import ServiceCall
from homeassistant.helpers.restore_state import RestoreEntity
import json

from homeassistant.const import (
    STATE_OK,
)

from .irrigation_unlimited import (
    IUCoordinator,
    IUController,
    IUZone,
)

from .const import (
    ATTR_ENABLED,
    BINARY_SENSOR,
    DOMAIN,
    COORDINATOR,
    ICON,
    SERVICE_ENABLE,
    SERVICE_DISABLE,
)


class IUEntity(BinarySensorEntity, RestoreEntity):
    def __init__(
        self,
        coordinator: IUCoordinator,
        controller: IUController,
        zone: IUZone,
    ):
        self._coordinator = coordinator
        self._controller = controller
        self._zone = zone  # This will be None if it belongs to a Master/Controller
        self.entity_id = f"{BINARY_SENSOR}.{DOMAIN}_c{self._controller.index + 1}"
        if self._zone is None:
            self.entity_id = self.entity_id + "_m"
        else:
            self.entity_id = self.entity_id + f"_z{self._zone.index + 1}"
        return

    async def async_added_to_hass(self):
        self._coordinator.register_entity(self._controller, self._zone, self)
        state = await self.async_get_last_state()
        if state is not None:
            if ATTR_ENABLED in state.attributes:
                if state.attributes[ATTR_ENABLED]:
                    self._coordinator.service_call(
                        SERVICE_ENABLE, self._controller, self._zone, None
                    )
                else:
                    self._coordinator.service_call(
                        SERVICE_DISABLE, self._controller, self._zone, None
                    )
            return
        return

    async def async_will_remove_from_hass(self):
        self._coordinator.deregister_entity(self._controller, self._zone, self)
        return

    def dispatch(self, service: str, call: ServiceCall) -> None:
        self._coordinator.service_call(service, self._controller, self._zone, call.data)
        return

    @property
    def controller(self) -> IUController:
        return self._controller

    @property
    def zone(self) -> IUZone:
        return self._zone


class IUComponent(RestoreEntity):
    """Representation of IrrigationUnlimitedCoordinator"""

    def __init__(self, coordinator: IUCoordinator):
        self._coordinator = coordinator
        self.entity_id = f"{DOMAIN}.{COORDINATOR}"
        return

    async def async_added_to_hass(self):
        self._coordinator.register_entity(None, None, self)
        return

    async def async_will_remove_from_hass(self):
        self._coordinator.deregister_entity(None, None, self)
        return

    def dispatch(self, service: str, call: ServiceCall) -> None:
        self._coordinator.service_call(service, None, None, call.data)
        return

    @property
    def should_poll(self):
        """If entity should be polled"""
        return False

    @property
    def unique_id(self):
        """Return a unique ID."""
        return "coordinator"

    @property
    def name(self):
        """Return the name of the integration."""
        return "Irrigation Unlimited Coordinator"

    @property
    def state(self):
        """Return the state of the entity."""
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
