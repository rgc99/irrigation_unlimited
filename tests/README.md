# Irrigation Unlimited tests

If new functionality is added to the integration it should accompany a test to ensure it works and hasn't broken or changed the behaviour of any other functionality. Don't change existing tests unless you are certain the test or result is wrong. This will make sure of backward compatibility. Uses [`pytest`](https://docs.pytest.org/en/latest/) for its tests, and the tests that have been included are modelled after tests that are written for core Home Assistant integrations.

Feel confident that if you change anything there will be some hundreds if not thousands of timing tests performed to ensure what was working, stays working. More tests are a good thing.

## Getting started

To begin, it is recommended to create a virtual environment to install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
```

You can then install the dependencies that will allow you to run tests:
`pip3 install -r requirements_test.txt.`

This will install `homeassistant`, `pytest`, and `pytest-homeassistant-custom-component`, a plugin which allows you to leverage helpers that are available in Home Assistant for core integration tests.

## Useful commands

Command | Description
------- | -----------
`pytest tests/` | This will run all tests in `tests/` and tell you how many passed/failed
`pytest --durations=10 --cov-report term-missing --cov=custom_components.irrigation_unlimited tests` | This tells `pytest` that your target module to test is `custom_components.irrigation_unlimited` so that it can give you a [code coverage](https://en.wikipedia.org/wiki/Code_coverage) summary, including % of code that was executed and the line numbers of missed executions.
`pytest tests/test_service.py -k test_service_adjust_time` | Runs the `test_service_adjust_time` test function located in `tests/test_service.py`

## Framework

To begin you will need some basic knowledge of python programming. Each test_*.py file usually contains multiple exams and each exam has multiple tests which are a set of events that must occur in order at a certain time.

### Internal testing

Irrigation Unlimited has an internal testing module. The tests are configured in the *.yaml file, see the main documentation on the [Testing Object](../README.md#testing-object). Each test details the order and time for the events that should occur. Support classes include IUEvent, IUTest and IUTester. The testing model uses a virtual clock to speed up (or slow down if you want) real time. Warning: Pushing this too far may lead to the 'skipping' of events where the hardware can't keep up. Note: Although the integration runs on a special (virtual) time, Home Assistant does not. This means other integrations like recorder will log state changes in real time.

### External testing

The iu_test_support.py module contains various routines for testing the integration and builds upon the internal tester. These routines have been put together in the IUExam class. IUExam is a simple to use external system framework for managing the internal testing regime. The integration is driven by pseudo clock ticks without delay. It avoids the skipping issue of the internal tester and allows 'full-speed' testing. Faster hardware will equal faster testing.

Please use [test_model.py](./test_model.py) as a template for any new tests. Here is an overview of the various class functions:

## IUExam class

This class wraps the individual support routines for convenience. The constructor takes a hass instance and the name of a configuration.yaml file.

### Initialising

Use the python `with` statement to start the exam because when it goes out of scope home assistant will be restored, see note below. Alternatively call the `restore` method when done.

```python
    async with IUExam(hass, "test_model.yaml") as exam:
```

Note: If the *.yaml file contains a `homeassistant:` section that modifies `unit_system`, `time_zone`, `latitude`, `longitude` or `elevation` then it must be restored to prevent side-effects on subsequent tests (sunrise/sunset times will be effected for example). Using the IUExam class as described will restore the home assistant settings.

### Properties

Name | Type | Default | Description
---- | ---- | ------- | -----------
config_directory | str | "tests/configs/" | Sets/gets the path to the config files.
coordinator | IUCoordinator | read-only | Returns the top level coordinator object.
track_interval | timedelta | read-only | Returns the system clock interval. The duration of a tick is the combination of the `granularity` and `refresh_interval` settings.
virtual_time | datetime | read-only | Returns the current 'virtual time' in the test.
config | ConfigType | read-only | The processed config file.

### Methods

#### begin_test(test_no)

Start a test. Resets the virtual clock to the `start` time defined for the test in the config file.

Parameter Name | Type | Description
---- | ---- | -----------
test_no | int | The test number to run (1's based).

#### finish_test()

Finish a test. Will complete advancing the virtual clock until the test `end` time defined in the config file is reached. Results of the test against events are then checked. Will raise error if results are not correct.

#### quiet_mode()

Sometimes it can be hard to see the forest for all the trees so eliminate some noise.

#### async_load_component(domain)

Load a component.

Parameter Name | Type | Description
---- | ---- | -----------
domain | str | The name of the domain to load for example 'homeassistant'.

#### run_test(test_no)

Run a single test and check the results.

Parameter Name | Type | Description
---- | ---- | -----------
test_no | int | The test number to run (1's based).

#### run_all()

Run all tests in the config and check the results.

#### run_until(stop_at)

Run to a point in time.

Parameter Name | Type | Description
---- | ---- | -----------
stop_at | datetime | The virtual time.

#### run_for(duration)

Run for a period of time.

Parameter Name | Type | Description
---- | ---- | -----------
duration | timedelta | The virtual duration.

#### run_for_1_tick()

Run for one tick. This method will advance the current test for one clock tick. Required after a service call before checking the entity. Also useful to single step through the test.

#### check_summary()

This will check all tests have been run, the events tally with the results and there were no errors in any tests.

#### no_check()

Use this option to prevent results being checked and reported. When used with the `output_events` parameter in the `testing:` section of the yaml it will output event information that can be copied as result data. Great to obtain results that you know are correct - it's the teachers edition.

#### setup()

Setup the hass environment. Load config file, setup core config and components. Call automatically when used with the python `with` statement.

#### restore()

Restore the hass environment. If the `homeassistant:` section has been changed in the configuration then call this method to restore defaults. Called automatically when used with the python `with` statement.

### Examples

Here are some basic examples of using the framework. See [test_model.py](./test_model.py) for all the imports etc.

This is a basic three-liner to run all the tests in the config file and check the results.

```python
    async with IUExam(hass, "test_model.yaml") as exam:
        await exam.run_all()
        exam.check_summary()
```

Here we run a single test, maybe do something in between, finish the test and check the summary.

```python
    async with IUExam(hass, "test_model.yaml") as exam:
        await exam.begin_test(1)
        # Test has started, chance to do something like check state of entity, make
        # a service call, have a peek at something etc.

        # print(json.dumps(exam.coordinator.as_dict(), default=str))

        # state = hass.states.get("binary_sensor.irrigation_unlimited_c1_m")
        # assert state.state == STATE_OFF

        await exam.finish_test()
        exam.check_summary()
```

Run a test with a service call.

```python
    async with IUExam(hass, "test_model.yaml") as exam:
        await exam.begin_test(1)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
                "zones": 0,
                "actual": "00:10",
            },
            True,
        )
        await exam.finish_test()
        exam.check_summary()
```

Start and stop the test, run to certain points in time. This will give an opportunity to examine entities and other hass information along the way.

```python
    async with IUExam(hass, "test_model.yaml") as exam:

        # Test starts at 05:00
        await exam.begin_test(1)

        # Run until 5:30 am
        await exam.run_until(datetime.fromisoformat("2021-01-04 05:30:00+00:00"))

        # Run for another 30 minutes
        await exam.run_for(timedelta(minutes=30))

        # Run for one more clock tick
        await exam.run_for_1_tick()

        # Test ends at 07:00
        await exam.finish_test()

        # Check all tests completed
        exam.check_summary()
```

Finally, for whatever reason, here is doing it the hard way. Does not use the python `with` statement.

```python
    exam = IUExam(hass, "test_model.yaml")
    try
      await exam.setup()
      await exam.begin_test(1)
      await exam.finish_test()
      exam.check_summary()
    finally
      await exam.restore()
```
