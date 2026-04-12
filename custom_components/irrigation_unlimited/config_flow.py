"""Config flow for Irrigation Unlimited."""

from __future__ import annotations

import copy
import logging
from datetime import date as date_type
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)
from homeassistant import config_entries
from homeassistant.const import CONF_DELAY, CONF_ENTITY_ID, CONF_NAME, CONF_WEEKDAY
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
    CONF_SEQUENCES,
    CONF_START_N_DAYS,
    CONF_TIME,
    CONF_ZONE_ID,
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


# ── Schema helpers ─────────────────────────────────────────────────────────────

def _zone_form_schema(default_name: str, default_entity: str | None) -> vol.Schema:
    schema: dict = {vol.Required(CONF_NAME, default=default_name): _TEXT_SELECTOR}
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
                    options=[{"value": str(i), "label": z[CONF_NAME]} for i, z in enumerate(zones)],
                    mode=SelectSelectorMode.LIST,
                )
            )
        }
    )


def _target_options(zones: list[dict], sequences: list[dict]) -> list[dict]:
    """Options list covering every zone and sequence (for schedule assignment)."""
    opts = [{"value": f"zone:{i}", "label": f"Zone: {z[CONF_NAME]}"} for i, z in enumerate(zones)]
    for i, s in enumerate(sequences):
        opts.append({"value": f"seq:{i}", "label": f"Sequence: {s.get(CONF_NAME, f'Sequence {i+1}')}"})
    return opts


def _target_select_schema(
    zones: list[dict],
    sequences: list[dict],
    default_target: str = "zone:0",
) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("target_ref", default=default_target): SelectSelector(
                SelectSelectorConfig(
                    options=_target_options(zones, sequences),
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )


def _schedule_details_schema(
    include_duration: bool = True,
    default_name: str = "",
    default_time: str = "06:00",
    default_duration: str = "00:20:00",
    default_every_n_days: int | None = None,
    default_start_date: str = "",
    default_weekday: list[str] | None = None,
) -> vol.Schema:
    schema: dict = {
        vol.Optional(CONF_NAME, default=default_name): _TEXT_SELECTOR,
        vol.Required(CONF_TIME, default=default_time): _TEXT_SELECTOR,
    }
    if include_duration:
        schema[vol.Required(CONF_DURATION, default=default_duration)] = _TEXT_SELECTOR
    if default_every_n_days is not None:
        schema[vol.Optional(CONF_EVERY_N_DAYS, default=default_every_n_days)] = NumberSelector(
            NumberSelectorConfig(min=1, max=365, step=1, mode=NumberSelectorMode.BOX)
        )
    else:
        schema[vol.Optional(CONF_EVERY_N_DAYS)] = NumberSelector(
            NumberSelectorConfig(min=1, max=365, step=1, mode=NumberSelectorMode.BOX)
        )
    schema[vol.Optional(CONF_START_N_DAYS, default=default_start_date)] = TextSelector(
        TextSelectorConfig(type=TextSelectorType.DATE)
    )
    if default_weekday is not None:
        schema[vol.Optional(CONF_WEEKDAY, default=default_weekday)] = _WEEKDAY_SELECTOR
    else:
        schema[vol.Optional(CONF_WEEKDAY)] = _WEEKDAY_SELECTOR
    return vol.Schema(schema)


def _schedule_select_schema(zones: list[dict], sequences: list[dict]) -> vol.Schema:
    options = []
    for zi, zone in enumerate(zones):
        for si, sched in enumerate(zone.get(CONF_SCHEDULES, [])):
            name = sched.get(CONF_NAME) or f"Schedule {si + 1}"
            label = f"Zone {zone[CONF_NAME]}: {name} ({sched.get(CONF_TIME,'?')} for {sched.get(CONF_DURATION,'?')})"
            options.append({"value": f"zone:{zi}:{si}", "label": label})
    for qi, seq in enumerate(sequences):
        seq_name = seq.get(CONF_NAME, f"Sequence {qi + 1}")
        for si, sched in enumerate(seq.get(CONF_SCHEDULES, [])):
            name = sched.get(CONF_NAME) or f"Schedule {si + 1}"
            label = f"Seq {seq_name}: {name} ({sched.get(CONF_TIME, '?')})"
            options.append({"value": f"seq:{qi}:{si}", "label": label})
    return vol.Schema(
        {vol.Required("schedule_ref"): SelectSelector(SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST))}
    )


def _sequence_select_schema(sequences: list[dict]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("sequence_index"): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": str(i), "label": s.get(CONF_NAME, f"Sequence {i + 1}")}
                        for i, s in enumerate(sequences)
                    ],
                    mode=SelectSelectorMode.LIST,
                )
            )
        }
    )


def _sequence_zone_form_schema(
    zones: list[dict],
    default_zone_id: str = "1",
    exclude_zone_ids: set[str] | None = None,
) -> vol.Schema:
    available = [
        (i, z) for i, z in enumerate(zones)
        if exclude_zone_ids is None or str(i + 1) not in exclude_zone_ids
    ]
    return vol.Schema(
        {
            vol.Required(CONF_ZONE_ID, default=default_zone_id): SelectSelector(
                SelectSelectorConfig(
                    options=[{"value": str(i + 1), "label": z[CONF_NAME]} for i, z in available],
                    mode=SelectSelectorMode.LIST,
                )
            ),
        }
    )


def _sequence_zone_select_schema(sequence: dict, zones: list[dict]) -> vol.Schema:
    """Selector for zones within a sequence."""
    sz_list = sequence.get(CONF_ZONES, [])
    options = []
    for i, sz in enumerate(sz_list):
        zone_id = sz.get(CONF_ZONE_ID, ["?"])[0] if isinstance(sz.get(CONF_ZONE_ID), list) else str(sz.get(CONF_ZONE_ID, "?"))
        zone_name = _zone_name_for_id(zones, zone_id)
        dur = sz.get(CONF_DURATION, "")
        label = f"{zone_name}" + (f" ({dur})" if dur else "")
        options.append({"value": str(i), "label": label})
    return vol.Schema(
        {vol.Required("zone_position"): SelectSelector(SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST))}
    )


def _sequence_added_zone_ids(sequence: dict) -> set[str]:
    """Return the set of zone_ids already present in a sequence."""
    ids: set[str] = set()
    for sz in sequence.get(CONF_ZONES, []):
        zid = sz.get(CONF_ZONE_ID)
        if isinstance(zid, list):
            ids.update(zid)
        elif zid:
            ids.add(str(zid))
    return ids


def _format_sequence_zones(sequence: dict, zones: list[dict]) -> str:
    """Return a human-readable list of zones in a sequence."""
    sz_list = sequence.get(CONF_ZONES, [])
    if not sz_list:
        return "No zones added yet."
    lines = []
    for sz in sz_list:
        zid = sz.get(CONF_ZONE_ID, ["?"])
        zid = zid[0] if isinstance(zid, list) else str(zid)
        lines.append(f"- {_zone_name_for_id(zones, zid)}")
    return "\n".join(lines)


def _format_sequences_overview(sequences: list[dict], zones: list[dict]) -> str:
    """Return a multi-line overview of all sequences and their zones."""
    if not sequences:
        return "No sequences configured."
    lines = []
    for i, seq in enumerate(sequences):
        name = seq.get(CONF_NAME, f"Sequence {i + 1}")
        sz_list = seq.get(CONF_ZONES, [])
        zone_names = []
        for sz in sz_list:
            zid = sz.get(CONF_ZONE_ID, ["?"])
            zid = zid[0] if isinstance(zid, list) else str(zid)
            zone_names.append(_zone_name_for_id(zones, zid))
        zones_str = ", ".join(zone_names) if zone_names else "no zones"
        lines.append(f"{name}: {zones_str}")
    return "\n".join(lines)


def _zone_name_for_id(zones: list[dict], zone_id: str) -> str:
    """Look up a zone name from its zone_id (1-based index string)."""
    try:
        idx = int(zone_id) - 1
        return zones[idx][CONF_NAME]
    except (ValueError, IndexError):
        return f"Zone {zone_id}"


# ── Schedule helpers ───────────────────────────────────────────────────────────

def _sequence_duration_info(sequence: dict) -> str:
    """Return a human-readable total duration estimate for a sequence."""
    sz_list = sequence.get(CONF_ZONES, [])
    n = len(sz_list)
    if n == 0:
        return "No zones in sequence yet."
    dur_str = sequence.get(CONF_DURATION, "")
    delay_str = sequence.get(CONF_DELAY, "")
    if dur_str and delay_str:
        return f"Estimated run: {n} zones × {dur_str} + {n - 1} gaps × {delay_str}"
    if dur_str:
        return f"Estimated run: {n} zones × {dur_str}"
    if delay_str:
        return f"{n} zones with {delay_str} gaps (zone durations set individually)"
    return f"{n} zones (durations set individually)"


def _build_schedule(user_input: dict) -> dict:
    schedule: dict = {CONF_TIME: user_input[CONF_TIME]}
    if CONF_DURATION in user_input:
        schedule[CONF_DURATION] = user_input[CONF_DURATION]
    if name := user_input.get(CONF_NAME, "").strip():
        schedule[CONF_NAME] = name
    every_n = user_input.get(CONF_EVERY_N_DAYS)
    if every_n is not None and int(every_n) > 1:
        start = user_input.get(CONF_START_N_DAYS) or str(date_type.today())
        schedule[CONF_DAY] = {CONF_EVERY_N_DAYS: int(every_n), CONF_START_N_DAYS: start}
    elif weekday := user_input.get(CONF_WEEKDAY):
        schedule[CONF_WEEKDAY] = weekday
    return schedule


def _describe_recurrence(schedule: dict) -> str:
    if CONF_WEEKDAY in schedule:
        return ", ".join(schedule[CONF_WEEKDAY])
    day = schedule.get(CONF_DAY)
    if isinstance(day, dict) and CONF_EVERY_N_DAYS in day:
        return f"every {day[CONF_EVERY_N_DAYS]} days from {day.get(CONF_START_N_DAYS, '')}"
    return "every day"


def _format_schedules_list(zones: list[dict], sequences: list[dict]) -> str:
    lines = []
    for zone in zones:
        for s in zone.get(CONF_SCHEDULES, []):
            name = s.get(CONF_NAME, "")
            entry = f"Zone {zone[CONF_NAME]}: {s.get(CONF_TIME,'?')} for {s.get(CONF_DURATION,'?')} - {_describe_recurrence(s)}"
            if name:
                entry = f"Zone {zone[CONF_NAME]}: {name}: {s.get(CONF_TIME,'?')} for {s.get(CONF_DURATION,'?')} - {_describe_recurrence(s)}"
            lines.append(entry)
    for i, seq in enumerate(sequences):
        seq_name = seq.get(CONF_NAME, f"Sequence {i+1}")
        for s in seq.get(CONF_SCHEDULES, []):
            name = s.get(CONF_NAME, "")
            entry = f"Seq {seq_name}: {s.get(CONF_TIME,'?')} - {_describe_recurrence(s)}"
            if name:
                entry = f"Seq {seq_name}: {name}: {s.get(CONF_TIME,'?')} - {_describe_recurrence(s)}"
            lines.append(entry)
    return "\n".join(lines) if lines else "No schedules configured."


def _has_schedules(zones: list[dict], sequences: list[dict]) -> bool:
    return any(z.get(CONF_SCHEDULES) for z in zones) or any(s.get(CONF_SCHEDULES) for s in sequences)


# ── Config flow (initial setup) ────────────────────────────────────────────────

class IUConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Irrigation Unlimited."""

    VERSION = 1

    def __init__(self) -> None:
        self._controller_name: str = ""
        self._zones: list[dict] = []

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> IUOptionsFlow:
        return IUOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict | None = None) -> config_entries.FlowResult:
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

    async def async_step_add_zone(self, user_input: dict | None = None) -> config_entries.FlowResult:
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

    async def async_step_zone_menu(self, user_input: dict | None = None) -> config_entries.FlowResult:
        return self.async_show_menu(step_id="zone_menu", menu_options=["add_zone", "finish"])

    async def async_step_finish(self, user_input: dict | None = None) -> config_entries.FlowResult:
        return self.async_create_entry(
            title=self._controller_name,
            data={CONF_CONTROLLERS: [{CONF_NAME: self._controller_name, CONF_ZONES: self._zones}]},
        )


# ── Options flow (edit after setup) ───────────────────────────────────────────

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
        self._zones: list[dict] = copy.deepcopy(controller.get(CONF_ZONES, []))
        self._sequences: list[dict] = copy.deepcopy(controller.get(CONF_SEQUENCES, []))
        entity_ids = controller.get(CONF_ENTITY_ID, [])
        self._master_entity: str | None = entity_ids[0] if entity_ids else None
        # Zone editing
        self._edit_zone_index: int | None = None
        # Schedule editing
        self._edit_schedule_ref: str | None = None  # "zone:zi:si" or "seq:qi:si"
        # Sequence editing
        self._pending_sequence: dict | None = None   # sequence being built/edited
        self._edit_sequence_index: int | None = None  # None = new, int = editing existing
        self._edit_seq_zone_pos: int | None = None    # position within sequence zones
        # Schedule editing
        self._pending_schedule_target: str | None = None  # "zone:N" or "seq:N"

    def _current_config(self) -> dict:
        config = {CONF_NAME: self._controller_name, CONF_ZONES: self._zones}
        if self._sequences:
            config[CONF_SEQUENCES] = self._sequences
        return {CONF_CONTROLLERS: [config]}

    def _decode_schedule_ref(self, ref: str) -> tuple[str, int, int]:
        """Parse "zone:zi:si" or "seq:qi:si" → (kind, outer_idx, schedule_idx)."""
        parts = ref.split(_REF_SEP)
        return parts[0], int(parts[1]), int(parts[2])

    def _schedule_owner(self, kind: str, idx: int) -> dict:
        return self._zones[idx] if kind == "zone" else self._sequences[idx]

    def _default_target(self) -> str:
        return "zone:0" if self._zones else (f"seq:0" if self._sequences else "zone:0")

    # ── Init menu ──────────────────────────────────────────────────────────────

    async def async_step_init(self, user_input: dict | None = None) -> config_entries.FlowResult:
        has_zones = bool(self._zones)
        has_sequences = bool(self._sequences)
        has_schedules = _has_schedules(self._zones, self._sequences)
        has_targets = has_zones or has_sequences

        menu_options = ["add_zone"]
        if has_zones:
            menu_options += ["edit_zone", "remove_zone"]
        menu_options += ["add_sequence"]
        if has_sequences:
            menu_options += ["view_sequences", "edit_sequence", "remove_sequence"]
        if has_targets:
            menu_options += ["add_schedule"]
        if has_schedules:
            menu_options += ["edit_schedule", "remove_schedule", "view_schedules"]
        menu_options.append("finish")
        return self.async_show_menu(step_id="init", menu_options=menu_options)

    # ── Zones ──────────────────────────────────────────────────────────────────

    async def async_step_add_zone(self, user_input: dict | None = None) -> config_entries.FlowResult:
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

    async def async_step_edit_zone(self, user_input: dict | None = None) -> config_entries.FlowResult:
        if user_input is not None:
            self._edit_zone_index = int(user_input["zone_index"])
            return await self.async_step_edit_zone_details()
        return self.async_show_form(step_id="edit_zone", data_schema=_zone_select_schema(self._zones))

    async def async_step_edit_zone_details(self, user_input: dict | None = None) -> config_entries.FlowResult:
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

    async def async_step_remove_zone(self, user_input: dict | None = None) -> config_entries.FlowResult:
        if user_input is not None:
            self._zones.pop(int(user_input["zone_index"]))
            return await self.async_step_init()
        return self.async_show_form(step_id="remove_zone", data_schema=_zone_select_schema(self._zones))

    # ── Sequences ──────────────────────────────────────────────────────────────

    async def async_step_add_sequence(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Start building a new sequence: collect name, delay and duration."""
        if user_input is not None:
            self._pending_sequence = {
                CONF_NAME: user_input[CONF_NAME],
                CONF_DURATION: user_input[CONF_DURATION],
                CONF_ZONES: [],
            }
            if delay := user_input.get(CONF_DELAY, "").strip():
                self._pending_sequence[CONF_DELAY] = delay
            self._edit_sequence_index = None
            return await self.async_step_sequence_menu()
        seq_number = len(self._sequences) + 1
        return self.async_show_form(
            step_id="add_sequence",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=f"Sequence {seq_number}"): _TEXT_SELECTOR,
                vol.Optional(CONF_DELAY, default=""): _TEXT_SELECTOR,
                vol.Required(CONF_DURATION, default="00:10"): _TEXT_SELECTOR,
            }),
        )

    async def async_step_edit_sequence(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Select which sequence to edit."""
        if user_input is not None:
            self._edit_sequence_index = int(user_input["sequence_index"])
            self._pending_sequence = dict(self._sequences[self._edit_sequence_index])
            self._pending_sequence[CONF_ZONES] = list(self._pending_sequence.get(CONF_ZONES, []))
            return await self.async_step_edit_sequence_details()
        return self.async_show_form(step_id="edit_sequence", data_schema=_sequence_select_schema(self._sequences))

    async def async_step_edit_sequence_details(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Edit the name, delay and duration of the selected sequence."""
        if user_input is not None:
            self._pending_sequence[CONF_NAME] = user_input[CONF_NAME]
            self._pending_sequence[CONF_DURATION] = user_input[CONF_DURATION]
            if delay := user_input.get(CONF_DELAY, "").strip():
                self._pending_sequence[CONF_DELAY] = delay
            else:
                self._pending_sequence.pop(CONF_DELAY, None)
            return await self.async_step_sequence_menu()
        return self.async_show_form(
            step_id="edit_sequence_details",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=self._pending_sequence.get(CONF_NAME, "")): _TEXT_SELECTOR,
                vol.Optional(CONF_DELAY, default=self._pending_sequence.get(CONF_DELAY, "")): _TEXT_SELECTOR,
                vol.Required(CONF_DURATION, default=self._pending_sequence.get(CONF_DURATION, "00:10")): _TEXT_SELECTOR,
            }),
        )

    async def async_step_remove_sequence(self, user_input: dict | None = None) -> config_entries.FlowResult:
        if user_input is not None:
            self._sequences.pop(int(user_input["sequence_index"]))
            return await self.async_step_init()
        return self.async_show_form(step_id="remove_sequence", data_schema=_sequence_select_schema(self._sequences))

    async def async_step_view_sequences(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Show all sequences; selecting one navigates to its edit page."""
        if user_input is not None:
            idx = int(user_input["sequence_index"])
            self._edit_sequence_index = idx
            self._pending_sequence = dict(self._sequences[idx])
            self._pending_sequence[CONF_ZONES] = list(self._pending_sequence.get(CONF_ZONES, []))
            return await self.async_step_edit_sequence_details()
        return self.async_show_form(
            step_id="view_sequences",
            data_schema=_sequence_select_schema(self._sequences),
            description_placeholders={
                "sequences": _format_sequences_overview(self._sequences, self._zones)
            },
        )

    # ── Sequence zone management ───────────────────────────────────────────────

    async def async_step_sequence_menu(self, _user_input: dict | None = None) -> config_entries.FlowResult:
        """Menu for managing zones within the pending sequence."""
        sz_list = self._pending_sequence.get(CONF_ZONES, [])
        # Only offer "add zone" when there are still zones available to add
        added_ids = _sequence_added_zone_ids(self._pending_sequence)
        can_add = len(added_ids) < len(self._zones)
        menu_options = []
        if can_add:
            menu_options.append("add_sequence_zone")
        if sz_list:
            menu_options += ["edit_sequence_zone", "remove_sequence_zone"]
        menu_options.append("finish_sequence")
        return self.async_show_menu(
            step_id="sequence_menu",
            menu_options=menu_options,
            description_placeholders={
                "zones_list": _format_sequence_zones(self._pending_sequence, self._zones)
            },
        )

    async def async_step_add_sequence_zone(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Add a zone step to the pending sequence."""
        if user_input is not None:
            self._pending_sequence.setdefault(CONF_ZONES, []).append(
                {CONF_ZONE_ID: [user_input[CONF_ZONE_ID]]}
            )
            return await self.async_step_sequence_menu()
        exclude = _sequence_added_zone_ids(self._pending_sequence)
        return self.async_show_form(
            step_id="add_sequence_zone",
            data_schema=_sequence_zone_form_schema(self._zones, exclude_zone_ids=exclude),
        )

    async def async_step_edit_sequence_zone(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Select which zone step to edit."""
        if user_input is not None:
            self._edit_seq_zone_pos = int(user_input["zone_position"])
            return await self.async_step_edit_sequence_zone_details()
        return self.async_show_form(
            step_id="edit_sequence_zone",
            data_schema=_sequence_zone_select_schema(self._pending_sequence, self._zones),
        )

    async def async_step_edit_sequence_zone_details(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Edit a zone step within the pending sequence."""
        pos = self._edit_seq_zone_pos
        if user_input is not None:
            self._pending_sequence[CONF_ZONES][pos] = {CONF_ZONE_ID: [user_input[CONF_ZONE_ID]]}
            self._edit_seq_zone_pos = None
            return await self.async_step_sequence_menu()
        sz = self._pending_sequence[CONF_ZONES][pos]
        zone_id = sz.get(CONF_ZONE_ID, ["1"])[0] if isinstance(sz.get(CONF_ZONE_ID), list) else str(sz.get(CONF_ZONE_ID, "1"))
        return self.async_show_form(
            step_id="edit_sequence_zone_details",
            data_schema=_sequence_zone_form_schema(self._zones, default_zone_id=zone_id),
        )

    async def async_step_remove_sequence_zone(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Remove a zone step from the pending sequence."""
        if user_input is not None:
            self._pending_sequence[CONF_ZONES].pop(int(user_input["zone_position"]))
            return await self.async_step_sequence_menu()
        return self.async_show_form(
            step_id="remove_sequence_zone",
            data_schema=_sequence_zone_select_schema(self._pending_sequence, self._zones),
        )

    async def async_step_finish_sequence(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Save the pending sequence."""
        if self._edit_sequence_index is not None:
            self._sequences[self._edit_sequence_index] = self._pending_sequence
        else:
            self._sequences.append(self._pending_sequence)
        self._pending_sequence = None
        self._edit_sequence_index = None
        return await self.async_step_init()

    # ── Schedules ─────────────────────────────────────────────────────────────

    async def async_step_add_schedule(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Step 1: choose which zone or sequence to schedule."""
        if user_input is not None:
            self._pending_schedule_target = user_input["target_ref"]
            return await self.async_step_add_schedule_details()
        return self.async_show_form(
            step_id="add_schedule",
            data_schema=_target_select_schema(self._zones, self._sequences, self._default_target()),
        )

    async def async_step_add_schedule_details(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Step 2: enter schedule details (duration omitted for sequences)."""
        kind, idx = self._pending_schedule_target.split(_REF_SEP)
        is_seq = kind == "seq"
        if user_input is not None:
            owner = self._schedule_owner(kind, int(idx))
            owner.setdefault(CONF_SCHEDULES, []).append(_build_schedule(user_input))
            _LOGGER.debug("IU add_schedule_details: owner id=%d schedules=%s", id(owner), owner.get(CONF_SCHEDULES))
            _LOGGER.debug("IU add_schedule_details: zones[%s] id=%d", idx, id(self._zones[int(idx)]) if kind == "zone" else -1)
            self._pending_schedule_target = None
            return await self.async_step_init()
        duration_info = _sequence_duration_info(self._sequences[int(idx)]) if is_seq else ""
        return self.async_show_form(
            step_id="add_schedule_details",
            data_schema=_schedule_details_schema(include_duration=not is_seq),
            description_placeholders={"duration_info": duration_info},
        )

    async def async_step_edit_schedule(self, user_input: dict | None = None) -> config_entries.FlowResult:
        if user_input is not None:
            self._edit_schedule_ref = user_input["schedule_ref"]
            return await self.async_step_edit_schedule_details()
        return self.async_show_form(
            step_id="edit_schedule",
            data_schema=_schedule_select_schema(self._zones, self._sequences),
        )

    async def async_step_edit_schedule_details(self, user_input: dict | None = None) -> config_entries.FlowResult:
        kind, old_idx, old_si = self._decode_schedule_ref(self._edit_schedule_ref)
        is_seq = kind == "seq"
        owner = self._schedule_owner(kind, old_idx)
        if user_input is not None:
            owner[CONF_SCHEDULES][old_si] = _build_schedule(user_input)
            self._edit_schedule_ref = None
            return await self.async_step_init()
        sched = owner[CONF_SCHEDULES][old_si]
        day = sched.get(CONF_DAY)
        duration_info = _sequence_duration_info(self._sequences[old_idx]) if is_seq else ""
        return self.async_show_form(
            step_id="edit_schedule_details",
            data_schema=_schedule_details_schema(
                include_duration=not is_seq,
                default_name=sched.get(CONF_NAME, ""),
                default_time=sched.get(CONF_TIME, "06:00"),
                default_duration=sched.get(CONF_DURATION, "00:20:00"),
                default_every_n_days=day.get(CONF_EVERY_N_DAYS) if isinstance(day, dict) else None,
                default_start_date=str(day.get(CONF_START_N_DAYS, "")) if isinstance(day, dict) else "",
                default_weekday=sched.get(CONF_WEEKDAY),
            ),
            description_placeholders={"duration_info": duration_info},
        )

    async def async_step_remove_schedule(self, user_input: dict | None = None) -> config_entries.FlowResult:
        if user_input is not None:
            kind, idx, si = self._decode_schedule_ref(user_input["schedule_ref"])
            owner = self._schedule_owner(kind, idx)
            owner[CONF_SCHEDULES].pop(si)
            if not owner[CONF_SCHEDULES]:
                del owner[CONF_SCHEDULES]
            return await self.async_step_init()
        return self.async_show_form(
            step_id="remove_schedule",
            data_schema=_schedule_select_schema(self._zones, self._sequences),
        )

    async def async_step_view_schedules(self, user_input: dict | None = None) -> config_entries.FlowResult:
        if user_input is not None:
            return await self.async_step_init()
        return self.async_show_form(
            step_id="view_schedules",
            data_schema=vol.Schema({}),
            description_placeholders={"schedules": _format_schedules_list(self._zones, self._sequences)},
        )

    # ── Finish ─────────────────────────────────────────────────────────────────

    async def async_step_finish(self, user_input: dict | None = None) -> config_entries.FlowResult:
        cfg = self._current_config()
        _LOGGER.debug("IU finish: saving config=%s", cfg)
        return self.async_create_entry(title="", data=cfg)
