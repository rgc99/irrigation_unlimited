"""HA entity classes"""

import json
from collections.abc import Iterator
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import ServiceCall, ServiceResponse
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt

from homeassistant.const import (
    CONF_STATE,
    CONF_UNTIL,
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
    ATTR_CONTROLLER_COUNT,
    ATTR_ENABLED,
    ATTR_NEXT_TICK,
    ATTR_TICK_LOG,
    ATTR_SUSPENDED,
    ATTR_ZONES,
    CONF_CONTROLLER,
    CONF_CONTROLLERS,
    CONF_ENABLED,
    CONF_INDEX,
    CONF_RESET,
    CONF_SEQUENCE,
    CONF_SEQUENCE_ID,
    CONF_SEQUENCE_ZONE,
    CONF_SEQUENCE_ZONES,
    CONF_SEQUENCES,
    CONF_ZONE,
    CONF_ZONES,
    COORDINATOR,
    ICON,
    SERVICE_ENABLE,
    SERVICE_DISABLE,
    SERVICE_TIME_ADJUST,
    SERVICE_SUSPEND,
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

    @property
    def is_on(self) -> list:
        """Return the list of objects left in on state"""
        return self._is_on

    def _add_to_on_list(
        self,
        controller: IUController,
        zone: IUZone = None,
        sequence: IUSequence = None,
        sequence_zone: IUSequenceZone = None,
    ) -> None:
        # pylint: disable=too-many-arguments
        if sequence_zone is None:
            if sequence is not None:
                for item in self._is_on:
                    if item[CONF_SEQUENCE] == sequence:
                        return
            elif zone is not None:
                for item in self._is_on:
                    if item[CONF_ZONE] == zone:
                        return
            elif controller is not None:
                for item in self._is_on:
                    if item[CONF_CONTROLLER] == controller:
                        return
        self._is_on.append(
            {
                CONF_CONTROLLER: controller,
                CONF_ZONE: zone,
                CONF_SEQUENCE: sequence,
                CONF_SEQUENCE_ZONE: sequence_zone,
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
            svd[CONF_SEQUENCE_ID] = [sequence.index + 1]
            if sequence_zone is not None:
                svd[CONF_ZONES] = [sequence_zone.index + 1]
        self._coordinator.service_call(svc, controller, zone, None, svd)

    def _restore_suspend(
        self,
        data: dict,
        controller: IUController,
        zone: IUZone,
        sequence: IUSequence,
        sequence_zone: IUSequenceZone,
    ) -> None:
        # pylint: disable=too-many-arguments
        if not ATTR_SUSPENDED in data:
            return
        svd = {}
        if data.get(ATTR_SUSPENDED) is not None:
            svd[CONF_UNTIL] = dt.parse_datetime(data.get(ATTR_SUSPENDED))
        else:
            svd[CONF_RESET] = None
        if sequence is not None:
            svd[CONF_SEQUENCE_ID] = [sequence.index + 1]
            if sequence_zone is not None:
                svd[CONF_ZONES] = [sequence_zone.index + 1]
        self._coordinator.service_call(SERVICE_SUSPEND, controller, zone, None, svd)

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
            svd[CONF_SEQUENCE_ID] = [sequence.index + 1]
            if sequence_zone is not None:
                svd[CONF_ZONES] = [sequence_zone.index + 1]
        self._coordinator.service_call(SERVICE_TIME_ADJUST, controller, zone, None, svd)

    def _restore_sequence_zone(
        self, data: dict, controller: IUController, sequence: IUSequence
    ) -> None:
        if (sequence_zone := sequence.get_zone(data.get(CONF_INDEX))) is None:
            return
        self._restore_enabled(data, controller, None, sequence, sequence_zone)
        self._restore_suspend(data, controller, None, sequence, sequence_zone)
        self._restore_adjustment(data, controller, None, sequence, sequence_zone)
        self._check_is_on(data, controller, None, sequence, sequence_zone)

    def _restore_sequence(self, data: dict, controller: IUController) -> None:
        if (sequence := controller.get_sequence(data.get(CONF_INDEX))) is None:
            return
        self._restore_enabled(data, controller, None, sequence, None)
        self._restore_suspend(data, controller, None, sequence, None)
        self._restore_adjustment(data, controller, None, sequence, None)
        for sz_data in data.get(CONF_SEQUENCE_ZONES, []):
            self._restore_sequence_zone(sz_data, controller, sequence)
        self._check_is_on(data, controller, None, sequence, None)

    def _restore_zone(self, data: dict, controller: IUController) -> None:
        if (zone := controller.get_zone(data.get(CONF_INDEX))) is None:
            return
        self._restore_enabled(data, controller, zone, None, None)
        self._restore_suspend(data, controller, zone, None, None)
        self._restore_adjustment(data, controller, zone, None, None)
        self._check_is_on(data, controller, zone, None, None)

    def _restore_controller(self, data: dict) -> None:
        if (controller := self._coordinator.get(data.get(CONF_INDEX))) is None:
            return
        self._restore_enabled(data, controller, None, None, None)
        self._restore_suspend(data, controller, None, None, None)
        for sq_data in data.get(CONF_SEQUENCES, []):
            self._restore_sequence(sq_data, controller)
        for z_data in data.get(CONF_ZONES, []):
            self._restore_zone(z_data, controller)
        self._check_is_on(data, controller, None, None, None)

    def report_is_on(self) -> Iterator[str]:
        """Generate a list of incomplete cycles"""
        for item in self._is_on:
            yield ",".join(
                IUBase.idl(
                    [
                        item[CONF_CONTROLLER],
                        item[CONF_ZONE],
                        item[CONF_SEQUENCE],
                        item[CONF_SEQUENCE_ZONE],
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
        sequence: IUSequence,
    ):
        """Base entity class"""
        self._coordinator = coordinator
        self._controller = controller
        self._zone = zone  # This will be None if it belongs to a Master/Controller
        self._sequence = sequence
        if self._sequence is not None:
            self.entity_id = self._sequence.entity_id
        elif self._zone is not None:
            self.entity_id = self._zone.entity_id
        else:
            self.entity_id = self._controller.entity_id

    def _call_iu(self, service: str, data: dict) -> ServiceResponse:
        return self._coordinator.service_call(
            service, self._controller, self._zone, self._sequence, data
        )

    async def _restore_entity(self) -> None:
        """Restore various attributes from last saved state"""

        def _append_zone(data: dict, zone: int) -> None:
            if zone is not None:
                data[CONF_ZONES] = [zone]

        def _restore_enabled(attr: dict, zone: int = None) -> None:
            svc = SERVICE_ENABLE if attr.get(ATTR_ENABLED, True) else SERVICE_DISABLE
            svd = {}
            _append_zone(svd, zone)
            self._call_iu(svc, svd)

        def _restore_suspend(attr: dict, zone: int = None) -> None:
            svd = {}
            if (adate := attr.get(ATTR_SUSPENDED)) is not None:
                svd[CONF_UNTIL] = adate
            else:
                svd[CONF_RESET] = None
            _append_zone(svd, zone)
            self._call_iu(SERVICE_SUSPEND, svd)

        def _restore_adjustment(attr: dict, zone: int = None) -> None:
            if (svd := IUAdjustment(attr.get(ATTR_ADJUSTMENT)).to_dict()) == {}:
                svd[CONF_RESET] = None
            _append_zone(svd, zone)
            self._call_iu(SERVICE_TIME_ADJUST, svd)

        def _check_is_on(state: str) -> None:
            if state == "on":
                self._coordinator.logger.log_incomplete_cycle(
                    self._controller, self._zone, self._sequence, None
                )

        if (state := await self.async_get_last_state()) is None:
            return

        _check_is_on(state.state)
        _restore_enabled(state.attributes)
        _restore_suspend(state.attributes)
        _restore_adjustment(state.attributes)
        if self._sequence is not None and state.attributes.get(ATTR_ZONES) is not None:
            for index, zone in enumerate(state.attributes[ATTR_ZONES]):
                _restore_enabled(zone, index + 1)
                _restore_suspend(zone, index + 1)
                _restore_adjustment(zone, index + 1)

    async def async_added_to_hass(self):
        if self._coordinator.restore_from_entity:
            try:
                await self._restore_entity()
            # pylint: disable=broad-except
            except Exception as exc:
                self._coordinator.logger.log_invalid_restore_data(repr(exc), None)

        self._coordinator.register_entity(
            self._controller, self._zone, self._sequence, self
        )
        return

    async def async_will_remove_from_hass(self):
        self._coordinator.deregister_entity(
            self._controller, self._zone, self._sequence, self
        )
        return

    def dispatch(self, service: str, call: ServiceCall) -> ServiceResponse:
        """Dispatcher for service calls"""
        return self._call_iu(service, call.data)


class IUComponent(RestoreEntity):
    """Representation of IrrigationUnlimitedCoordinator"""

    def __init__(self, coordinator: IUCoordinator):
        self._coordinator = coordinator
        self.entity_id = self._coordinator.entity_id

    async def async_added_to_hass(self):
        self._coordinator.register_entity(None, None, None, self)
        state = await self.async_get_last_state()
        if state is None or ATTR_CONFIGURATION not in state.attributes:
            return
        if not self._coordinator.restore_from_entity:
            json_data = state.attributes.get(ATTR_CONFIGURATION, {})
            try:
                data = json.loads(json_data)
                for item in IURestore(data, self._coordinator).is_on:
                    controller: IUController = item[CONF_CONTROLLER]
                    zone: IUZone = item[CONF_ZONE]
                    sequence: IUSequence = item[CONF_SEQUENCE]
                    sequence_zone: IUSequenceZone = item[CONF_SEQUENCE_ZONE]
                    self._coordinator.logger.log_incomplete_cycle(
                        controller,
                        zone,
                        sequence,
                        sequence_zone,
                    )
            # pylint: disable=broad-except
            except Exception as exc:
                self._coordinator.logger.log_invalid_restore_data(repr(exc), json_data)
        return

    async def async_will_remove_from_hass(self):
        self._coordinator.deregister_entity(None, None, None, self)
        return

    def dispatch(self, service: str, call: ServiceCall) -> None:
        """Service call dispatcher"""
        self._coordinator.service_call(service, None, None, None, call.data)

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
        attr[ATTR_CONTROLLER_COUNT] = len(self._coordinator.controllers)
        if self._coordinator.show_config:
            attr[ATTR_CONFIGURATION] = self._coordinator.configuration
        if self._coordinator.clock.show_log:
            next_tick = self._coordinator.clock.next_tick
            attr[ATTR_NEXT_TICK] = (
                dt.as_local(next_tick) if next_tick is not None else None
            )
            attr[ATTR_TICK_LOG] = list(
                dt.as_local(tick) for tick in self._coordinator.clock.tick_log
            )
        return attr
