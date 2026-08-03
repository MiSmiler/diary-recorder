import pytest
from diary_recorder.formatter import (
    format_show,
    format_list,
    format_add,
    format_modify,
    format_delete,
)
from diary_recorder.models import Event


class TestFormatShow:
    def test_empty_events_shows_template(self):
        result = format_show("2026-08-03", [])
        assert result == "# 2026-08-03\n\n## Events\n"

    def test_single_event(self):
        events = [Event(time="08:30", content="wake up")]
        result = format_show("2026-08-03", events)
        assert result == (
            "# 2026-08-03\n\n"
            "## Events\n\n"
            "1. `08:30` wake up\n"
        )

    def test_multiple_events_numbered(self):
        events = [
            Event(time="08:30", content="wake up"),
            Event(time="09:00", content="meeting"),
            Event(time="18:00", content="go home"),
        ]
        result = format_show("2026-08-03", events)
        assert result == (
            "# 2026-08-03\n\n"
            "## Events\n\n"
            "1. `08:30` wake up\n"
            "2. `09:00` meeting\n"
            "3. `18:00` go home\n"
        )


class TestFormatList:
    def test_multiple_dates(self):
        dates = [
            ("2026-08-03", "Mon", 3),
            ("2026-08-02", "Sun", 1),
            ("2026-07-28", "Tue", 5),
        ]
        result = format_list(dates)
        assert result == (
            "2026-08-03  Mon  3 events\n"
            "2026-08-02  Sun  1 event\n"
            "2026-07-28  Tue  5 events\n"
        )

    def test_singular_event(self):
        dates = [("2026-08-03", "Mon", 1)]
        result = format_list(dates)
        assert "1 event" in result
        assert "1 events" not in result

    def test_zero_events(self):
        dates = [("2026-08-03", "Mon", 0)]
        result = format_list(dates)
        assert "0 events" in result

    def test_empty_returns_empty_string(self):
        result = format_list([])
        assert result == ""


class TestFormatAdd:
    def test_basic(self):
        event = Event(time="14:30", content="go shopping")
        result = format_add(event, "2026-08-03")
        assert result == (
            "Added event for 2026-08-03:\n"
            "\u2022 `14:30` go shopping"
        )


class TestFormatModify:
    def test_both_changed(self):
        old = Event(time="09:00", content="meeting")
        new = Event(time="10:00", content="team meeting")
        result = format_modify(old, new, "2026-08-03")
        assert result == (
            "Modified event for 2026-08-03:\n"
            "- `09:00` meeting\n"
            "+ `10:00` team meeting"
        )

    def test_time_only(self):
        old = Event(time="09:00", content="meeting")
        new = Event(time="10:00", content="meeting")
        result = format_modify(old, new, "2026-08-03")
        assert result == (
            "Modified event for 2026-08-03:\n"
            "- `09:00` meeting\n"
            "+ `10:00` meeting"
        )

    def test_content_only(self):
        old = Event(time="09:00", content="meeting")
        new = Event(time="09:00", content="team meeting")
        result = format_modify(old, new, "2026-08-03")
        assert result == (
            "Modified event for 2026-08-03:\n"
            "- `09:00` meeting\n"
            "+ `09:00` team meeting"
        )


class TestFormatDelete:
    def test_basic(self):
        event = Event(time="09:00", content="meeting")
        result = format_delete(event, "2026-08-03")
        assert result == (
            "Deleted event for 2026-08-03:\n"
            "\u2022 `09:00` meeting"
        )
