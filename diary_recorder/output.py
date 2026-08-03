"""Output formatting for diary CLI commands."""

from diary_recorder.models import Event, Note, DateSummary


def show(date_str: str, events: list[Event], notes: list[Note]) -> str:
    """Format the show command output with numbered events and notes."""
    lines = [f"# {date_str}", ""]
    lines.append("## Events")
    if events:
        lines.append("")
    for i, e in enumerate(events, 1):
        lines.append(f"{i}. `{e.time}` {e.content}")

    lines.append("")
    lines.append("## Notes")
    if notes:
        lines.append("")
    for i, n in enumerate(notes, 1):
        lines.append(f"{i}. {n.content}")

    return "\n".join(lines) + "\n"


def list_dates(dates: list[DateSummary]) -> str:
    """Format the list command output."""
    if not dates:
        return ""
    lines = []
    for d in dates:
        ev_label = "event" if d.event_count == 1 else "events"
        nt_label = "note" if d.note_count == 1 else "notes"
        lines.append(
            f"{d.date_str}  {d.weekday}  "
            f"{d.event_count} {ev_label}, {d.note_count} {nt_label}"
        )
    return "\n".join(lines) + "\n"


def add_event(event: Event, date_str: str) -> str:
    """Format the add event confirmation message."""
    return (
        f"Added event for {date_str}:\n"
        f"• `{event.time}` {event.content}"
    )


def modify_event(old: Event, new: Event, date_str: str) -> str:
    """Format the modify event confirmation message (diff style)."""
    return (
        f"Modified event for {date_str}:\n"
        f"- `{old.time}` {old.content}\n"
        f"+ `{new.time}` {new.content}"
    )


def delete_event(event: Event, date_str: str) -> str:
    """Format the delete event confirmation message."""
    return (
        f"Deleted event for {date_str}:\n"
        f"• `{event.time}` {event.content}"
    )


def add_note(note: Note, date_str: str) -> str:
    """Format the add note confirmation message."""
    return (
        f"Added note for {date_str}:\n"
        f"• {note.content}"
    )


def modify_note(old: Note, new: Note, date_str: str) -> str:
    """Format the modify note confirmation message (diff style)."""
    return (
        f"Modified note for {date_str}:\n"
        f"- {old.content}\n"
        f"+ {new.content}"
    )


def delete_note(note: Note, date_str: str) -> str:
    """Format the delete note confirmation message."""
    return (
        f"Deleted note for {date_str}:\n"
        f"• {note.content}"
    )
