from datetime import datetime

import pytz


def get_now_utc() -> datetime:
    """Get the current timestamp in UTC"""
    return datetime.now(tz=pytz.UTC)
