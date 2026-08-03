"""CLI entry point using argparse."""

import argparse
import os
import re
import sys
from datetime import datetime, date

from diary_recorder.models import Event
from diary_recorder.storage import DiaryStorage
from diary_recorder import output

_TIME_RE = re.compile(r"^\d{2}:\d{2}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _today_str() -> str:
    return date.today().isoformat()


def _now_time_str() -> str:
    return datetime.now().strftime("%H:%M")


def _validate_date(s: str) -> str:
    if not _DATE_RE.match(s):
        raise argparse.ArgumentTypeError(
            f"invalid date '{s}': expected YYYY-MM-DD"
        )
    try:
        date.fromisoformat(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date '{s}'")
    return s


def _validate_time(s: str) -> str:
    if s == "now":
        return s
    if not _TIME_RE.match(s):
        raise argparse.ArgumentTypeError(
            f"invalid time '{s}': expected HH:MM"
        )
    hh, mm = int(s[:2]), int(s[3:])
    if hh > 23 or mm > 59:
        raise argparse.ArgumentTypeError(f"invalid time '{s}'")
    return s


def _resolve_time(time_str: str, date_str: str) -> str:
    """Resolve 'now' keyword to current system time.

    Only allowed when date_str is today.  Plain HH:MM strings pass through.
    """
    if time_str != "now":
        return time_str
    if date_str != _today_str():
        _fail(f"'now' is only valid when date is today ({_today_str()})")
    return _now_time_str()


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


def cmd_add(args):
    storage = _get_storage()
    date_str = args.date or _today_str()
    time_str = _resolve_time(args.time, date_str)
    try:
        event = Event(time=time_str, content=args.content)
        storage.add_event(date_str, event)
        print(output.add(event, date_str))
    except ValueError as e:
        _fail(str(e))


def cmd_modify(args):
    storage = _get_storage()
    date_str = args.date or _today_str()
    if args.id < 1:
        _fail(f"invalid event id: {args.id} (must be >= 1)")
    try:
        new_time_resolved = _resolve_time(args.new_time, date_str) if args.new_time else None
        old, new = storage.modify_event(
            date_str,
            args.id - 1,
            new_time=new_time_resolved,
            new_content=args.new_content,
        )
        print(output.modify(old, new, date_str))
    except (FileNotFoundError, IndexError, ValueError) as e:
        _fail(str(e))


def cmd_delete(args):
    storage = _get_storage()
    date_str = args.date or _today_str()
    if args.id < 1:
        _fail(f"invalid event id: {args.id} (must be >= 1)")
    try:
        deleted = storage.delete_event(date_str, args.id - 1)
        print(output.delete(deleted, date_str))
    except (FileNotFoundError, IndexError) as e:
        _fail(str(e))


def cmd_show(args):
    storage = _get_storage()
    date_str = args.date or _today_str()
    try:
        events = storage.read_events(date_str)
        print(output.show(date_str, events), end="")
    except FileNotFoundError as e:
        _fail(str(e))


def cmd_list(args):
    storage = _get_storage()
    dates = storage.list_dates()
    out = output.list_dates(dates)
    if out:
        print(out, end="")


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
    p_add = sub.add_parser("add", help="Add a new event")
    p_add.add_argument("--date", type=_validate_date, default=None,
                       help="Date (YYYY-MM-DD), default: today")
    p_add.add_argument("--time", type=_validate_time, required=True,
                       help="Time (HH:MM) or 'now' for current time")
    p_add.add_argument("--content", type=_validate_content, required=True,
                       help="Event content (single line)")
    p_add.set_defaults(func=cmd_add)

    # ---- modify ----
    p_mod = sub.add_parser("modify", help="Modify an existing event")
    p_mod.add_argument("--date", type=_validate_date, default=None,
                       help="Date (YYYY-MM-DD), default: today")
    p_mod.add_argument("--id", type=int, required=True, metavar="N",
                       help="Event number (1-based, see show output)")
    p_mod.add_argument("--new-time", type=_validate_time, default=None,
                       help="New time (HH:MM)")
    p_mod.add_argument("--new-content", type=_validate_content, default=None,
                       help="New content")
    p_mod.set_defaults(func=cmd_modify)

    # ---- delete ----
    p_del = sub.add_parser("delete", help="Delete an event")
    p_del.add_argument("--date", type=_validate_date, default=None,
                       help="Date (YYYY-MM-DD), default: today")
    p_del.add_argument("--id", type=int, required=True, metavar="N",
                       help="Event number (1-based, see show output)")
    p_del.set_defaults(func=cmd_delete)

    # ---- show ----
    p_show = sub.add_parser("show", help="Show diary for a date")
    p_show.add_argument("--date", type=_validate_date, default=None,
                        help="Date (YYYY-MM-DD), default: today")
    p_show.set_defaults(func=cmd_show)

    # ---- list ----
    p_list = sub.add_parser("list", help="List all diary dates")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
