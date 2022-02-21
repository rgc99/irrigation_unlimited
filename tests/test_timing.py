"""Test irrigation_unlimited timing operations."""
# pylint: disable=unused-import
import os
import glob
import homeassistant.core as ha
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_timings(hass: ha.HomeAssistant, skip_setup, skip_history):
    # pylint: disable=unused-argument
    """Test timings. Process all the configuration files in the
    test_config directory matching timing_*.yaml and check the results."""

    for fname in glob.glob(IUExam.default_config_dir + "timing_*.yaml"):
        print(f"Processing: {fname}")
        async with IUExam(hass, os.path.basename(fname)) as exam:
            await exam.run_all()
            exam.check_summary()
