"""irrigation_unlimited util test module"""

from homeassistant.util.dt import parse_datetime, parse_duration, parse_time, parse_date
from custom_components.irrigation_unlimited.util import (
    convert_data,
    is_none,
)


async def test_util():
    """Test util module"""

    assert convert_data(
        [
            {
                "atimedelta": parse_duration("01:10:30"),
                "adate": parse_date("2025-12-16"),
                "atime": parse_time("12:30:15"),
                "adatetime": parse_datetime("2025-12-16T12:30:15-08:00"),
            },
        ]
    ) == [
        {
            "atimedelta": 4230,
            "adate": "2025-12-16",
            "atime": "12:30:15",
            "adatetime": "2025-12-16T12:30:15-08:00",
        }
    ]

    assert is_none(None, "abc") == "abc"
    assert is_none(None, 123) == 123
