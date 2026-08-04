"""CLI entry point using argparse."""

import argparse
import os
import re
import sys
from datetime import datetime, timedelta

from diary_recorder import output
from diary_recorder.models import Event, Note, TimePoint
from diary_recorder.storage import DiaryStorage

_RELATIVE_RE = re.compile(r"^-(?:(\d+)h)?(?:(\d+)(?:min|m))?$")


def parse_timepoint(s: str, *, now: datetime | None = None) -> TimePoint:
    """Parse a TimePoint string into a TimePoint dataclass.

    Accepts forms like:
    - "2026-08-03T12:30" (full datetime)
    - "todayT14:00" (today with time)
    - "today" (date only)
    - "2026-08-03" (date only)
    - "now" (current date and time)
    - "-15min", "-1h20m", "-5h" (relative time offset)

    The `now` parameter is used to resolve relative times and "now"/"today".
    If None, the current system time is used.
    """
    if now is None:
        now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    if "T" in s:
        # Reject spaces around T
        if " T" in s or "T " in s:
            raise ValueError(f"invalid timepoint '{s}': no spaces allowed around 'T'")
        date_part, time_part = s.split("T", 1)
        if time_part == "now":
            raise ValueError("'now' cannot be combined with a date part. Use 'now' standalone.")
        if date_part == "today":
            date_part = today_str
        return TimePoint(date_str=date_part, time_str=time_part)
    if s == "today":
        return TimePoint(date_str=today_str, time_str=None)
    if s == "now":
        return TimePoint(date_str=today_str, time_str=now.strftime("%H:%M"))

    # Relative time: -15min, -1h20m, -5h, -15m
    if s.startswith("-"):
        m = _RELATIVE_RE.match(s)
        if not m or (m.group(1) is None and m.group(2) is None):
            raise ValueError(f"invalid relative time '{s}': expected -Nh, -Nmin, -Nm, or -NhNm")
        hours = int(m.group(1)) if m.group(1) else 0
        minutes = int(m.group(2)) if m.group(2) else 0
        offset_minutes = hours * 60 + minutes
        if offset_minutes == 0:
            raise ValueError("zero offset is not allowed for relative time. Use 'now' instead.")
        if offset_minutes > 300:
            raise ValueError(
                f"relative time offset must not exceed 5 hours, "
                f"got {hours}h{minutes}m. Use an explicit datetime instead."
            )
        resolved = now - timedelta(minutes=offset_minutes)
        return TimePoint(
            date_str=resolved.strftime("%Y-%m-%d"),
            time_str=resolved.strftime("%H:%M"),
        )

    return TimePoint(date_str=s, time_str=None)


def _validate_content(s: str) -> str:
    trimmed = s.strip()
    if not trimmed:
        raise argparse.ArgumentTypeError("content cannot be empty")
    if "\n" in trimmed:
        raise argparse.ArgumentTypeError("content must be single line")
    return trimmed


def _get_storage() -> DiaryStorage:
    base_dir = os.environ.get("DIARY_DIR", os.path.expanduser("~/.diary"))
    return DiaryStorage(base_dir)


def _fail(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


# ------------------------------------------------------------------
# add event
# ------------------------------------------------------------------


def cmd_add_event(args):
    storage = _get_storage()
    try:
        tp = parse_timepoint(args.at)
    except ValueError as e:
        _fail(str(e))
    if tp.date_str is None:
        _fail("event requires a date")
    if tp.time_str is None:
        _fail("event requires a time")
    try:
        event = Event(time=tp.time_str, content=args.content)
        storage.add_event(tp.date_str, event)
        print(output.add_event(event, tp.date_str))
    except ValueError as e:
        _fail(str(e))


# ------------------------------------------------------------------
# add note
# ------------------------------------------------------------------


def cmd_add_note(args):
    storage = _get_storage()
    try:
        tp = parse_timepoint(args.at)
    except ValueError as e:
        _fail(str(e))
    if tp.date_str is None:
        _fail("note requires a date")
    if tp.time_str is not None:
        _fail("note must not have a time")
    try:
        note = Note(content=args.content)
        storage.add_note(tp.date_str, note)
        print(output.add_note(note, tp.date_str))
    except ValueError as e:
        _fail(str(e))


# ------------------------------------------------------------------
# modify event
# ------------------------------------------------------------------


def cmd_modify_event(args):
    storage = _get_storage()
    try:
        tp = parse_timepoint(args.at)
    except ValueError as e:
        _fail(str(e))
    if tp.date_str is None:
        _fail("modify requires a date")
    if tp.time_str is not None:
        _fail("modify requires a date only, not a time")
    if args.id < 1:
        _fail(f"invalid event id: {args.id} (must be >= 1)")

    new_date = None
    new_time = None
    if args.new_at:
        try:
            new_tp = parse_timepoint(args.new_at)
        except ValueError as e:
            _fail(str(e))
        if new_tp.date_str is None:
            _fail("new-at requires a date")
        if new_tp.time_str is None:
            _fail("new-at requires a time for event")
        new_date = new_tp.date_str
        new_time = new_tp.time_str

    try:
        result = storage.modify_event(
            tp.date_str,
            args.id - 1,
            new_date=new_date,
            new_time=new_time,
            new_content=args.new_content,
        )
        print(output.modify_event(result.old, result.new, result.old_date, result.new_date))
    except (FileNotFoundError, IndexError, ValueError) as e:
        _fail(str(e))


# ------------------------------------------------------------------
# modify note
# ------------------------------------------------------------------


def cmd_modify_note(args):
    storage = _get_storage()
    try:
        tp = parse_timepoint(args.at)
    except ValueError as e:
        _fail(str(e))
    if tp.date_str is None:
        _fail("modify requires a date")
    if tp.time_str is not None:
        _fail("modify requires a date only, not a time")
    if args.id < 1:
        _fail(f"invalid note id: {args.id} (must be >= 1)")

    new_date = None
    if args.new_at:
        try:
            new_tp = parse_timepoint(args.new_at)
        except ValueError as e:
            _fail(str(e))
        if new_tp.date_str is None:
            _fail("new-at requires a date")
        if new_tp.time_str is not None:
            _fail("new-at must not have a time for note")
        new_date = new_tp.date_str

    try:
        result = storage.modify_note(
            tp.date_str,
            args.id - 1,
            new_date=new_date,
            new_content=args.new_content,
        )
        print(output.modify_note(result.old, result.new, result.old_date, result.new_date))
    except (FileNotFoundError, IndexError, ValueError) as e:
        _fail(str(e))


# ------------------------------------------------------------------
# delete event
# ------------------------------------------------------------------


def cmd_delete_event(args):
    storage = _get_storage()
    try:
        tp = parse_timepoint(args.at)
    except ValueError as e:
        _fail(str(e))
    if tp.date_str is None:
        _fail("delete requires a date")
    if tp.time_str is not None:
        _fail("delete requires a date only, not a time")
    if args.id < 1:
        _fail(f"invalid event id: {args.id} (must be >= 1)")
    try:
        deleted = storage.delete_event(tp.date_str, args.id - 1)
        print(output.delete_event(deleted, tp.date_str))
    except (FileNotFoundError, IndexError) as e:
        _fail(str(e))


# ------------------------------------------------------------------
# delete note
# ------------------------------------------------------------------


def cmd_delete_note(args):
    storage = _get_storage()
    try:
        tp = parse_timepoint(args.at)
    except ValueError as e:
        _fail(str(e))
    if tp.date_str is None:
        _fail("delete requires a date")
    if tp.time_str is not None:
        _fail("delete requires a date only, not a time")
    if args.id < 1:
        _fail(f"invalid note id: {args.id} (must be >= 1)")
    try:
        deleted = storage.delete_note(tp.date_str, args.id - 1)
        print(output.delete_note(deleted, tp.date_str))
    except (FileNotFoundError, IndexError) as e:
        _fail(str(e))


# ------------------------------------------------------------------
# show
# ------------------------------------------------------------------


def cmd_show(args):
    storage = _get_storage()
    try:
        tp = parse_timepoint(args.at)
    except ValueError as e:
        _fail(str(e))
    if tp.date_str is None:
        _fail("show requires a date")
    if tp.time_str is not None:
        _fail("show requires a date only, not a time")
    try:
        if args.raw:
            print(storage.read_raw(tp.date_str), end="")
        else:
            events, notes = storage.read(tp.date_str)
            print(output.show(tp.date_str, events, notes), end="")
    except FileNotFoundError as e:
        _fail(str(e))


# ------------------------------------------------------------------
# list
# ------------------------------------------------------------------


def cmd_list(args):
    storage = _get_storage()
    dates = storage.list_dates()
    out = output.list_dates(dates)
    if out:
        print(out, end="")


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------


def main(argv: list[str] | None = None):
    """Entry point. argv overrides sys.argv[1:] for testing."""
    # Force UTF-8 output so that special characters (e.g. bullet •)
    # work regardless of the system's default encoding.
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="diary-recorder",
        description="A CLI diary tool for managing daily markdown journals.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ---- add ----
    p_add = sub.add_parser("add", help="Add an event or note")
    add_sub = p_add.add_subparsers(dest="add_type", required=True)

    p_add_event = add_sub.add_parser("event", help="Add a new event")
    p_add_event.add_argument(
        "--at",
        type=str,
        required=True,
        help="TimePoint (date+time): YYYY-MM-DDTHH:MM, todayTHH:MM, now, -15min",
    )
    p_add_event.add_argument(
        "--content", type=_validate_content, required=True, help="Event content (single line)"
    )
    p_add_event.set_defaults(func=cmd_add_event)

    p_add_note = add_sub.add_parser("note", help="Add a new note")
    p_add_note.add_argument(
        "--at", type=str, required=True, help="TimePoint (date only): YYYY-MM-DD, today"
    )
    p_add_note.add_argument(
        "--content", type=_validate_content, required=True, help="Note content (single line)"
    )
    p_add_note.set_defaults(func=cmd_add_note)

    # ---- modify ----
    p_mod = sub.add_parser("modify", help="Modify an existing event or note")
    mod_sub = p_mod.add_subparsers(dest="modify_type", required=True)

    p_mod_event = mod_sub.add_parser("event", help="Modify an existing event")
    p_mod_event.add_argument(
        "--at", type=str, required=True, help="TimePoint (date only): YYYY-MM-DD, today"
    )
    p_mod_event.add_argument(
        "--id", type=int, required=True, metavar="N", help="Event number (1-based, see show output)"
    )
    p_mod_event.add_argument(
        "--new-at",
        type=str,
        default=None,
        help="New TimePoint (date+time): YYYY-MM-DDTHH:MM, todayTHH:MM, now, -15min",
    )
    p_mod_event.add_argument(
        "--new-content", type=_validate_content, default=None, help="New content"
    )
    p_mod_event.set_defaults(func=cmd_modify_event)

    p_mod_note = mod_sub.add_parser("note", help="Modify an existing note")
    p_mod_note.add_argument(
        "--at", type=str, required=True, help="TimePoint (date only): YYYY-MM-DD, today"
    )
    p_mod_note.add_argument(
        "--id", type=int, required=True, metavar="N", help="Note number (1-based, see show output)"
    )
    p_mod_note.add_argument(
        "--new-at", type=str, default=None, help="New TimePoint (date only): YYYY-MM-DD, today"
    )
    p_mod_note.add_argument(
        "--new-content", type=_validate_content, default=None, help="New content"
    )
    p_mod_note.set_defaults(func=cmd_modify_note)

    # ---- delete ----
    p_del = sub.add_parser("delete", help="Delete an event or note")
    del_sub = p_del.add_subparsers(dest="delete_type", required=True)

    p_del_event = del_sub.add_parser("event", help="Delete an event")
    p_del_event.add_argument(
        "--at", type=str, required=True, help="TimePoint (date only): YYYY-MM-DD, today"
    )
    p_del_event.add_argument(
        "--id", type=int, required=True, metavar="N", help="Event number (1-based, see show output)"
    )
    p_del_event.set_defaults(func=cmd_delete_event)

    p_del_note = del_sub.add_parser("note", help="Delete a note")
    p_del_note.add_argument(
        "--at", type=str, required=True, help="TimePoint (date only): YYYY-MM-DD, today"
    )
    p_del_note.add_argument(
        "--id", type=int, required=True, metavar="N", help="Note number (1-based, see show output)"
    )
    p_del_note.set_defaults(func=cmd_delete_note)

    # ---- show ----
    p_show = sub.add_parser("show", help="Show diary for a date")
    p_show.add_argument(
        "--at", type=str, required=True, help="TimePoint (date only): YYYY-MM-DD, today"
    )
    p_show.add_argument(
        "--raw", action="store_true", default=False, help="Output raw markdown file content as-is"
    )
    p_show.set_defaults(func=cmd_show)

    # ---- list ----
    p_list = sub.add_parser("list", help="List all diary dates")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
