"""irrigation_unlimited test unit for native cycle-and-soak"""

from datetime import timedelta
import homeassistant.core as ha
from tests.iu_test_support import IUExam
from custom_components.irrigation_unlimited.const import (
    SERVICE_MANUAL_RUN,
    SERVICE_TIME_ADJUST,
)
from custom_components.irrigation_unlimited.irrigation_unlimited import calc_cycles

IUExam.quiet_mode()


def _td(spec: str) -> timedelta:
    """Build a timedelta from a M or H:M:S style helper"""
    parts = [int(p) for p in spec.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    return timedelta(hours=parts[0], minutes=parts[1], seconds=parts[2])


def test_calc_cycles() -> None:
    """Unit test the cycle splitting algorithm"""
    max_d = _td("0:15:0")
    min_d = _td("0:10:0")

    # Even split, no trailing stub
    assert calc_cycles(_td("0:45:0"), max_d, min_d) == [_td("0:15:0")] * 3
    # Uneven total distributed evenly (35 -> 3 x ~11.7, sum preserved)
    cycles = calc_cycles(_td("0:35:0"), max_d, min_d)
    assert len(cycles) == 3
    assert sum(cycles, timedelta()) == _td("0:35:0")
    # Min duration floor caps the cycle count
    assert calc_cycles(_td("0:20:0"), max_d, min_d) == [_td("0:10:0")] * 2
    # Total below the floor runs once
    assert calc_cycles(_td("0:05:0"), max_d, min_d) == [_td("0:05:0")]
    # Total equal to the cap is a single cycle
    assert calc_cycles(_td("0:15:0"), max_d, min_d) == [_td("0:15:0")]
    # No cap configured -> single cycle
    assert calc_cycles(_td("0:45:0"), None, min_d) == [_td("0:45:0")]
    # Nothing to run
    assert calc_cycles(timedelta(0), max_d, min_d) == []
    # No min duration: pure max split
    assert calc_cycles(_td("0:60:0"), max_d, None) == [_td("0:15:0")] * 4


async def test_sequence_cycle_basic(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Three equal zones interleave with a guaranteed soak."""
    async with IUExam(hass, "test_sequence_cycle_basic.yaml") as exam:
        await exam.run_test(1)
        exam.check_summary()


async def test_sequence_cycle_dropout(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Zones with smaller totals finish early and drop out."""
    async with IUExam(hass, "test_sequence_cycle_dropout.yaml") as exam:
        await exam.run_test(1)
        exam.check_summary()


async def test_sequence_cycle_edge(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Short, exact-cap and even-split edge cases."""
    async with IUExam(hass, "test_sequence_cycle_edge.yaml") as exam:
        await exam.run_test(1)
        exam.check_summary()


async def test_sequence_cycle_adjust(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """adjust_time actual re-derives the per-cycle split (Smart Irrigation)."""
    async with IUExam(hass, "test_sequence_cycle_adjust.yaml") as exam:
        await exam.run_test(1)
        # Push a new total onto the first sequence zone; the next run should
        # re-derive from 45 -> 60 min i.e. 4 cycles of 15 instead of 3.
        await exam.call(
            SERVICE_TIME_ADJUST,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_s1",
                "actual": "01:00:00",
                "zones": [1],
            },
        )
        await exam.run_test(2)
        exam.check_summary()


async def test_sequence_cycle_manual_run(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """manual_run honours cycle-and-soak and interleaves the zones."""
    async with IUExam(hass, "test_sequence_cycle_manual.yaml") as exam:
        await exam.begin_test(1)
        await exam.call(
            SERVICE_MANUAL_RUN,
            {
                "entity_id": "binary_sensor.irrigation_unlimited_c1_m",
                "sequence_id": 1,
            },
        )
        await exam.finish_test()
        exam.check_summary()


async def test_sequence_cycle_zone_override(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """A sequence zone overrides the sequence-level max_duration."""
    async with IUExam(hass, "test_sequence_cycle_zone_override.yaml") as exam:
        await exam.run_test(1)
        exam.check_summary()


async def test_sequence_cycle_zone_only(
    hass: ha.HomeAssistant, skip_dependencies, skip_history
):
    """Per-zone cycle blocks activate cycle-and-soak without a sequence cycle."""
    async with IUExam(hass, "test_sequence_cycle_zone_only.yaml") as exam:
        await exam.run_test(1)
        exam.check_summary()
