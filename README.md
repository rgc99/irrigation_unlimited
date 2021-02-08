# Irrigation Unlimited

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Community Forum][forum-shield]][forum]

This integration is for irrigation systems large and small. It can offer some complex arrangements without large and messy scripts. This integration will complement many other irrigation projects.

Home Assistant makes automating switches easy with the built in tools available. So why this project? You have a system in place but now you have extended it to have a number of zones. You don't want all the zones on at once because of water pressure issues. Maybe you would like each zone to have a number of schedules say a morning and evening watering. What about water restrictions that limit irrigation systems to certain days of the week or days in the month, odd or even for example. Perhaps you would like different schedules for winter and summer. Now you would like to adjust the times based on weather conditions, past, present or future. Let's turn a zone or even a controller off for system maintenance. Starting to sound more like your system? Finally what's going on now and what's up next.

Each controller has an associated (master) sensor which shows on/off status and other attributes. The master will be on when any of its zones are on. The master sensor can have a pre and post amble period to activate or warm up the system like charge up a pump, enable WiFi or turn on a master valve. The master sensor has a number of service calls available to enable/disable all the zones it controls.

Zones also have an associated sensor which, like the master, shows on/off status and various attributes. Zones sensors have service calls that can enable/disable and provide manual runs. Also adjust run times in automation scripts using information from integrations that collect weather data like [OpenWeatherMap](https://www.home-assistant.io/integrations/openweathermap/), [BOM](https://github.com/bremor/bureau_of_meteorology), [weatherunderground](https://www.home-assistant.io/integrations/wunderground/) and many others. Go crazy with projects like [HAsmartirrigation](https://github.com/jeroenterheerdt/HAsmartirrigation).

## Features

1. Unlimited controllers.
2. Unlimited zones.
3. Unlimited schedules. Schedule by absolute time or sun events (sunrise/sunset). Select by days of the week (mon/tue/wed...). Select by days in the month (1/2/3.../odd/even). Select by months in the year (jan/feb/mar...). Overlapped schedules.
4. Hardware independant. Use your own switches/valve controllers.
5. Software independant. Pure play python.

Practicle limitations will depend on your hardware.

## Structure

Irrigation Unlimited is comprised of controllers, zones and schedules in a tree like formation. Each controller has one or more zones and each zone has one or more schedules. Controllers and zones will have a binary sensor associated with each one so they can be intregrated with Home Assistant.

~~~text
└── Irrigation Unlimited
  └── Controller 1 -> binary_sensor.irrigation_unlimited_c1_m
    └── Zone 1 -> binary_sensor.irrigation_unlimited_c1_z1
      └── Schedule 1
      └── Schedule 2
          ...
      └── Schedule N
    └── Zone 2 -> binary_sensor.irrigation_unlimited_c1_z2
        ...
    └── Zone N -> binary_sensor.irrigation_unlimited_c1_zN
        ...
  └── Controller 2 -> binary_sensor.irrigation_unlimited_c2_m
      ...
  └── Controller N -> binary_sensor.irrigation_unlimited_cN_m
      ...
~~~

Controllers and zones can specify an entity such as a switch or light, basically anything that turns on or off the system can control it. This is the irrigation valve. If this does not go far enough for your purposes then track the state of the binary sensors in an automation and do your own thing like run a script or scene.

**This component will set up the following platforms.**

| Platform | Description |
| ---- | ---- |
| `binary_sensor` | Show a valve `On` or `Off`|

A binary sensor is associated with each controller and zone. Controller or master sensors are named `binary_sensor.irrigation_unlimited_cN_m` and zone sensors `binary_sensor.irrigation_unlimited_cN_zN`. These sensors show the state of the master or child zones. Attributes show additional information like current schedule and next run time and duration.

![example][exampleimg]

## Installation

### Install from HACS

1. Just search for Irrigation Unlimited integration in [HACS][hacs] and install it.
2. Add Irrigation Unlimited to your configuration.yaml file. See _[configuration examples](#configuration-examples)_ below.
3. Restart Home Assistant.

### Manual installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `irrigation_unlimited`.
4. Download _all_ the files from the `custom_components/irrigation_unlimited/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Irrigation"

Using your HA configuration directory (folder) as a starting point you should now also have this:

~~~text
custom_components/irrigation_unlimited/__init__.py
custom_components/irrigation_unlimited/binary_sensor.py
custom_components/irrigation_unlimited/const.py
custom_components/irrigation_unlimited/entity.py
custom_components/irrigation_unlilmited/irrigation_unlimited.py
custom_components/irrigation_unlimited/manifest.json
custom_components/irrigation_unlimited/service.py
custom_components/irrigation_unlimited/services.yaml
~~~

## Configuration

Configuration is done by yaml.

The time type is a string in the format HH:MM. Time type must be a positive value. Seconds can be speicified but they will be rounded down to the system granularity. The default granularity is whole minutes (60 seconds). All times will be syncronised to these boundaries.

| Name | Type | Default | Description |
| -----| ---- | ------- | ----------- |
| `controllers` | list | _[Controller Objects](#controller-objects)_ | Controller details (Must have at least one) |
| `granularity` | number | 60 | System time boundaries in seconds |
| `testing` | object | _[Testing Object](#testing-object)_ | Used for testing setup |

### Controller Objects

This is the controller or master object and manages a collection of zones. There must be at least one controller in the system. The controller state reflects the state of its zones. The controller will be on if any of its zones are on and off when all zones are off.

| Name | Type | Default | Description |
| ---- | ---- | ------- | ----------- |
| `zones` | list | _[Zone Objects](#zone-objects)_ | Zone details (Must have at least one) |
| `name` | string | Controller _N_ | Friendly name for the controller |
| `enabled` | bool | true | Enable/disable the controller |
| `preamble` | time | '00:00' | The time master turns on before any zone turns on |
| `postamble` | time | '00:00' | The time master remains on after all zones are off |
| `entity_id` | string | | Entity ID (`switch.my_master_valve1`)|

### Zone Objects

The zone object manages a collection of schedules. There must be at least one zone for each controller.

| Name | Type | Default | Description |
| ---- | ---- | ------- | ----------- |
| `schedules` | list | _[Schedule Objects](#schedule-objects)_ | Schedule details (Must have at least one) |
| `name` | string | Zone _N_ | Friendly name for the zone |
| `enabled` | bool | true | Enable/disable the zone |
| `minimum` | time | '00:01' | The minimum run time |
| `maximum` | time | | The maximum run time |
| `entity_id` | string | | Entity ID (`switch.my_zone_valve1`) |

### Schedule Objects

Schedules are future events, _not_ dates for example Mondays. There must be at least one schedule for each zone.

The parameters `weekday`, `day` and `month` are date filters. If not specified then all dates qualify.

| Name | Type | Default | Description |
| ---- | ---- | ------- | ----------- |
| `time` | time/_[Sun Event](#sun-event)_ | **Required** | The start time. Either a time (07:30) or sun event |
| `duration` | time | **Required** | The length of time to run |
| `name` | string | Schedule *N* | Friendly name for the schedule |
| `weekday` | list | | The days of week to run [mon, tue...sun] |
| `day` | list | | Days of month to run [1, 2...31]/odd/even |
| `month` | list | | Months of year to run [jan, feb...dec] |

### Sun Event

Leave the time value in the _[Schedule Objects](#schedule-objects)_ blank and add the following object. An optional before or after time can be specified.

| Name | Type | Default | Description |
| ---- | ---- | ------- | ----------- |
| `sun` | string | **Required** | `sunrise` or `sunset` |
| `before` | time | '00:00' | Time before the event |
| `after` | time | '00:00' | Time after the event |

### Testing Object

The testing object is useful for running through a predetermined regime. Note: the `speed` value does _not_ alter the system clock in any way. It is accomplished by an internal 'virtual clock'.

| Name | Type | Default | Description |
| ---- | ---- | ------- | ----------- |
| `enabled` | bool | true | Enable/disable testing |
| `speed` | number | 1.0 | Test speed. A value less than 1 will slow down the system. Values above 1 will speed up tests. A value of 2 will double the speed, 60 will turn minutes to seconds and 3600 will turn hours to seconds. Upper limit will depend on individual systems.|
| `times` | list | _[Test Time Objects](#test-time-objects)_ | Test run times |

### Test Time Objects

This is the test time object. Test times do _not_ alter the system clock so there is no danger of disruption to the Home Assistant system.

| Name | Type | Default | Description |
| ---- | ---- | ------- | ----------- |
| `name` | string | Test *N* | Friendly name for the test |
| `start` | datetime | | The virtual start time (YYYY-mm-dd HH:MM) |
| `end` | datetime | | The virtual end time (YYYY-mm-dd HH:MM) |

## Configuration examples

### Minimal configuration

~~~yaml
# Example configuration.yaml entry
irrigation_unlimited:
  controllers:
    zones:
      entity_id: 'switch.my_switch'
      schedules:
        - time: '06:00'
          duration: '00:20'
~~~

### Sun event example

~~~yaml
# Example configuration.yaml entry
# Run 20 minutes before sunrise for 30 minutes
irrigation_unlimited:
  controllers:
    zones:
      schedules:
        - name: 'Before sunrise'
          time:
            sun: 'sunrise'
            before: '00:20'
          duration: '00:30'
~~~

For a more comprehensive example refer to [here](./examples/all_the_bells_and_whistles.yaml).

## Services

The binary sensor associated with each controller and zone provide several services. The sensors offer the following services:

- `enable`
- `disable`
- `manual_run`
- `adjust_time`

If a controller sensor is targetted then it will effect all its children zones.

### Services `enable` and `disable`

Enables/disables the controller or zone respectively.

| Service data attribute | Optional | Description |
| ---------------------- | -------- | ----------- |
| `entity_id` | no | Controller or zone to enable/disable.

### Service `manual_run`

Turn on the controller or zone for a period of time.

| Service data attribute | Optional | Description |
| ---------------------- | -------- | ----------- |
| `entity_id` | no | Controller or zone to run.
| `time` | no | Controller or zone to run.

### Service `adjust_time`

Adjust the run times. Calling this service will override any previous adjustment i.e. it will *not* make adjustments on adjustments. For example, if the scheduled duration is 30 minutes calling percent: 150 will make it 45 minutes then calling percent 200 will make it 60 minutes. Must have one and only one of `actual`, `percentage`, `increase`, `descrease` or `reset`.

#### Tip

Use forecast and observation data collected by weather integrations in automations to adjust the run times.

| Service data attribute | Optional | Description |
| ---------------------- | -------- | ----------- |
| `entity_id` | no | Controller or zone to run.
| `actual` | yes | Specify a new time time. This will replace the existing duration. A time value is required '00:30'.
| `percentage` | yes | Adjust time by a percentage. A positive float value. Values less than 1 will decrease the run time while values greater than 1 will increase the run time.
| `increase` | yes | Increase the run time by the specified time. A value of '00:10' will increase the duration by 10 minutes. Value will be capped by the `maximum` setting.
| `descrease` | yes | Decrease the run time by the specified time. A value of '00:05' will decrease the run time by 5 minutes. Value will be limited by the `minimum` setting.
| `reset` | yes | Reset adjustment back to the original schedule time (Does not effect minimum or maximum settings).
| `minimum` | yes | Set the minimum run time. Minimum run time is 1 minute and will be limited to this. Use the `disable` service to turn off.
| `maximum` | yes | Set the maximum run time. Note: The default is no limit.

## Frontend

Because this is an integration there is no frontend. For an out-of-the-box vanilla solution, simply put the master and zone binary sensors onto an entity card to see what is going on. However, for some inspiration and a compact card try [this](./examples/card.yaml).

![Collapsed](./examples/card_collapsed.png)

and it expands to:

![Expanded](./examples/card_expanded.png)

Note: This card uses some custom cards [multiple-entity-row](https://github.com/benct/lovelace-multiple-entity-row), [fold-entity-row](https://github.com/thomasloven/lovelace-fold-entity-row) and at the moment [card-mod](https://github.com/thomasloven/lovelace-card-mod) for styles.

## Troubleshooting

Please set your logging for the custom_component to debug:

~~~yaml
logger:
  default: info
  logs:
    custom_components.irrigation_unlimited: debug
~~~

## Notes

1. All feature requests, issues and questions are welcome.

<a href="https://www.buymeacoffee.com/rgc99" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height=40px width=144px></a><!---->

## Contributions are welcome

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md).

## Credits

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template.

***

[irrigation_unlimited]: https://github.com/custom-components/irrigation_unlimited
[buymecoffee]: https://www.buymeacoffee.com/rgc99
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/custom-components/blueprint.svg?style=for-the-badge
[commits]: https://github.com/custom-components/irrigation_unlimited/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/custom-components/blueprint.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Robert%20Cook%20%40rgc99-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/custom-components/blueprint.svg?style=for-the-badge
[releases]: https://github.com/custom-components/irrigation_unlimited/releases
[integration_blueprint]: https://github.com/custom-components/integration_blueprint
