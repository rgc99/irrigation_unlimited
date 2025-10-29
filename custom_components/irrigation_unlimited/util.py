"""Various support routines"""

from typing import Any
from datetime import timedelta, date, datetime, time
from homeassistant.util import dt


def convert_data(data: Any) -> Any:
    """Convert the data to a JSON serializable format"""

    def convert_item(value: Any) -> Any:
        if isinstance(value, timedelta):
            return round(value.total_seconds())
        if isinstance(value, (date, datetime)):
            return dt.as_local(value).isoformat()
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
