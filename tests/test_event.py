"""Test irrigation_unlimited events."""
import homeassistant.core as ha
from homeassistant.config import (
    load_yaml_config_file,
    async_process_ha_core_config,
)
from homeassistant.setup import async_setup_component

from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
)
from custom_components.irrigation_unlimited.const import (
    DOMAIN,
    COORDINATOR,
    EVENT_FINISH,
    EVENT_START,
)
from custom_components.irrigation_unlimited.__init__ import CONFIG_SCHEMA
from tests.iu_test_support import (
    begin_test,
    check_summary,
    finish_test,
    quiet_mode,
    TEST_CONFIG_DIR,
)

quiet_mode()


async def test_events(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test loading of a config."""
    # pylint: disable=unused-argument

    event_data = []

    def handle_event(event: ha.Event):
        nonlocal event_data
        event_data.append(event.data)

    hass.bus.async_listen(f"{DOMAIN}_{EVENT_START}", handle_event)
    hass.bus.async_listen(f"{DOMAIN}_{EVENT_FINISH}", handle_event)

    full_path = TEST_CONFIG_DIR + "test_event.yaml"
    config = CONFIG_SCHEMA(load_yaml_config_file(full_path))
    if ha.DOMAIN in config:
        await async_process_ha_core_config(hass, config[ha.DOMAIN])
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    coordinator: IUCoordinator = hass.data[DOMAIN][COORDINATOR]

    # Run all tests
    for test in range(coordinator.tester.total_tests):
        start_time = await begin_test(test + 1, coordinator)
        await finish_test(hass, coordinator, start_time, True)

    check_summary(full_path, coordinator)

    assert event_data == [
        {
            "controller": {"index": 0, "name": "Test controller 1"},
            "sequence": {"index": 0, "name": "Seq 1"},
            "run": {"duration": 2280},
            "schedule": {"index": 0, "name": "Schedule 1"},
        },
        {
            "controller": {"index": 0, "name": "Test controller 1"},
            "sequence": {"index": 0, "name": "Seq 1"},
            "run": {"duration": 2280},
            "schedule": {"index": 0, "name": "Schedule 1"},
        },
        {
            "controller": {"index": 0, "name": "Test controller 1"},
            "sequence": {"index": 1, "name": "Seq 2"},
            "run": {"duration": 2280},
            "schedule": {"index": 0, "name": "Schedule 1"},
        },
        {
            "controller": {"index": 0, "name": "Test controller 1"},
            "sequence": {"index": 1, "name": "Seq 2"},
            "run": {"duration": 2280},
            "schedule": {"index": 0, "name": "Schedule 1"},
        },
    ]
