"""Utility helper functions."""

from typing import Dict, Any
from datetime import datetime


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO string."""
    return dt.isoformat()


def parse_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime string to datetime object."""
    return datetime.fromisoformat(dt_str)


def safe_get(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary."""
    return d.get(key, default)
