# UI Configuration

> **Experimental.** UI configuration is still in early development and covers a subset of the full feature set. For complex setups, YAML configuration is recommended.

Irrigation Unlimited can be configured through the Home Assistant UI for basic setups — no `yaml` required.

> **YAML takes precedence.** If an `irrigation_unlimited:` block exists in your `configuration.yaml`, it will override any settings made through the UI. Remove or comment out the YAML block to use UI configuration exclusively.

## Adding the integration

1. In HA go to **Settings → Devices & Services → Add Integration**.
2. Search for **Irrigation Unlimited** and select it.
3. Follow the prompts to configure your first controller.

## What can be configured via the UI

- Controllers (name, master valve entity)
- Zones (name, switch entity, default duration)
- Sequences (name, zone order)
- Schedules (start time, duration, days of week or every N days)

## Limitations

The UI currently supports a subset of the options available through YAML. Features such as sun events, cron expressions, adjustments, history, check-back, and advanced sequence options require YAML configuration. See the [full configuration reference](README.md#5-configuration) in the README.

## Entities created per zone

When configured via the UI, the following entities are created for each zone and grouped as a single HA device:

| Entity | Description |
| --- | --- |
| `binary_sensor` | Current on/off state with schedule attributes |
| `button` | Trigger a manual run immediately |
| `number` | Run duration (minutes) used for manual runs |
| `switch` | Enable or disable the zone |

Sequences and controllers get equivalent groupings.

## Reloading

After making changes through the UI the integration reloads automatically — no HA restart is needed.

## Exporting to YAML

If you outgrow the UI and want to move to a full YAML configuration, you can export your current setup using the `export_config` action.

In **Developer Tools → Actions**:

```yaml
action: irrigation_unlimited.export_config
data: {}
```

The response contains your complete configuration in `configuration.yaml`-compatible format, including all controllers, zones, sequences, and schedules. To use it:

1. Copy the response and paste it into `configuration.yaml` under an `irrigation_unlimited:` key:
   ```yaml
   irrigation_unlimited:
     controllers:
       - name: ...
         zones: ...
         sequences: ...
   ```
2. Restart Home Assistant (or reload the integration).
3. Remove the integration from **Settings → Devices & Services** to avoid the UI config conflicting with the YAML.

> **Note:** YAML takes precedence over UI settings — if both exist, the YAML config will be used and UI changes will have no effect.
