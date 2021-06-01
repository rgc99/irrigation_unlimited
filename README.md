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
4. Unlimited sequences. Operate zones one at a time in a particular order with a delay in between. A 'playlist' for your zones.
5. Hardware independant. Use your own switches/valve controllers.
6. Software independant. Pure play python.

*Practicle limitations will depend on your hardware.

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
| `binary_sensor` | Show a valve `on` or `off`|

A binary sensor is associated with each controller and zone. Controller or master sensors are named `binary_sensor.irrigation_unlimited_cN_m` and zone sensors `binary_sensor.irrigation_unlimited_cN_zN`. These sensors show the state of the master or child zones. Attributes show additional information like current schedule and next run time and duration.

![entities](./examples/entities.png)

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

Configuration is done by yaml. Note: The configuration can be reloaded without restarting HA. See [below](#service-reload) for details and limitations.

The time type is a string in the format HH:MM. Time type must be a positive value. Seconds can be speicified but they will be rounded down to the system granularity. The default granularity is whole minutes (60 seconds). All times will be syncronised to these boundaries.

| Name | Type | Default | Description |
| -----| ---- | ------- | ----------- |
| `controllers` | list | _[Controller Objects](#controller-objects)_ | Controller details (Must have at least one) |
| `granularity` | number | 60 | System time boundaries in seconds |
| `refresh_interval` | number | 30 | Refresh interval in seconds. When a controller or zone is on this value will govern how often the count down timers will update. Decrease this number for a more repsonsive display. Increase this number to conserve resources.
| `testing` | object | _[Testing Object](#testing-object)_ | Used for testing setup |

### Controller Objects

This is the controller or master object and manages a collection of zones. There must be at least one controller in the system. The controller state reflects the state of its zones. The controller will be on if any of its zones are on and off when all zones are off.

| Name | Type | Default | Description |
| ---- | ---- | ------- | ----------- |
| `zones` | list | _[Zone Objects](#zone-objects)_ | Zone details (Must have at least one) |
| `sequences` | list | _[Sequence Objects](#sequence-objects)_ | Sequence details |
| `name` | string | Controller _N_ | Friendly name for the controller |
| `enabled` | bool | true | Enable/disable the controller |
| `preamble` | time | '00:00' | The time master turns on before any zone turns on |
| `postamble` | time | '00:00' | The time master remains on after all zones are off |
| `entity_id` | string | | Entity ID (`switch.my_master_valve1`). Takes a csv list for multiple id's|

### Zone Objects

The zone object manages a collection of schedules. There must be at least one zone for each controller.

| Name | Type | Default | Description |
| ---- | ---- | ------- | ----------- |
| `schedules` | list | _[Schedule Objects](#schedule-objects)_ | Schedule details (Must have at least one) |
| `zone_id` | string | _N_ | Zone reference. Used for sequencing. |
| `name` | string | Zone _N_ | Friendly name for the zone |
| `enabled` | bool | true | Enable/disable the zone |
| `minimum` | time | '00:01' | The minimum run time |
| `maximum` | time | | The maximum run time |
| `entity_id` | string | | Entity ID (`switch.my_zone_valve1`). Takes a csv list for multiple id's |

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

Leave the time value in the _[Schedule Objects](#schedule-objects)_ blank and add the following object. An optional `before` or `after` time can be specified.

| Name | Type | Default | Description |
| ---- | ---- | ------- | ----------- |
| `sun` | string | **Required** | `sunrise` or `sunset` |
| `before` | time | '00:00' | Time before the event |
| `after` | time | '00:00' | Time after the event |

### Sequence Objects

Sequences allow zones to run one at a time in a particular order with a delay in between. This is a type of watering 'playlist'.

| Name | Type | Default | Description |
| ---- | ---- | ------- | ----------- |
| `schedules` | list | _[Schedule Objects](#schedule-objects)_ | Schedule details (Must have at least one). Note: `duration` is ignored |
| `zones` | list | _[Sequence Zone Objects](#sequence-zone-objects)_ | Zone details (Must have at least one) |
| `delay` | time | | Delay between zones. This value is a default for all _[Sequence Zone Objects](#sequence-zone-objects)_ |
| `duration` | time | | The length of time to run. This value is a default for all _[Sequence Zone Objects](#sequence-zone-objects)_ |
| `repeat` | number | 1 | Number of times to repeat the sequence |
| `name` | string | Run _N_ | Friendly name for the sequence |

### Sequence Zone Objects

The sequence zone is a reference to the actual zone defined in the _[Zone Objects](#zone-objects)_. Ensure the `zone_id`'s match between this object and the zone object. The zone may appear more than once in the case of a split run.

| Name | Type | Default | Description |
| ---- | ---- | ------- | ----------- |
| `zone_id` | string | **Required** | Zone reference. This must match the `zone_id` in the _[Zone Objects](#zone-objects)_ |
| `delay` | time | | Delay between zones. This value will override the `delay` setting in the _[Sequence Objects](#sequence-objects)_ |
| `duration` | time | | The length of time to run. This value will override the `duration` setting in the _[Sequence Objects](#sequence-objects)_ |
| `repeat` | number | 1 | Number of times to repeat this zone |

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
      entity_id: "switch.my_switch_1"
      schedules:
        - name: 'Before sunrise'
          time:
            sun: 'sunrise'
            before: '00:20'
          duration: '00:30'
~~~

### Sequence example

~~~yaml
# Example configuration.yaml entry
irrigation_unlimited:
  controllers:
    zones:
      - name: 'Front lawn'
        entity_id: 'switch.my_switch_1'
      - name: 'Vege patch'
        entity_id: 'switch.my_switch_2'
      - name: 'Flower bed'
        entity_id: 'switch.my_switch_3'
    sequences:
      - delay: '00:01'
        schedules:
          - name: 'Sunrise'
            time:
              sun: 'sunrise'
          - name: 'After sunset'
            time:
              sun: 'sunset'
              after: '00:30'
        zones:
          - zone_id: 1
            duration: '00:10'
          - zone_id: 2
            duration: '00:02'
          - zone_id: 3
            duration: '00:01'
~~~

### Simple water saving / eco mode example

~~~yaml
# Example water saver. Run for 5 min on 2 off repeat 3 times
irrigation_unlimited:
  controllers:
    zones:
      - entity_id: 'switch.my_switch_1'
    sequences:
      - duration: '00:05'
        delay: '00:02'
        repeat: 3
        schedules:
          - time: '05:00'
        zones:
          - zone_id: 1
~~~

### Every hour on the hour

~~~yaml
# Example to run for 5 min every hour on the hour from 5am to 5pm
irrigation_unlimited:
  controllers:
    zones:
      - entity_id: 'switch.my_switch_1'
    sequences:
      - name: 'On the hour from 5am to 5pm'
        duration: '00:05'
        delay: '00:55'
        repeat: 12
        schedules:
          - time: '05:00'
        zones:
          - zone_id: 1
~~~

### Seasonal watering

~~~yaml
# Run 15 min 3 times a week in summer, 10 min once a week in winter and twice a week in spring/autumn
irrigation_unlimited:
  controllers:
    zones:
      - entity_id: 'switch.my_switch_1'
        schedules:
          - time: '05:30'
            duration: '00:15'
            weekday: [mon, wed, fri]
            month: [dec, jan, feb]
          - time: '05:30'
            duration: '00:10'
            weekday: [sun]
            month: [jun, jul, aug]
          - time: '05:30'
            duration: '00:12'
            weekday: [mon, thu]
            month: [mar, apr, may, sep, oct, nov]
~~~

For a more comprehensive example refer to [here](./examples/all_the_bells_and_whistles.yaml).

### Tips

1. Schedules can not only have a day of week (mon, wed, fri) but also a month of year (jan, feb, mar). This allows the setup of seasonal watering schedules. For example run every day in summer and twice a week in winter. Setup a different schedule for each month of the year using this filter.

2. Use sequences to setup a water saving or eco mode. Eco mode uses small cycles with a delay to allow the water to soak in and minimise run off. Run all the zones for half the time and then repeat.

3. No need to restart HA after changing the configuration.yaml file. Go to Configuration -> Server Controls -> YAML configuration and reloading and press 'RELOAD IRRIGATION UNLIMITED'.

4. After setting up configuration.yaml, the operation can be controlled via service calls as shown _[below](#services)_. Perform manual runs, adjust watering times, cancel running schedules and enable/disable zones from a _[frontend](#frontend)_

## Services

The binary sensor associated with each controller and zone provide several services. The sensors offer the following services:

- `enable`
- `disable`
- `toggle`
- `cancel`
- `manual_run`
- `adjust_time`

If a controller sensor is targetted then it will effect all its children zones.

### Services `enable`, `disable` and `toggle`

Enables/disables/toggles the controller or zone respectively.

| Service data attribute | Optional | Description |
| ---------------------- | -------- | ----------- |
| `entity_id` | no | Controller or zone to enable/disable/toggle.

### Service `cancel`

Cancels the current running schedule.

| Service data attribute | Optional | Description |
| ---------------------- | -------- | ----------- |
| `entity_id` | no | Controller or zone to cancel.

### Service `manual_run`

Turn on the controller or zone for a period of time. When a sequence is specified each zone's duration will be auto adjusted as a proportion of the original sequence. Zone times are calculated and rounded to the nearest time boundary. This means the total run time may vary from the specified time.

| Service data attribute | Optional | Description |
| ---------------------- | -------- | ----------- |
| `entity_id` | no | Controller or zone to run.
| `time` | no | Total time to run.
| `sequence_id` | yes | Sequence to run (1, 2..N). Only relevant when entity_id is a controller/master. Each zone duration will be adjusted to fit the allocated time.

### Service `adjust_time`

Adjust the run times. Calling this service will override any previous adjustment i.e. it will *not* make adjustments on adjustments. For example, if the scheduled duration is 30 minutes calling percent: 150 will make it 45 minutes then calling percent 200 will make it 60 minutes. Must have one and only one of `actual`, `percentage`, `increase`, `descrease` or `reset`.

#### Tip

Use forecast and observation data collected by weather integrations in automations to adjust the run times. See [below](#automation) for more information.

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

### Service `reload`

Reload the YAML configuration file. Do not add or delete controllers or zones, they will not work because of the associated entities which are created on startup. This may be addressed in a future release, however, suggested work around is to set enabled to false to effectively disable/delete. All other settings can be changed including schedules. You will find the control in Configuration -> Server Controls -> YAML configuration reloading.

## Frontend

Because this is an integration there is no frontend. For an out-of-the-box vanilla solution, simply put the master and zone binary sensors onto an entity card to see what is going on. However, for some inspiration and a compact card try [this](./lovelace/card.yaml).

![Collapsed](./examples/card_collapsed.png)

and it expands to:

![Expanded](./examples/card_expanded.png)

Note: This card uses some custom cards [multiple-entity-row](https://github.com/benct/lovelace-multiple-entity-row), [fold-entity-row](https://github.com/thomasloven/lovelace-fold-entity-row), [logbook-card](https://github.com/royto/logbook-card) and at the moment [card-mod](https://github.com/thomasloven/lovelace-card-mod) for styles.

For watering history information here is a [sample card](./lovelace/watering_history_card.yaml).

![watering_history_card](./examples/watering_history_card.png).

Note: At time of writing this requires a pre-released version of [mini-graph-card](https://github.com/kalkih/mini-graph-card/releases/tag/v0.11.0-dev.3).

Although not really part of the integration but to get you started quickly here is a [temperature card](./lovelace/temperature_card.yaml).

![temperature_card](./examples/temperature_card.png).

And a [rainfall card](./lovelace/rainfall_card.yaml). Note how the watering times reduced as rainfall started. More on this below in [Automation](#Automation).

![rainfall_card](./examples/rainfall_card.png)

Finally, a system event [log](./lovelace/system_history_card.yaml)

![system_history_card](./examples/system_history_card.png)

Putting it all together, here is the [complete picture](./lovelace/my_dashboard.yaml)

![my_dashboard.png](./examples/my_dashboard.png)

This configuration is three vertical stacks and works well on mobile devices.

### Manual run card

Here is a card for manual runs. You can find the code [here](./lovelace/card_manual_run.yaml). Note: This card uses [paper-buttons-row](https://github.com/jcwillox/lovelace-paper-buttons-row) because it can create a button without the need for an actual entity.

![manual_run_card](./examples/card_manual_run.png)

There is a support file [here](./packages/irrigation_unlimited_controls.yaml) which should go in the config/packages directory. Also required is a [pyscript](./pyscript/irrigation_unlimited_service_shim.py) which is called from the above automation to populate the input_select with all the irrigation unlimited controllers and zones. The script should go in the config/pyscript directory. If you don't have a packages or pyscript folder then create them and add the following to your configuration.yaml.

```yaml
homeassistant:
  packages: !include_dir_named packages
```
More information on packages can be found [here](https://www.home-assistant.io/docs/configuration/packages) and pyscript can be found [here](https://github.com/custom-components/pyscript), don't worry about the Jupyter kernel unless you are really keen. Hint: A pyscript is used instead of Jinja2 as it produces a list which Jinja2 is not capable of, many have tried...

## Automation

Due to the many weather integrations available and their relevance to your situation, there is realistically no way to provide a built in 'auto-adjustment' feature. Therefore, no attempt has been made to include a solution and this also makes the integration more independant and flexible. Run time adjustment is achieved by setting up sensor(s) that consume weather information such as rainfall and temperature but could factor in wind speed, solar radiation etc. to determine if more or less watering time is required. You might also consider using forecast information... A service call is then made to irrigation unlimited to adjust the run times. This does mean some knowledge of creating automations is required.

On a personal note, I use the national weather service [BOM](http://www.bom.gov.au) for my forecast information but find their observation data not relevant due to the extreme regional variations in my situation. There are many micro climates (mountains) and a few kilometers in any direction makes a lot of difference, down pour to a few drops. To this end I have a Personal Weather Station (PWS) that feeds [Weather Underground](https://www.wunderground.com) where I use the [WUnderground](https://www.home-assistant.io/integrations/wunderground) integration to retrieve the data.

You will find my adjustment automation [here](./packages/irrigation_unlimited_adjustment.yaml) which feeds off the temperature and rainfall observation data. There is a card [here](./lovelace/observations_card.yaml) which displays this information (uses [multiple-entity-row](https://github.com/benct/lovelace-multiple-entity-row)). Some ideas were gleaned from [kloggy's](https://github.com/kloggy/HA-Irrigation-Version2) work.

### HAsmartirrigation
[HAsmartirrigation](https://github.com/jeroenterheerdt/HAsmartirrigation) calculates the time to run your irrigation system to compensate for moisture lost by evaporation / evapotranspiration. The following automation runs at 23:30 and takes the calculated run time from HAsmartirrigation and updates Irrigation Unlimited with the new watering time. It then calls HAsmartirrigation to reset the bucket when the irrigation has run.

~~~yaml
# Example automation for HAsmartirrigation integration (smart_irrigation)[https://github.com/jeroenterheerdt/HAsmartirrigation]
automation:
  - alias: Smart Irrigation adjustment
    description: Adjust watering times based on smart irrigation calculations
    trigger:
      - platform: time
          at: "23:30"
    action:
      - service: irrigation_unlimited.adjust_time
        data:
          entity_id: binary_sensor.irrigation_unlimited_c1_z1
          actual: >
            {% set t = states('sensor.smart_irrigation_daily_adjusted_run_time') | int %}
            {{ '{:02d}:{:02d}:{:02d}'.format((t // 3600) % 24, (t % 3600) // 60, (t % 3600) % 60) }}
    mode: single

  - alias: Smart Irrigation reset bucket
    description: Resets the Smart Irrigation bucket after watering
    trigger:
      - platform: state
        entity_id:
          # Add Irrigation Unlimited sensors here
          - binary_sensor.irrigation_unlimited_c1_m
        from: "on"
        to: "off"
    action:
      - service: smart_irrigation.smart_irrigation_reset_bucket
~~~

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

Some inspiration was taken from [kloggy](https://github.com/kloggy/HA-Irrigation-Version2)'s work.

***

[irrigation_unlimited]: https://github.com/rgc99/irrigation_unlimited
[buymecoffee]: https://www.buymeacoffee.com/rgc99
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/rgc99/irrigation_unlimited?style=for-the-badge
[commits]: https://github.com/rgc99/irrigation_unlimited/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/rgc99/irrigation_unlimited.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Robert%20Cook%20%40rgc99-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/rgc99/irrigation_unlimited.svg?style=for-the-badge
[releases]: https://github.com/rgc99/irrigation_unlimited/releases
[download-shield]: https://img.shields.io/github/downloads/rgc99/irrigation_unlimited/total?style=for-the-badge
[integration_blueprint]: https://github.com/custom-components/integration_blueprint
