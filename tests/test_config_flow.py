"""irrigation_unlimited config flow test"""

# pylint: disable=unused-import
from datetime import date, timedelta

import homeassistant.core as ha
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_AFTER,
    CONF_BEFORE,
    CONF_DELAY,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_REPEAT,
    CONF_UNTIL,
    CONF_WEEKDAY,
)
from homeassistant.data_entry_flow import FlowResultType

from custom_components.irrigation_unlimited.const import (
    CONF_CONTROLLERS,
    CONF_DAY,
    CONF_DURATION,
    CONF_EVERY_N_DAYS,
    CONF_FROM,
    CONF_MAXIMUM,
    CONF_MINIMUM,
    CONF_MONTH,
    CONF_SCHEDULES,
    CONF_SEQUENCES,
    CONF_START_N_DAYS,
    CONF_SUN,
    CONF_THRESHOLD,
    CONF_TIME,
    CONF_ZONES,
    CONF_ZONE_ID,
    COORDINATOR,
    DOMAIN,
    SERVICE_EXPORT_CONFIG,
    SERVICE_ENABLE,
    SERVICE_DISABLE,
)
from tests.iu_test_support import IUExam, mk_utc, mk_local

IUExam.quiet_mode()


async def _run_config_flow(hass: ha.HomeAssistant, zones: list[str]):
    """Drive IUConfigFlow end to end and return the created entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_NAME: "Test Controller"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "add_zone"

    for zone in zones:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_NAME: zone}
        )
        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "zone_menu"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"next_step_id": "add_zone" if zone != zones[-1] else "finish"},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    return result


async def test_config_flow_sets_up_integration(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """A controller created purely through the UI sets up and produces entities."""
    # pylint: disable=unused-argument

    result = await _run_config_flow(hass, ["Zone 1", "Zone 2"])

    assert result["title"] == "Test Controller"
    assert result["data"] == {
        CONF_CONTROLLERS: [
            {
                CONF_NAME: "Test Controller",
                CONF_ZONES: [{CONF_NAME: "Zone 1"}, {CONF_NAME: "Zone 2"}],
            }
        ]
    }

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    await hass.async_block_till_done()

    # No yaml block was used, so the integration must have come up from the entry alone
    assert entry.state.name == "LOADED"
    coordinator = hass.data[DOMAIN][COORDINATOR]
    assert len(coordinator.controllers) == 1
    assert [zone.name for zone in coordinator.controllers[0].zones] == [
        "Zone 1",
        "Zone 2",
    ]
    assert hass.states.get("binary_sensor.irrigation_unlimited_c1_m") is not None
    assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z1") is not None
    assert hass.states.get("binary_sensor.irrigation_unlimited_c1_z2") is not None


async def test_options_flow_adds_sequence_and_schedule(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Zones, sequences and schedules can be edited through the options flow."""
    # pylint: disable=unused-argument

    result = await _run_config_flow(hass, ["Zone 1", "Zone 2"])
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.entry_id == result["result"].entry_id

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "init"

    # Add a sequence covering both zones
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "add_sequence"}
    )
    assert result["step_id"] == "add_sequence"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_NAME: "Sequence 1", "delay": "00:01", "duration": "00:10"},
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "sequence_menu"

    for zone_id in ("1", "2"):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "add_sequence_zone"}
        )
        assert result["step_id"] == "add_sequence_zone"
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"zone_id": zone_id}
        )
        assert result["step_id"] == "sequence_menu"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "finish_sequence"}
    )
    assert result["step_id"] == "init"

    # Schedule zone 1 at 06:00 for 20 minutes
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "add_schedule"}
    )
    assert result["step_id"] == "add_schedule"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"target_ref": "zone:0"}
    )
    assert result["step_id"] == "add_schedule_details"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Morning",
            "time": "06:00",
            "duration": "00:20:00",
            "start_n_days": "",
            "weekday": [],
        },
    )
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "finish"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    assert entry.options[CONF_CONTROLLERS] == [
        {
            CONF_NAME: "Test Controller",
            CONF_ZONES: [
                {
                    CONF_NAME: "Zone 1",
                    CONF_SCHEDULES: [
                        {
                            CONF_NAME: "Morning",
                            CONF_TIME: "06:00",
                            CONF_DURATION: "00:20:00",
                        }
                    ],
                },
                {CONF_NAME: "Zone 2"},
            ],
            CONF_SEQUENCES: [
                {
                    CONF_NAME: "Sequence 1",
                    CONF_DELAY: "00:01",
                    CONF_DURATION: "00:10",
                    CONF_ZONES: [{CONF_ZONE_ID: ["1"]}, {CONF_ZONE_ID: ["2"]}],
                }
            ],
        }
    ]
    # The schedule was applied to the in-memory copy of zone 1
    coordinator = hass.data[DOMAIN][COORDINATOR]
    zone = coordinator.controllers[0].zones[0]
    assert zone.schedules[0].name == "Morning"


async def test_sun_event_schedule(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """A schedule can be triggered by a sun event with before/after offsets."""
    # pylint: disable=unused-argument

    result = await _run_config_flow(hass, ["Zone 1"])
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "add_schedule"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"target_ref": "zone:0"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "At dawn",
            CONF_TIME: "06:00",
            CONF_DURATION: "00:20:00",
            CONF_SUN: "sunrise",
            CONF_BEFORE: "00:20",
            CONF_START_N_DAYS: "",
            CONF_WEEKDAY: [],
            "day_type": "",
            "day_numbers": "",
            CONF_FROM: "",
            CONF_UNTIL: "",
        },
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "finish"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    zone = hass.data[DOMAIN][COORDINATOR].controllers[0].zones[0]
    schedule = zone.schedules[0]

    # The stored form is plain JSON: the sun dict with a duration *string*
    assert entry.options[CONF_CONTROLLERS][0][CONF_ZONES][0][CONF_SCHEDULES][0] == {
        CONF_NAME: "At dawn",
        CONF_TIME: {CONF_SUN: "sunrise", CONF_BEFORE: "00:20:00"},
        CONF_DURATION: "00:20:00",
    }
    # The coordinator coerced the string offsets back into timedeltas
    assert schedule.start_time == {
        CONF_SUN: "sunrise",
        CONF_BEFORE: timedelta(minutes=20),
    }


async def test_month_day_and_season_span(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Months, days of the month and a from/until span all survive the UI round trip."""
    # pylint: disable=unused-argument

    await _run_config_flow(hass, ["Zone 1"])
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "add_schedule"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"target_ref": "zone:0"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Summer",
            CONF_TIME: "06:00",
            CONF_DURATION: "00:20:00",
            CONF_START_N_DAYS: "",
            CONF_MONTH: ["jun", "jul", "aug"],
            "day_type": "specific",
            "day_numbers": "1, 15, 31",
            CONF_FROM: "2026-06-01",
            CONF_UNTIL: "2026-08-31",
        },
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "finish"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    stored = entry.options[CONF_CONTROLLERS][0][CONF_ZONES][0][CONF_SCHEDULES][0]
    assert stored[CONF_MONTH] == ["jun", "jul", "aug"]
    assert stored[CONF_DAY] == [1, 15, 31]
    assert stored[CONF_FROM] == "2026-06-01"
    assert stored[CONF_UNTIL] == "2026-08-31"

    schedule = hass.data[DOMAIN][COORDINATOR].controllers[0].zones[0].schedules[0]
    # _from/_until have no public accessor; read them off the schedule
    assert schedule._from == date(2026, 6, 1)
    assert schedule._until == date(2026, 8, 31)
    # Months are translated to their numeric form internally
    assert schedule.months == [6, 7, 8]


async def test_zone_limits_and_multiple_entities(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Zone min/max/threshold and multiple switch entities are editable in the UI."""
    # pylint: disable=unused-argument

    await _run_config_flow(hass, ["Zone 1"])
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "edit_zone"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"zone_index": "0"}
    )
    assert result["step_id"] == "edit_zone_details"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Zone 1",
            CONF_ENTITY_ID: ["switch.valve_a", "switch.valve_b"],
            CONF_MINIMUM: "00:05",
            CONF_MAXIMUM: "00:45",
            CONF_THRESHOLD: "00:10",
        },
    )
    assert result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "finish"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    zone_cfg = entry.options[CONF_CONTROLLERS][0][CONF_ZONES][0]
    assert zone_cfg[CONF_ENTITY_ID] == ["switch.valve_a", "switch.valve_b"]
    assert zone_cfg[CONF_MINIMUM] == "00:05"

    zone = hass.data[DOMAIN][COORDINATOR].controllers[0].zones[0]
    # No public accessor for the run-time caps; read the run queue directly
    assert zone.runs._minimum == timedelta(minutes=5)
    assert zone.runs._maximum == timedelta(minutes=45)
    assert zone.runs._threshold == timedelta(minutes=10)


async def test_sequence_step_overrides(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """A sequence step can carry its own duration, delay and repeat count."""
    # pylint: disable=unused-argument

    await _run_config_flow(hass, ["Zone 1", "Zone 2"])
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "add_sequence"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_NAME: "Seq", CONF_DELAY: "00:01", CONF_DURATION: "00:10"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "add_sequence_zone"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ZONE_ID: "1",
            CONF_DURATION: "00:06",
            CONF_DELAY: "00:02",
            CONF_REPEAT: 3,
        },
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "finish_sequence"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "finish"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    step = entry.options[CONF_CONTROLLERS][0][CONF_SEQUENCES][0][CONF_ZONES][0]
    assert step == {
        CONF_ZONE_ID: ["1"],
        CONF_DURATION: "00:06",
        CONF_DELAY: "00:02",
        CONF_REPEAT: 3,
    }

    seq_zone = hass.data[DOMAIN][COORDINATOR].controllers[0].sequences[0].zones[0]
    assert seq_zone.duration == timedelta(minutes=6)
    assert seq_zone.delay == timedelta(minutes=2)
    assert seq_zone.repeat == 3


async def test_config_flow_is_registered(hass: ha.HomeAssistant, skip_dependencies):
    """The domain must advertise a UI config flow, not be yaml-only."""
    # pylint: disable=unused-argument

    from homeassistant.loader import async_get_integration

    integration = await async_get_integration(hass, DOMAIN)
    assert integration.config_flow is True
    assert hass.config_entries.flow.async_progress_by_handler(DOMAIN) == []


async def test_export_config(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test export_config action"""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_export_config.yaml") as exam:

        await exam.begin_test(1)
        data = await exam.call(
            SERVICE_EXPORT_CONFIG,
            None,
            True,
        )
        assert data == {
            "controllers": [
                {
                    "name": "Test controller 1",
                    "zones": [
                        {"name": "Zone 1", "zone_id": "1"},
                        {"name": "Zone 2", "zone_id": "2"},
                    ],
                    "sequences": [
                        {
                            "name": "Sequence 1",
                            "delay": "0:01:00",
                            "zones": [
                                {"zone_id": "1", "duration": "0:06:00"},
                                {"zone_id": "2", "duration": "0:12:00"},
                            ],
                            "schedules": [
                                {
                                    "name": "Schedule 1",
                                    "time": "{'sun': 'sunrise', 'before': datetime.timedelta(seconds=2)}",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        await exam.finish_test()
        exam.check_summary()


async def test_helpers(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test helpers"""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_helper.yaml") as exam:

        await exam.begin_test(1)

        # Initial state should be on
        assert (
            hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes[
                "enabled"
            ]
            is True
        )
        assert hass.states.get("switch.zone_1_enabled").state == "on"

        # Disable zone 1
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        assert (
            hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes[
                "enabled"
            ]
            is False
        )
        # assert hass.states.get("switch.zone_1_enabled").state == "off"

        # Reenable zone 1
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        assert (
            hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes[
                "enabled"
            ]
            is True
        )
        assert hass.states.get("switch.zone_1_enabled").state == "on"

        # Disable zone 1 via helper
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": "switch.zone_1_enabled"}, True
        )
        await hass.async_block_till_done()
        assert hass.states.get("switch.zone_1_enabled").state == "off"
        assert (
            hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes[
                "enabled"
            ]
            is False
        )

        # Enable zone 1
        await exam.call(
            SERVICE_ENABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        assert (
            hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes[
                "enabled"
            ]
            is True
        )
        # assert hass.states.get("switch.zone_1_enabled").state == "on"

        # Disable zone 1
        await exam.call(
            SERVICE_DISABLE,
            {"entity_id": "binary_sensor.irrigation_unlimited_c1_z1"},
        )
        assert (
            hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes[
                "enabled"
            ]
            is False
        )
        assert hass.states.get("switch.zone_1_enabled").state == "off"

        # Enable zone 1 via helper
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": "switch.zone_1_enabled"}, True
        )
        await hass.async_block_till_done()
        assert hass.states.get("switch.zone_1_enabled").state == "on"
        assert (
            hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes[
                "enabled"
            ]
            is True
        )

        await exam.finish_test()
        exam.check_summary()
