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
    IUAdjustment,
)

from .const import (
    ATTR_ADJUSTMENT,
    ATTR_CONFIGURATION,
    ATTR_ENABLED,
    CONF_CONTROLLERS,
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
    SERVICE_TIME_ADJUST,
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

        # This code should be removed in future update. Moved to coordinator JSON configuration.
        if not self._coordinator.restored_from_configuration:
            state = await self.async_get_last_state()
            if state is None:
                return
            service = (
                SERVICE_ENABLE
                if state.attributes.get(ATTR_ENABLED, True)
                else SERVICE_DISABLE
            )
            self._coordinator.service_call(service, self._controller, self._zone, {})
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
        state = await self.async_get_last_state()
        if state is None or ATTR_CONFIGURATION not in state.attributes:
            return
        json_data = state.attributes.get(ATTR_CONFIGURATION, {})
        try:
            data = json.loads(json_data)
            for ctrl in data.get(CONF_CONTROLLERS, []):
                controller = self._coordinator.controllers[ctrl[CONF_INDEX]]
                service = (
                    SERVICE_ENABLE if ctrl.get(CONF_ENABLED, True) else SERVICE_DISABLE
                )
                self._coordinator.service_call(service, controller, None, {})

                for zne in ctrl.get(CONF_ZONES, []):
                    zone = controller.zones[zne[CONF_INDEX]]
                    service = (
                        SERVICE_ENABLE
                        if zne.get(CONF_ENABLED, True)
                        else SERVICE_DISABLE
                    )
                    self._coordinator.service_call(service, controller, zone, {})

                    data = IUAdjustment(zne.get(ATTR_ADJUSTMENT)).to_dict()
                    if data != {}:
                        self._coordinator.service_call(
                            SERVICE_TIME_ADJUST, controller, zone, data
                        )

                for sequence in ctrl.get(CONF_SEQUENCES, []):
                    service = (
                        SERVICE_ENABLE
                        if sequence.get(CONF_ENABLED, True)
                        else SERVICE_DISABLE
                    )
                    self._coordinator.service_call(
                        service,
                        controller,
                        None,
                        {CONF_SEQUENCE_ID: sequence[CONF_INDEX] + 1},
                    )

                    data = IUAdjustment(sequence.get(ATTR_ADJUSTMENT)).to_dict()
                    if data != {}:
                        data[CONF_SEQUENCE_ID] = sequence[CONF_INDEX] + 1
                        self._coordinator.service_call(
                            SERVICE_TIME_ADJUST, controller, None, data
                        )

                    for sequence_zone in sequence.get(CONF_SEQUENCE_ZONES, []):
                        service = (
                            SERVICE_ENABLE
                            if sequence_zone.get(CONF_ENABLED, True)
                            else SERVICE_DISABLE
                        )
                        self._coordinator.service_call(
                            service,
                            controller,
                            None,
                            {
                                CONF_SEQUENCE_ID: sequence[CONF_INDEX] + 1,
                                CONF_ZONES: [sequence_zone[CONF_INDEX] + 1],
                            },
                        )

                        data = IUAdjustment(
                            sequence_zone.get(ATTR_ADJUSTMENT)
                        ).to_dict()
                        if data != {}:
                            data[CONF_SEQUENCE_ID] = sequence[CONF_INDEX] + 1
                            data[CONF_ZONES] = [sequence_zone[CONF_INDEX] + 1]
                            self._coordinator.service_call(
                                SERVICE_TIME_ADJUST, controller, None, data
                            )
            self._coordinator.restored_from_configuration = True
        # pylint: disable=broad-except
        except Exception as exc:
            self._coordinator.logger.log_bad_config(str(exc), json_data)
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
        attr[ATTR_CONFIGURATION] = self._coordinator.configuration
        return attr
