"""irrigation_unlimited config flow test"""

# pylint: disable=unused-import
import datetime
import homeassistant.core as ha
from custom_components.irrigation_unlimited.const import (
    SERVICE_EXPORT_CONFIG,
)
from tests.iu_test_support import IUExam, mk_utc, mk_local

IUExam.quiet_mode()


async def test_export_config(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Model IUExam class."""
    # pylint: disable=unused-argument

    async with IUExam(hass, "test_export_config.yaml") as exam:

        await exam.begin_test(1)
        data = await exam.call(
            SERVICE_EXPORT_CONFIG,
            None,
            True,
        )
        assert data == {
            "controllers": [
                {
                    "name": "Test controller 1",
                    "zones": [
                        {"name": "Zone 1", "zone_id": "1"},
                        {"name": "Zone 2", "zone_id": "2"},
                    ],
                    "sequences": [
                        {
                            "name": "Sequence 1",
                            "delay": "0:01:00",
                            "zones": [
                                {"zone_id": "1", "duration": "0:06:00"},
                                {"zone_id": "2", "duration": "0:12:00"},
                            ],
                            "schedules": [
                                {
                                    "name": "Schedule 1",
                                    "time": "{'sun': 'sunrise', 'before': datetime.timedelta(seconds=2)}",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        await exam.finish_test()
        exam.check_summary()
