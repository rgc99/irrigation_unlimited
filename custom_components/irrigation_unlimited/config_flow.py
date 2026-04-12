"""Config flow for Irrigation Unlimited."""

from __future__ import annotations

from datetime import date as date_type
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME, CONF_WEEKDAY
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_CONTROLLERS,
    CONF_DAY,
    CONF_DURATION,
    CONF_EVERY_N_DAYS,
    CONF_SCHEDULES,
    CONF_START_N_DAYS,
    CONF_TIME,
    CONF_ZONES,
    DOMAIN,
)

_ENTITY_SELECTOR = EntitySelector(EntitySelectorConfig(domain=["switch", "valve"]))
_TEXT_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))
_WEEKDAY_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[
            {"value": "mon", "label": "Monday"},
            {"value": "tue", "label": "Tuesday"},
            {"value": "wed", "label": "Wednesday"},
            {"value": "thu", "label": "Thursday"},
            {"value": "fri", "label": "Friday"},
            {"value": "sat", "label": "Saturday"},
            {"value": "sun", "label": "Sunday"},
        ],
        multiple=True,
        mode=SelectSelectorMode.LIST,
    )
)

_REF_SEP = ":"


def _zone_form_schema(default_name: str, default_entity: str | None) -> vol.Schema:
    schema: dict = {
        vol.Required(CONF_NAME, default=default_name): _TEXT_SELECTOR,
    }
    if default_entity is not None:
        schema[vol.Optional(CONF_ENTITY_ID, default=default_entity)] = _ENTITY_SELECTOR
    else:
        schema[vol.Optional(CONF_ENTITY_ID)] = _ENTITY_SELECTOR
    return vol.Schema(schema)


def _zone_select_schema(zones: list[dict]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("zone_index"): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": str(i), "label": z[CONF_NAME]}
                        for i, z in enumerate(zones)
                    ],
                    mode=SelectSelectorMode.LIST,
                )
            )
        }
    )


def _schedule_form_schema(
    zones: list[dict],
    default_zone_index: int = 0,
    default_name: str = "",
    default_time: str = "06:00",
    default_duration: str = "00:20:00",
    default_every_n_days: int | None = None,
    default_start_date: str = "",
    default_weekday: list[str] | None = None,
) -> vol.Schema:
    """Single form: zone, name, time, duration, every-N-days, weekdays.

    Priority when saving: every_n_days (>1) > weekdays > every day.
    """
    schema: dict = {
        vol.Required("zone_index", default=str(default_zone_index)): SelectSelector(
            SelectSelectorConfig(
                options=[
                    {"value": str(i), "label": z[CONF_NAME]}
                    for i, z in enumerate(zones)
                ],
                mode=SelectSelectorMode.LIST,
            )
        ),
        vol.Optional(CONF_NAME, default=default_name): _TEXT_SELECTOR,
        vol.Required(CONF_TIME, default=default_time): _TEXT_SELECTOR,
        vol.Required(CONF_DURATION, default=default_duration): _TEXT_SELECTOR,
    }

    # Every-N-days fields (above weekdays per user request)
    if default_every_n_days is not None:
        schema[vol.Optional(CONF_EVERY_N_DAYS, default=default_every_n_days)] = (
            NumberSelector(
                NumberSelectorConfig(min=1, max=365, step=1, mode=NumberSelectorMode.BOX)
            )
        )
    else:
        schema[vol.Optional(CONF_EVERY_N_DAYS)] = NumberSelector(
            NumberSelectorConfig(min=1, max=365, step=1, mode=NumberSelectorMode.BOX)
        )

    schema[vol.Optional(CONF_START_N_DAYS, default=default_start_date)] = TextSelector(
        TextSelectorConfig(type=TextSelectorType.DATE)
    )

    # Days of week (below every-N-days per user request)
    if default_weekday is not None:
        schema[vol.Optional(CONF_WEEKDAY, default=default_weekday)] = _WEEKDAY_SELECTOR
    else:
        schema[vol.Optional(CONF_WEEKDAY)] = _WEEKDAY_SELECTOR

    return vol.Schema(schema)


def _schedule_select_schema(zones: list[dict]) -> vol.Schema:
    """Selector listing all schedules across all zones."""
    options = []
    for zi, zone in enumerate(zones):
        for si, sched in enumerate(zone.get(CONF_SCHEDULES, [])):
            name = sched.get(CONF_NAME) or f"Schedule {si + 1}"
            time = sched.get(CONF_TIME, "?")
            duration = sched.get(CONF_DURATION, "?")
            label = f"{zone[CONF_NAME]}: {name} ({time} for {duration})"
            options.append({"value": f"{zi}{_REF_SEP}{si}", "label": label})
    return vol.Schema(
        {
            vol.Required("schedule_ref"): SelectSelector(
                SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST)
            )
        }
    )


def _build_schedule(user_input: dict) -> dict:
    """Build a schedule dict from form input.

    Priority: every_n_days (>1) > weekdays > every day.
    """
    schedule: dict = {
        CONF_TIME: user_input[CONF_TIME],
        CONF_DURATION: user_input[CONF_DURATION],
    }
    if name := user_input.get(CONF_NAME, "").strip():
        schedule[CONF_NAME] = name

    every_n = user_input.get(CONF_EVERY_N_DAYS)
    if every_n is not None and int(every_n) > 1:
        start = user_input.get(CONF_START_N_DAYS) or str(date_type.today())
        schedule[CONF_DAY] = {
            CONF_EVERY_N_DAYS: int(every_n),
            CONF_START_N_DAYS: start,  # ISO string; coordinator parses it back to date
        }
    elif weekday := user_input.get(CONF_WEEKDAY):
        schedule[CONF_WEEKDAY] = weekday

    return schedule


def _describe_recurrence(schedule: dict) -> str:
    if CONF_WEEKDAY in schedule:
        return ", ".join(schedule[CONF_WEEKDAY])
    day = schedule.get(CONF_DAY)
    if isinstance(day, dict) and CONF_EVERY_N_DAYS in day:
        n = day[CONF_EVERY_N_DAYS]
        start = day.get(CONF_START_N_DAYS, "")
        return f"every {n} days from {start}"
    return "every day"


def _format_schedules_list(zones: list[dict]) -> str:
    lines = []
    for zone in zones:
        schedules = zone.get(CONF_SCHEDULES, [])
        if not schedules:
            continue
        lines.append(f"{zone[CONF_NAME]}:")
        for s in schedules:
            name = s.get(CONF_NAME, "")
            time = s.get(CONF_TIME, "?")
            duration = s.get(CONF_DURATION, "?")
            recurrence = _describe_recurrence(s)
            entry = f"  {time} for {duration} - {recurrence}"
            if name:
                entry = f"  {name}: {time} for {duration} - {recurrence}"
            lines.append(entry)
    return "\n".join(lines) if lines else "No schedules configured."


class IUConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Irrigation Unlimited."""

    VERSION = 1

    def __init__(self) -> None:
        self._controller_name: str = ""
        self._zones: list[dict] = []

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> IUOptionsFlow:
        return IUOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._controller_name = user_input[CONF_NAME]
            return await self.async_step_add_zone()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, default="Irrigation Controller"
                    ): _TEXT_SELECTOR
                }
            ),
        )

    async def async_step_add_zone(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            zone: dict = {CONF_NAME: user_input[CONF_NAME]}
            if entity_id := user_input.get(CONF_ENTITY_ID):
                zone[CONF_ENTITY_ID] = [entity_id]
            self._zones.append(zone)
            return await self.async_step_zone_menu()
        zone_number = len(self._zones) + 1
        return self.async_show_form(
            step_id="add_zone",
            data_schema=_zone_form_schema(f"Zone {zone_number}", None),
            description_placeholders={"zone_number": str(zone_number)},
        )

    async def async_step_zone_menu(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        return self.async_show_menu(
            step_id="zone_menu",
            menu_options=["add_zone", "finish"],
        )

    async def async_step_finish(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        return self.async_create_entry(
            title=self._controller_name,
            data={
                CONF_CONTROLLERS: [
                    {CONF_NAME: self._controller_name, CONF_ZONES: self._zones}
                ]
            },
        )


class IUOptionsFlow(config_entries.OptionsFlow):
    """Handle options (edit) flow for Irrigation Unlimited."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        # Options take precedence over data when present (written by previous options flows)
        current = (
            dict(config_entry.options)
            if config_entry.options
            else dict(config_entry.data)
        )
        controller = current[CONF_CONTROLLERS][0]
        self._controller_name: str = controller[CONF_NAME]
        self._zones: list[dict] = list(controller.get(CONF_ZONES, []))
        self._edit_zone_index: int | None = None
        self._edit_schedule_ref: str | None = None  # "zi:si"

    def _current_config(self) -> dict:
        return {
            CONF_CONTROLLERS: [
                {CONF_NAME: self._controller_name, CONF_ZONES: self._zones}
            ]
        }

    def _decode_ref(self, ref: str) -> tuple[int, int]:
        zi, si = ref.split(_REF_SEP)
        return int(zi), int(si)

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        has_zones = bool(self._zones)
        has_schedules = any(z.get(CONF_SCHEDULES) for z in self._zones)
        menu_options = ["add_zone"]
        if has_zones:
            menu_options += ["edit_zone", "remove_zone", "add_schedule"]
        if has_schedules:
            menu_options += ["edit_schedule", "remove_schedule", "view_schedules"]
        menu_options.append("finish")
        return self.async_show_menu(step_id="init", menu_options=menu_options)

    # ── Zones ─────────────────────────────────────────────────────────────────

    async def async_step_add_zone(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            zone: dict = {CONF_NAME: user_input[CONF_NAME]}
            if entity_id := user_input.get(CONF_ENTITY_ID):
                zone[CONF_ENTITY_ID] = [entity_id]
            self._zones.append(zone)
            return await self.async_step_init()
        zone_number = len(self._zones) + 1
        return self.async_show_form(
            step_id="add_zone",
            data_schema=_zone_form_schema(f"Zone {zone_number}", None),
            description_placeholders={"zone_number": str(zone_number)},
        )

    async def async_step_edit_zone(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._edit_zone_index = int(user_input["zone_index"])
            return await self.async_step_edit_zone_details()
        return self.async_show_form(
            step_id="edit_zone",
            data_schema=_zone_select_schema(self._zones),
        )

    async def async_step_edit_zone_details(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            zone = dict(self._zones[self._edit_zone_index])
            zone[CONF_NAME] = user_input[CONF_NAME]
            if entity_id := user_input.get(CONF_ENTITY_ID):
                zone[CONF_ENTITY_ID] = [entity_id]
            else:
                zone.pop(CONF_ENTITY_ID, None)
            self._zones[self._edit_zone_index] = zone
            self._edit_zone_index = None
            return await self.async_step_init()
        zone = self._zones[self._edit_zone_index]
        current_entity = (zone.get(CONF_ENTITY_ID) or [None])[0]
        return self.async_show_form(
            step_id="edit_zone_details",
            data_schema=_zone_form_schema(zone[CONF_NAME], current_entity),
            description_placeholders={"zone_name": zone[CONF_NAME]},
        )

    async def async_step_remove_zone(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._zones.pop(int(user_input["zone_index"]))
            return await self.async_step_init()
        return self.async_show_form(
            step_id="remove_zone",
            data_schema=_zone_select_schema(self._zones),
        )

    # ── Schedules ─────────────────────────────────────────────────────────────

    async def async_step_add_schedule(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            zi = int(user_input["zone_index"])
            self._zones[zi].setdefault(CONF_SCHEDULES, []).append(
                _build_schedule(user_input)
            )
            return await self.async_step_init()
        return self.async_show_form(
            step_id="add_schedule",
            data_schema=_schedule_form_schema(self._zones),
        )

    async def async_step_edit_schedule(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._edit_schedule_ref = user_input["schedule_ref"]
            return await self.async_step_edit_schedule_details()
        return self.async_show_form(
            step_id="edit_schedule",
            data_schema=_schedule_select_schema(self._zones),
        )

    async def async_step_edit_schedule_details(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        zi, si = self._decode_ref(self._edit_schedule_ref)

        if user_input is not None:
            new_zi = int(user_input["zone_index"])
            # Remove from old location
            self._zones[zi][CONF_SCHEDULES].pop(si)
            if not self._zones[zi][CONF_SCHEDULES]:
                del self._zones[zi][CONF_SCHEDULES]
            # Insert at new zone
            self._zones[new_zi].setdefault(CONF_SCHEDULES, []).append(
                _build_schedule(user_input)
            )
            self._edit_schedule_ref = None
            return await self.async_step_init()

        sched = self._zones[zi][CONF_SCHEDULES][si]
        day = sched.get(CONF_DAY)
        default_every_n = (
            day.get(CONF_EVERY_N_DAYS) if isinstance(day, dict) else None
        )
        default_start = (
            str(day.get(CONF_START_N_DAYS, "")) if isinstance(day, dict) else ""
        )
        return self.async_show_form(
            step_id="edit_schedule_details",
            data_schema=_schedule_form_schema(
                zones=self._zones,
                default_zone_index=zi,
                default_name=sched.get(CONF_NAME, ""),
                default_time=sched.get(CONF_TIME, "06:00"),
                default_duration=sched.get(CONF_DURATION, "00:20:00"),
                default_every_n_days=default_every_n,
                default_start_date=default_start,
                default_weekday=sched.get(CONF_WEEKDAY),
            ),
        )

    async def async_step_remove_schedule(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            zi, si = self._decode_ref(user_input["schedule_ref"])
            self._zones[zi][CONF_SCHEDULES].pop(si)
            if not self._zones[zi][CONF_SCHEDULES]:
                del self._zones[zi][CONF_SCHEDULES]
            return await self.async_step_init()
        return self.async_show_form(
            step_id="remove_schedule",
            data_schema=_schedule_select_schema(self._zones),
        )

    async def async_step_view_schedules(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            return await self.async_step_init()
        return self.async_show_form(
            step_id="view_schedules",
            data_schema=vol.Schema({}),
            description_placeholders={
                "schedules": _format_schedules_list(self._zones)
            },
        )

    # ── Finish ────────────────────────────────────────────────────────────────

    async def async_step_finish(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        return self.async_create_entry(title="", data=self._current_config())
