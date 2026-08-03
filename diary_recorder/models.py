from dataclasses import dataclass


@dataclass
class Event:
    """A single diary event with time and content."""

    time: str      # "HH:MM"
    content: str
