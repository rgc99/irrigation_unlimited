"""Test irrigation_unlimited history."""
from unittest.mock import patch
import pytest
import homeassistant.core as ha

from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    EVENT_INCOMPLETE,
)
from custom_components.irrigation_unlimited.entity import IURestore
from tests.iu_test_support import IUExam, mk_utc

IUExam.quiet_mode()


@pytest.fixture(name="mock_state_z1_none")
def mock_state_z1_none():
    """Patch HA with no entity history"""
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        mock.return_value = None
        yield


@pytest.fixture(name="mock_state_z1_enabled")
def mock_state_z1_enabled():
    """Patch HA history with entity in enabled state"""
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        idx = "binary_sensor.irrigation_unlimited_c1_z1"
        mock.return_value = ha.State(
            idx,
            "on",
            {"enabled": True},
            mk_utc("2021-01-04 04:30:00"),
        )
        yield


@pytest.fixture(name="mock_state_z1_disabled")
def mock_state_z1_disabled():
    """Patch HA history with entity in disabled state"""
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        idx = "binary_sensor.irrigation_unlimited_c1_z1"
        mock.return_value = ha.State(
            idx,
            "on",
            {"enabled": False},
            mk_utc("2021-01-04 04:30:00"),
        )
        yield


@pytest.fixture(name="mock_state_coordinator")
def mock_state_coordinator():
    """Patch HA history"""
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        # pylint: disable=line-too-long
        dct = {
            "configuration": '{"controllers": [{"index": 0, "name": "Fundos", "state": "off", "enabled": true, "icon": "mdi:water-off", "status": "off", "zones": [{"index": 0, "name": "Gramado", "state": "off", "enabled": true, "icon": "mdi:valve-closed", "zone_id": "1", "status": "off", "adjustment": "%50.0", "current_duration": "", "schedules": []}, {"index": 1, "name": "Lateral", "state": "off", "enabled": true, "icon": "mdi:valve-closed", "zone_id": "2", "status": "off", "adjustment": "", "current_duration": "", "schedules": []}, {"index": 2, "name": "Corredor", "state": "off", "enabled": true, "icon": "mdi:valve-closed", "zone_id": "3", "status": "off", "adjustment": "", "current_duration": "", "schedules": []}, {"index": 3, "name": "Horta", "state": "off", "enabled": false, "icon": "mdi:circle-off-outline", "zone_id": "4", "status": "disabled", "adjustment": "", "current_duration": "", "schedules": []}], "sequences": [{"index": 0, "name": "Multi zone", "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "default_duration": "600", "default_delay": "20", "duration_factor": 0.24848484848484848, "total_delay": "40", "total_duration": "1650", "adjusted_duration": "410", "current_duration": "", "adjustment": "%25.0", "sequence_zones": [{"index": 0, "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "delay": "20", "base_duration": "600", "adjusted_duration": "450", "final_duration": "110", "zones": [1], "current_duration": "", "adjustment": "%75.0"}, {"index": 1, "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "delay": "20", "base_duration": "600", "adjusted_duration": "600", "final_duration": "150", "zones": [2], "current_duration": "", "adjustment": ""}, {"index": 2, "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "delay": "20", "base_duration": "600", "adjusted_duration": "600", "final_duration": "150", "zones": [3], "current_duration": "", "adjustment": ""}]}, {"index": 1, "name": "Outer zone", "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "default_duration": "900", "default_delay": "10", "duration_factor": 1.0, "total_delay": "10", "total_duration": "1800", "adjusted_duration": "1800", "current_duration": "", "adjustment": "", "sequence_zones": [{"index": 0, "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "delay": "10", "base_duration": "900", "adjusted_duration": "900", "final_duration": "900", "zones": [1], "current_duration": "", "adjustment": ""}, {"index": 1, "state": "off", "enabled": false, "icon": "mdi:circle-off-outline", "status": "disabled", "delay": "", "base_duration": "", "adjusted_duration": "", "final_duration": "", "zones": [2], "current_duration": "", "adjustment": ""}, {"index": 2, "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "delay": "10", "base_duration": "900", "adjusted_duration": "900", "final_duration": "900", "zones": [3,4], "current_duration": "", "adjustment": ""}]}, {"index": 2, "name": "Later zone", "state": "off", "enabled": false, "icon": "mdi:circle-off-outline", "status": "disabled", "default_duration": "720", "default_delay": "10", "duration_factor": 1.0, "total_delay": "", "total_duration": "", "adjusted_duration": "", "current_duration": "", "adjustment": "", "sequence_zones": [{"index": 0, "state": "off", "enabled": true, "icon": "mdi:alert-octagon-outline", "status": "blocked", "delay": "", "base_duration": "", "adjusted_duration": "", "final_duration": "", "zones": [3], "current_duration": "", "adjustment": ""}, {"index": 1, "state": "off", "enabled": true, "icon": "mdi:alert-octagon-outline", "status": "blocked", "delay": "", "base_duration": "", "adjusted_duration": "", "final_duration": "", "zones": [2], "current_duration": "", "adjustment": ""}, {"index": 2, "state": "off", "enabled": true, "icon": "mdi:alert-octagon-outline", "status": "blocked", "delay": "", "base_duration": "", "adjusted_duration": "", "final_duration": "", "zones": [1], "current_duration": "", "adjustment": ""}]}]}]}'
        }
        mock.return_value = ha.State(
            "irrigation_unlimited.coordinator",
            "ok",
            dct,
            mk_utc("2021-01-04 04:30:00"),
        )
        yield


@pytest.fixture(name="mock_state_coordinator_is_on")
def mock_state_coordinator_is_on():
    """Patch HA history"""
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state"
    ) as mock:
        # pylint: disable=line-too-long
        dct = {
            "configuration": '{"version": "1.0.0", "controllers": [{"index": 0, "name": "My Garden", "state": "on", "enabled": true, "icon": "mdi:water", "status": "on", "zones": [{"index": 0, "name": "Front Lawn", "state": "on", "enabled": true, "icon": "mdi:valve-open", "zone_id": "1", "status": "on", "adjustment": "", "current_duration": "90", "schedules": []}, {"index": 1, "name": "Vege Patch", "state": "off", "enabled": true, "icon": "mdi:valve-closed", "zone_id": "2", "status": "off", "adjustment": "", "current_duration": "", "schedules": []}, {"index": 2, "name": "Roses", "state": "off", "enabled": true, "icon": "mdi:valve-closed", "zone_id": "3", "status": "off", "adjustment": "", "current_duration": "", "schedules": []}, {"index": 3, "name": "Back Yard", "state": "off", "enabled": true, "icon": "mdi:valve-closed", "zone_id": "4", "status": "off", "adjustment": "", "current_duration": "", "schedules": []}], "sequences": [{"index": 0, "name": "Main run", "state": "on", "enabled": true, "icon": "mdi:play-circle-outline", "status": "on", "default_duration": "600", "default_delay": "20", "duration_factor": 1.0, "total_delay": "40", "total_duration": "1800", "adjusted_duration": "1800", "current_duration": "300", "adjustment": "", "sequence_zones": [{"index": 0, "state": "on", "enabled": true, "icon": "mdi:play-circle-outline", "status": "on", "delay": "20", "base_duration": "600", "adjusted_duration": "600", "final_duration": "600", "zones": [1], "current_duration": "90", "adjustment": ""}, {"index": 1, "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "delay": "20", "base_duration": "600", "adjusted_duration": "600", "final_duration": "600", "zones": [2], "current_duration": "", "adjustment": ""}, {"index": 2, "state": "off", "enabled": true, "icon": "mdi:stop-circle-outline", "status": "off", "delay": "20", "base_duration": "600", "adjusted_duration": "600", "final_duration": "600", "zones": [3], "current_duration": "", "adjustment": ""}]}]}]}'
        }
        mock.return_value = ha.State(
            "irrigation_unlimited.coordinator",
            "ok",
            dct,
            mk_utc("2021-01-04 04:30:00"),
        )
        yield


# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
async def test_restore_none(
    hass: ha.HomeAssistant, skip_dependencies, skip_history, mock_state_z1_none
):
    """Test restoring entity with no history"""

    async with IUExam(hass, "test_restore_entity.yaml"):
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["enabled"] is True


async def test_restore_enabled(
    hass: ha.HomeAssistant, skip_dependencies, skip_history, mock_state_z1_enabled
):
    """Test restoring entity in enabled state"""

    async with IUExam(hass, "test_restore_entity.yaml"):
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["enabled"] is True


async def test_restore_disabled(
    hass: ha.HomeAssistant, skip_dependencies, skip_history, mock_state_z1_disabled
):
    """Test restoring entity in disabled state"""

    async with IUExam(hass, "test_restore_entity.yaml"):
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1")
        assert sta.attributes["enabled"] is False


async def test_restore_coordinator(
    hass: ha.HomeAssistant, skip_dependencies, skip_history, mock_state_coordinator
):
    """Test restoring coordinator"""

    async with IUExam(hass, "test_restore_entity_sequence.yaml") as exam:
        assert str(exam.coordinator.controllers[0].zones[0].adjustment) == "%50.0"
        assert str(exam.coordinator.controllers[0].sequences[0].adjustment) == "%25.0"
        assert (
            str(exam.coordinator.controllers[0].sequences[0].zones[0].adjustment)
            == "%75.0"
        )

        assert exam.coordinator.controllers[0].zones[3].enabled is False
        sta = hass.states.get("binary_sensor.irrigation_unlimited_c1_z4")
        assert sta.attributes["enabled"] is False

        assert exam.coordinator.controllers[0].sequences[2].enabled is False
        assert (
            exam.coordinator.controllers[0].sequences[2].status(False, False)
            == "disabled"
        )
        assert (
            exam.coordinator.controllers[0].sequences[2].zones[0].status() == "blocked"
        )
        assert (
            exam.coordinator.controllers[0].sequences[2].zones[1].status() == "blocked"
        )
        assert (
            exam.coordinator.controllers[0].sequences[2].zones[2].status() == "blocked"
        )

        assert exam.coordinator.controllers[0].sequences[1].zones[1].enabled is False
        assert (
            exam.coordinator.controllers[0].sequences[1].zones[1].status() == "disabled"
        )

        IURestore(None, exam.coordinator)
        IURestore({}, exam.coordinator)

        # Missing fields. Check passes and nothing changes
        data = {
            "controllers": [
                {
                    "index": 0,
                    "zones": [
                        {},
                    ],
                    "sequences": [
                        {
                            "sequence_zones": [
                                {},
                            ],
                        },
                    ],
                }
            ]
        }
        IURestore(data, exam.coordinator)
        assert exam.coordinator.controllers[0].enabled is True
        assert exam.coordinator.controllers[0].zones[0].enabled is True
        assert exam.coordinator.controllers[0].sequences[0].enabled is True
        assert exam.coordinator.controllers[0].sequences[0].zones[0].enabled is True
        assert str(exam.coordinator.controllers[0].zones[0].adjustment) == "%50.0"
        assert str(exam.coordinator.controllers[0].sequences[0].adjustment) == "%25.0"
        assert (
            str(exam.coordinator.controllers[0].sequences[0].zones[0].adjustment)
            == "%75.0"
        )

        # Bad data
        data = {
            "controllers": [
                {
                    "index": 0,
                    "zones": [
                        {},
                    ],
                    "sequences": [
                        {
                            "index": 0,
                            "state": "on",
                            "enabled": True,
                            "sequence_zones": [
                                {
                                    "index": 0,
                                    "state": "xxx",
                                    "zones": "dummy",
                                },
                                {
                                    "index": 999,
                                    "state": "on",
                                    "zones": "dummy",
                                },
                            ],
                        },
                    ],
                }
            ]
        }
        IURestore(data, exam.coordinator)

        # Disable all and clear adjustments
        data = {
            "controllers": [
                {
                    "index": 0,
                    "state": "off",
                    "enabled": False,
                    "zones": [
                        {
                            "index": 0,
                            "state": "off",
                            "enabled": False,
                            "adjustment": "",
                        },
                    ],
                    "sequences": [
                        {
                            "index": 0,
                            "state": "off",
                            "enabled": False,
                            "adjustment": "",
                            "sequence_zones": [
                                {
                                    "index": 0,
                                    "state": "off",
                                    "enabled": False,
                                    "adjustment": "",
                                },
                            ],
                        },
                    ],
                }
            ]
        }
        IURestore(data, exam.coordinator)
        assert exam.coordinator.controllers[0].enabled is False
        assert exam.coordinator.controllers[0].zones[0].enabled is False
        assert exam.coordinator.controllers[0].sequences[0].enabled is False
        assert exam.coordinator.controllers[0].sequences[0].zones[0].enabled is False
        assert str(exam.coordinator.controllers[0].zones[0].adjustment) == ""
        assert str(exam.coordinator.controllers[0].sequences[0].adjustment) == ""
        assert (
            str(exam.coordinator.controllers[0].sequences[0].zones[0].adjustment) == ""
        )

        # Enable all and leave in on state
        data = {
            "controllers": [
                {
                    "index": 0,
                    "state": "on",
                    "enabled": True,
                    "zones": [
                        {
                            "index": 0,
                            "state": "off",
                            "enabled": True,
                            "adjustment": "",
                        },
                        {
                            "index": 1,
                            "state": "off",
                            "enabled": True,
                            "adjustment": "",
                        },
                        {
                            "index": 2,
                            "state": "on",
                            "enabled": True,
                            "adjustment": "",
                        },
                        {
                            "index": 3,
                            "state": "on",
                            "enabled": True,
                            "adjustment": "",
                        },
                    ],
                    "sequences": [
                        {
                            "index": 0,
                            "state": "on",
                            "enabled": True,
                            "adjustment": "",
                            "sequence_zones": [
                                {
                                    "index": 0,
                                    "state": "off",
                                    "enabled": True,
                                    "adjustment": "",
                                    "zones": [1],
                                },
                            ],
                        },
                        {
                            "index": 1,
                            "state": "on",
                            "enabled": True,
                            "adjustment": "",
                            "sequence_zones": [
                                {
                                    "index": 0,
                                    "state": "off",
                                    "enabled": True,
                                    "adjustment": "",
                                    "zones": [1],
                                },
                                {
                                    "index": 1,
                                    "state": "off",
                                    "enabled": True,
                                    "adjustment": "",
                                    "zones": [2],
                                },
                                {
                                    "index": 2,
                                    "state": "on",
                                    "enabled": True,
                                    "adjustment": "",
                                    "zones": [3, 4],
                                },
                            ],
                        },
                        {
                            "index": 2,
                            "state": "on",
                            "enabled": True,
                            "adjustment": "",
                            "sequence_zones": [
                                {
                                    "index": 0,
                                    "state": "off",
                                    "enabled": True,
                                    "adjustment": "",
                                    "zones": [1],
                                },
                                {
                                    "index": 1,
                                    "state": "off",
                                    "enabled": True,
                                    "adjustment": "",
                                    "zones": [2],
                                },
                                {
                                    "index": 2,
                                    "state": "on",
                                    "enabled": True,
                                    "adjustment": "",
                                    "zones": "3,4",
                                },
                            ],
                        },
                    ],
                }
            ]
        }
        assert list(IURestore(data, exam.coordinator).report_is_on()) == [
            "0,-,0,-",
            "0,2,1,2",
            "0,3,1,2",
            "0,2,2,2",
            "0,3,2,2",
        ]


async def test_restore_coordinator_events(
    hass: ha.HomeAssistant,
    skip_dependencies,
    skip_history,
    mock_state_coordinator_is_on,
):
    """Test restoring coordinator in on state"""

    event_data = []

    def handle_event(event: ha.Event):
        nonlocal event_data
        event_data.append(event.data)

    hass.bus.async_listen(f"{DOMAIN}_{EVENT_INCOMPLETE}", handle_event)

    async with IUExam(hass, "test_restore_entity_sequence.yaml"):

        # This is work in progress. No event is currently fired.
        assert not event_data
