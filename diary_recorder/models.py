from dataclasses import dataclass


@dataclass
class Event:
    """A single diary event with time and content."""

    time: str      # "HH:MM"
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
