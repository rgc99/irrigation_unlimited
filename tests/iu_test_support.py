from custom_components.irrigation_unlimited.irrigation_unlimited import (
    IUCoordinator,
)

test_config_dir = "tests/configs/"

def check_summary(full_path: str, coordinator: IUCoordinator):
    assert (
        coordinator.tester.total_events
        == coordinator.tester.total_checks
        == coordinator.tester.total_results
    )
    assert coordinator.tester.total_errors == 0
    print(
        "Finished: {0}; tests: {1}; events: {2}; checks: {3}; errors: {4}; time: {5:.2f}s".format(
            full_path,
            coordinator.tester.total_tests,
            coordinator.tester.total_events,
            coordinator.tester.total_checks,
            coordinator.tester.total_errors,
            coordinator.tester.total_time,
        )
    )
    return


