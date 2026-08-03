"""File I/O for reading and writing diary markdown files."""

import os
import re
from datetime import date
from pathlib import Path

from diary_recorder.models import Event, Note, DateSummary

_DATE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")


class DiaryStorage:
    """Manages diary markdown files in a base directory."""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def list_dates(self) -> list[DateSummary]:
        """Return dates with weekday and entry counts, reversed chronological."""
        result: list[DateSummary] = []
        try:
            for name in os.listdir(self.base_dir):
                m = _DATE_PATTERN.match(name)
                if not m:
                    continue
                date_str = m.group(1)
                path = self._path(date_str)
                events, notes = self._parse(path)
                result.append(DateSummary(
                    date_str=date_str,
                    weekday=self._weekday_abbr(date_str),
                    event_count=len(events),
                    note_count=len(notes),
                ))
        except FileNotFoundError:
            return []
        result.sort(key=lambda x: x.date_str, reverse=True)
        return result

    def read(self, date_str: str) -> tuple[list[Event], list[Note]]:
        """Read events and notes for a date.  Raises FileNotFoundError if no file."""
        path = self._path(date_str)
        if not path.exists():
            raise FileNotFoundError(f"no diary entry for {date_str}")
        return self._parse(path)

    def read_raw(self, date_str: str) -> str:
        """Read raw markdown content.  Raises FileNotFoundError if no file."""
        path = self._path(date_str)
        if not path.exists():
            raise FileNotFoundError(f"no diary entry for {date_str}")
        return path.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Event operations
    # ------------------------------------------------------------------

    def add_event(self, date_str: str, event: Event) -> Event:
        """Add an event, auto-creating the file.  Inserts in time order."""
        events, notes = self._read_or_empty(date_str)
        insert_at = self._insert_index(events, event.time)
        events.insert(insert_at, event)
        self._write(date_str, events, notes)
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

        events, notes = self.read(date_str)
        if index < 0 or index >= len(events):
            raise IndexError(
                f"event #{index + 1} not found for {date_str} "
                f"(has {len(events)} event{'s' if len(events) != 1 else ''})"
            )

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

        self._write(date_str, events, notes)
        return old, new_event

    def delete_event(self, date_str: str, index: int) -> Event:
        """Delete an event by 0-based index.  Returns the deleted event."""
        events, notes = self.read(date_str)
        if index < 0 or index >= len(events):
            raise IndexError(
                f"event #{index + 1} not found for {date_str} "
                f"(has {len(events)} event{'s' if len(events) != 1 else ''})"
            )
        deleted = events.pop(index)
        self._write(date_str, events, notes)
        return deleted

    # ------------------------------------------------------------------
    # Note operations
    # ------------------------------------------------------------------

    def add_note(self, date_str: str, note: Note) -> Note:
        """Add a note, auto-creating the file.  Appends to the end."""
        events, notes = self._read_or_empty(date_str)
        notes.append(note)
        self._write(date_str, events, notes)
        return note

    def modify_note(
        self,
        date_str: str,
        index: int,
        *,
        new_content: str,
    ) -> tuple[Note, Note]:
        """Modify a note by 0-based index.  Returns (old_note, new_note)."""
        events, notes = self.read(date_str)
        if index < 0 or index >= len(notes):
            raise IndexError(
                f"note #{index + 1} not found for {date_str} "
                f"(has {len(notes)} note{'s' if len(notes) != 1 else ''})"
            )

        old = notes[index]
        new_note = Note(content=new_content)
        notes[index] = new_note
        self._write(date_str, events, notes)
        return old, new_note

    def delete_note(self, date_str: str, index: int) -> Note:
        """Delete a note by 0-based index.  Returns the deleted note."""
        events, notes = self.read(date_str)
        if index < 0 or index >= len(notes):
            raise IndexError(
                f"note #{index + 1} not found for {date_str} "
                f"(has {len(notes)} note{'s' if len(notes) != 1 else ''})"
            )
        deleted = notes.pop(index)
        self._write(date_str, events, notes)
        return deleted

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _path(self, date_str: str) -> Path:
        return Path(self.base_dir) / f"{date_str}.md"

    def _read_or_empty(self, date_str: str) -> tuple[list[Event], list[Note]]:
        path = self._path(date_str)
        if not path.exists():
            return [], []
        return self._parse(path)

    def _parse(self, path: Path) -> tuple[list[Event], list[Note]]:
        text = path.read_text(encoding="utf-8")

        # Check that both expected sections exist
        if "## Events" not in text:
            raise ValueError(f"missing ## Events section in {path.name}")
        if "## Notes" not in text:
            raise ValueError(f"missing ## Notes section in {path.name}")

        events: list[Event] = []
        notes: list[Note] = []
        current_section: str | None = None

        for line in text.splitlines():
            if line.startswith("## Events"):
                current_section = "events"
                continue
            if line.startswith("## Notes"):
                current_section = "notes"
                continue
            if line.startswith("#"):
                current_section = None
                continue

            if current_section == "events" and line.startswith("- `"):
                try:
                    rest = line[3:]  # strip "- `"
                    tick = rest.index("`")
                    time_str = rest[:tick]
                    content = rest[tick + 1:].strip()
                    if time_str:
                        events.append(Event(time=time_str, content=content))
                except (ValueError, IndexError):
                    pass

            elif current_section == "notes" and line.startswith("- "):
                content = line[2:].strip()
                if content:
                    notes.append(Note(content=content))

        return events, notes

    @staticmethod
    def _format_event(event: Event) -> str:
        return f"- `{event.time}` {event.content}"

    @staticmethod
    def _format_note(note: Note) -> str:
        return f"- {note.content}"

    def _write(self, date_str: str, events: list[Event], notes: list[Note]):
        lines = [f"# {date_str}", ""]
        lines.append("## Events")
        lines.append("")
        for e in events:
            lines.append(self._format_event(e))
        lines.append("")
        lines.append("## Notes")
        if notes:
            lines.append("")
        for n in notes:
            lines.append(self._format_note(n))
        self._path(date_str).write_text("\n".join(lines) + "\n", encoding="utf-8")

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
