"""Various support routines"""

from typing import Any
from datetime import timedelta, date, datetime, time
from homeassistant.util import dt

# We use this a lot so make a constant
TD_ZERO = timedelta(0)


def convert_data(data: Any) -> Any:
    """Convert the data to a JSON serializable format"""

    def convert_item(value: Any) -> Any:
        if isinstance(value, timedelta):
            return round(value.total_seconds())
        if isinstance(value, datetime):
            return dt.as_local(value).isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, time):
            return value.isoformat()
        return value

    if isinstance(data, dict):
        for key, value in data.copy().items():
            if isinstance(value, (dict, list)):
                data[key] = convert_data(value)
            else:
                data[key] = convert_item(value)
        return data
    elif isinstance(data, list):
        return [convert_data(item) for item in data]
    else:
        return convert_item(data)


def is_none(value: Any | None, default: Any) -> Any:
    """Return the supplied value if not None otherwise
    return the default"""
    return value if value is not None else default
