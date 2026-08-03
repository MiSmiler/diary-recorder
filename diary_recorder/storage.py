"""File I/O for reading and writing diary markdown files."""

import os
import re
from datetime import date
from pathlib import Path

from diary_recorder.models import Event

_DATE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")


class DiaryStorage:
    """Manages diary markdown files in a base directory."""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def list_dates(self) -> list[tuple[str, str, int]]:
        """Return dates with weekday and event count, reversed chronological."""
        result: list[tuple[str, str, int]] = []
        try:
            for name in os.listdir(self.base_dir):
                m = _DATE_PATTERN.match(name)
                if not m:
                    continue
                date_str = m.group(1)
                count = self._count_events(date_str)
                weekday = self._weekday_abbr(date_str)
                result.append((date_str, weekday, count))
        except FileNotFoundError:
            return []
        result.sort(key=lambda x: x[0], reverse=True)
        return result

    def read_events(self, date_str: str) -> list[Event]:
        """Read events for a date.  Raises FileNotFoundError if no file."""
        path = self._path(date_str)
        if not path.exists():
            raise FileNotFoundError(f"no diary entry for {date_str}")
        return self._parse(path)

    def add_event(self, date_str: str, event: Event) -> Event:
        """Add an event, auto-creating the file.  Inserts in time order."""
        events = self._read_or_empty(date_str)
        insert_at = self._insert_index(events, event.time)
        events.insert(insert_at, event)
        self._write(date_str, events)
        return event

    def modify_event(
        self,
        date_str: str,
        index: int,
        *,
        new_time: str | None = None,
        new_content: str | None = None,
    ) -> tuple[Event, Event]:
        """Modify an event by 0-based index.

        Returns (old_event, new_event).  Re-sorts if time changed.
        """
        if new_time is None and new_content is None:
            raise ValueError("at least one of new_time or new_content is required")

        events = self.read_events(date_str)
        if index < 0 or index >= len(events):
            raise IndexError(f"event index {index} out of range (0..{len(events)-1})")

        old = events[index]
        new_event = Event(
            time=new_time if new_time is not None else old.time,
            content=new_content if new_content is not None else old.content,
        )
        events.pop(index)
        if new_time is not None:
            insert_at = self._insert_index(events, new_event.time)
            events.insert(insert_at, new_event)
        else:
            events.insert(index, new_event)

        self._write(date_str, events)
        return old, new_event

    def delete_event(self, date_str: str, index: int) -> Event:
        """Delete an event by 0-based index.  Returns the deleted event."""
        events = self.read_events(date_str)
        if index < 0 or index >= len(events):
            raise IndexError(f"event index {index} out of range (0..{len(events)-1})")
        deleted = events.pop(index)
        self._write(date_str, events)
        return deleted

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _path(self, date_str: str) -> Path:
        return Path(self.base_dir) / f"{date_str}.md"

    def _read_or_empty(self, date_str: str) -> list[Event]:
        path = self._path(date_str)
        if not path.exists():
            return []
        return self._parse(path)

    def _parse(self, path: Path) -> list[Event]:
        events: list[Event] = []
        in_events = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("## Events"):
                in_events = True
                continue
            if in_events and line.startswith("- `"):
                # Parse "- `HH:MM` content"
                try:
                    rest = line[3:]  # strip "- `"
                    tick = rest.index("`")
                    time_str = rest[:tick]
                    content = rest[tick + 1:].strip()
                    if time_str:
                        events.append(Event(time=time_str, content=content))
                except (ValueError, IndexError):
                    pass  # malformed line, skip
            elif in_events and line.startswith("#"):
                break  # next section
        return events

    def _write(self, date_str: str, events: list[Event]):
        lines = [f"# {date_str}", "", "## Events", ""]
        for e in events:
            lines.append(f"- `{e.time}` {e.content}")
        lines.append("")  # trailing newline
        self._path(date_str).write_text("\n".join(lines), encoding="utf-8")

    def _count_events(self, date_str: str) -> int:
        path = self._path(date_str)
        if not path.exists():
            return 0
        content = path.read_text(encoding="utf-8")
        return sum(1 for line in content.splitlines() if line.startswith("- `"))

    @staticmethod
    def _insert_index(events: list[Event], new_time: str) -> int:
        """Find insertion index that maintains ascending time order."""
        for i, e in enumerate(events):
            if new_time < e.time:
                return i
        return len(events)

    @staticmethod
    def _weekday_abbr(date_str: str) -> str:
        d = date.fromisoformat(date_str)
        return d.strftime("%a")
