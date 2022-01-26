"""HA entity classes"""
import json
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import ServiceCall
from homeassistant.helpers.restore_state import RestoreEntity

from homeassistant.const import (
    CONF_STATE,
    STATE_OK,
    STATE_ON,
)

from .irrigation_unlimited import (
    IUCoordinator,
    IUController,
    IUZone,
    IUSequence,
    IUSequenceZone,
    IUAdjustment,
    IUBase,
)

from .const import (
    ATTR_ADJUSTMENT,
    ATTR_CONFIGURATION,
    ATTR_ENABLED,
    CONF_CONTROLLERS,
    CONF_ENABLED,
    CONF_INDEX,
    CONF_RESET,
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


class IURestore:
    """Restore class"""

    # pylint: disable=too-few-public-methods

    def __init__(self, data: dict, coordinator: IUCoordinator):
        self._coordinator = coordinator
        self._is_on = []

        if data is not None and isinstance(data, dict):
            for c_data in data.get(CONF_CONTROLLERS, []):
                self._restore_controller(c_data)

        self._log_is_on()

    def _log_is_on(self) -> None:
        for item in self._is_on:
            self._coordinator.logger.log_incomplete_cycle(
                item["controller"],
                item["zone"],
                item["sequence"],
                item["sequence_zone"],
            )

    def _add_to_on_list(
        self,
        controller: IUController,
        zone: IUZone = None,
        sequence: IUSequence = None,
        sequence_zone: IUSequenceZone = None,
    ) -> None:
        if sequence_zone is None:
            if sequence is not None:
                for item in self._is_on:
                    if item["sequence"] == sequence:
                        return
            elif zone is not None:
                for item in self._is_on:
                    if item["zone"] == zone:
                        return
            elif controller is not None:
                for item in self._is_on:
                    if item["controller"] == controller:
                        return
        self._is_on.append(
            {
                "controller": controller,
                "zone": zone,
                "sequence": sequence,
                "sequence_zone": sequence_zone,
            }
        )
        return

    def _check_is_on(
        self,
        data: dict,
        controller: IUController,
        zone: IUZone,
        sequence: IUSequence,
        sequence_zone: IUSequenceZone,
    ) -> None:
        # pylint: disable=too-many-arguments
        if not CONF_STATE in data:
            return
        if data.get(CONF_STATE) == STATE_ON:
            if sequence_zone is not None:
                items = data.get(CONF_ZONES)
                if isinstance(items, str):
                    items = items.split(",")  # Old style 1's based CSV
                for item in items:
                    try:
                        item = int(item)
                        # zne = controller.get_zone(int(item) - 1)
                        zne = controller.get_zone(item - sequence_zone.ZONE_OFFSET)
                        if zne is not None:
                            self._add_to_on_list(
                                controller, zne, sequence, sequence_zone
                            )
                    except ValueError:
                        pass
            else:
                self._add_to_on_list(controller, zone, sequence, sequence_zone)

    def _restore_enabled(
        self,
        data: dict,
        controller: IUController,
        zone: IUZone,
        sequence: IUSequence,
        sequence_zone: IUSequenceZone,
    ) -> None:
        # pylint: disable=too-many-arguments
        if not CONF_ENABLED in data:
            return
        svc = SERVICE_ENABLE if data.get(CONF_ENABLED) else SERVICE_DISABLE
        svd = {}
        if sequence is not None:
            svd[CONF_SEQUENCE_ID] = sequence.index + 1
            if sequence_zone is not None:
                svd[CONF_ZONES] = [sequence_zone.index + 1]
        self._coordinator.service_call(svc, controller, zone, svd)

    def _restore_adjustment(
        self,
        data: dict,
        controller: IUController,
        zone: IUZone,
        sequence: IUSequence,
        sequence_zone: IUSequenceZone,
    ) -> None:
        # pylint: disable=too-many-arguments
        if not ATTR_ADJUSTMENT in data:
            return
        if (svd := IUAdjustment(data.get(ATTR_ADJUSTMENT)).to_dict()) == {}:
            svd[CONF_RESET] = None
        if sequence is not None:
            svd[CONF_SEQUENCE_ID] = sequence.index + 1
            if sequence_zone is not None:
                svd[CONF_ZONES] = [sequence_zone.index + 1]
        self._coordinator.service_call(SERVICE_TIME_ADJUST, controller, zone, svd)

    def _restore_sequence_zone(
        self, data: dict, controller: IUController, sequence: IUSequence
    ) -> None:
        if (sequence_zone := sequence.get_zone(data.get(CONF_INDEX))) is None:
            return
        self._restore_enabled(data, controller, None, sequence, sequence_zone)
        self._restore_adjustment(data, controller, None, sequence, sequence_zone)
        self._check_is_on(data, controller, None, sequence, sequence_zone)

    def _restore_sequence(self, data: dict, controller: IUController) -> None:
        if (sequence := controller.get_sequence(data.get(CONF_INDEX))) is None:
            return
        self._restore_enabled(data, controller, None, sequence, None)
        self._restore_adjustment(data, controller, None, sequence, None)
        for sz_data in data.get(CONF_SEQUENCE_ZONES, []):
            self._restore_sequence_zone(sz_data, controller, sequence)
        self._check_is_on(data, controller, None, sequence, None)

    def _restore_zone(self, data: dict, controller: IUController) -> None:
        if (zone := controller.get_zone(data.get(CONF_INDEX))) is None:
            return
        self._restore_enabled(data, controller, zone, None, None)
        self._restore_adjustment(data, controller, zone, None, None)
        self._check_is_on(data, controller, zone, None, None)

    def _restore_controller(self, data: dict) -> None:
        if (controller := self._coordinator.get(data.get(CONF_INDEX))) is None:
            return
        self._restore_enabled(data, controller, None, None, None)
        for sq_data in data.get(CONF_SEQUENCES, []):
            self._restore_sequence(sq_data, controller)
        for z_data in data.get(CONF_ZONES, []):
            self._restore_zone(z_data, controller)
        self._check_is_on(data, controller, None, None, None)

    @property
    def is_on(self) -> str:
        """Return warnings about incomplete cycles"""
        for item in self._is_on:
            yield ",".join(
                IUBase.idl(
                    [
                        item["controller"],
                        item["zone"],
                        item["sequence"],
                        item["sequence_zone"],
                    ],
                    "-",
                )
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
            for item in IURestore(data, self._coordinator).is_on:
                self._coordinator.logger.log_incomplete_cycle(
                    item["controller"],
                    item["zone"],
                    item["sequence"],
                    item["sequence_zone"],
                )
            self._coordinator.restored_from_configuration = True
        # pylint: disable=broad-except
        except Exception as exc:
            self._coordinator.logger.log_invalid_restore_data(str(exc), json_data)
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
