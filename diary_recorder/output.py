"""Output formatting for diary CLI commands."""

from diary_recorder.models import Event


def show(date_str: str, events: list[Event]) -> str:
    """Format the show command output with numbered events."""
    lines = [f"# {date_str}", "", "## Events"]
    if events:
        lines.append("")
        for i, e in enumerate(events, 1):
            lines.append(f"{i}. `{e.time}` {e.content}")
    return "\n".join(lines) + "\n"


def list_dates(dates: list[tuple[str, str, int]]) -> str:
    """Format the list command output."""
    if not dates:
        return ""
    lines = []
    for date_str, weekday, count in dates:
        label = "event" if count == 1 else "events"
        lines.append(f"{date_str}  {weekday}  {count} {label}")
    return "\n".join(lines) + "\n"


def add(event: Event, date_str: str) -> str:
    """Format the add confirmation message."""
    return (
        f"Added event for {date_str}:\n"
        f"• `{event.time}` {event.content}"
    )


def modify(old: Event, new: Event, date_str: str) -> str:
    """Format the modify confirmation message (diff style)."""
    return (
        f"Modified event for {date_str}:\n"
        f"- `{old.time}` {old.content}\n"
        f"+ `{new.time}` {new.content}"
    )


def delete(event: Event, date_str: str) -> str:
    """Format the delete confirmation message."""
    return (
        f"Deleted event for {date_str}:\n"
        f"• `{event.time}` {event.content}"
    )
