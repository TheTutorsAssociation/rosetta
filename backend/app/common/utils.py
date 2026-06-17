import re
from datetime import datetime, time


def escape_like(value: str) -> str:
    r"""Escape special LIKE pattern characters (%, _, \) for safe use in SQL LIKE queries."""
    return re.sub(r'([%_\\])', r'\\\1', value)


def inclusive_end_of_day(dt: datetime) -> datetime:
    """Bump a date-only datetime (time == 00:00:00) to end-of-day; pass through otherwise.

    Used for inclusive upper-bound date filters: ``created_to=2024-03-15`` should include
    records from the whole of March 15th, whereas an explicit time (``2024-03-15T10:00:00``)
    is preserved verbatim so callers can express sub-day cutoffs.
    """
    if dt.time() == time(0, 0, 0):
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt
