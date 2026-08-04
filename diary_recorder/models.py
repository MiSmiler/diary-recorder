import re
from dataclasses import dataclass
from typing import Generic, TypeVar

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^\d{2}:\d{2}$")

T = TypeVar("T")


@dataclass
class TimePoint:
    """A point in time with optional date and time parts.

    date_str: "YYYY-MM-DD" or None
    time_str: "HH:MM" or None
    """

    date_str: str | None
    time_str: str | None

    def __post_init__(self):
        if self.date_str is not None and not _DATE_RE.match(self.date_str):
            raise ValueError(f"invalid date_str '{self.date_str}': expected YYYY-MM-DD")
        if self.time_str is not None and not _TIME_RE.match(self.time_str):
            raise ValueError(f"invalid time_str '{self.time_str}': expected HH:MM")


@dataclass
class ModifyResult(Generic[T]):
    """Result of a modify operation, carrying old/new values and dates."""

    old: T
    new: T
    old_date: str
    new_date: str


@dataclass
class Event:
    """A single diary event with time and content."""

    time: str  # "HH:MM"
    content: str


@dataclass
class Note:
    """A single diary note with content only (no time)."""

    content: str


@dataclass
class DateSummary:
    """Aggregate summary of a single date's diary entries."""

    date_str: str
    weekday: str
    event_count: int
    note_count: int
