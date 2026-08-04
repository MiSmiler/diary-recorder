from diary_recorder.models import DateSummary, Event, Note
from diary_recorder.output import (
    add_event,
    add_note,
    delete_event,
    delete_note,
    list_dates,
    modify_event,
    modify_note,
    show,
)


class TestShow:
    def test_empty_both_sections(self):
        result = show("2026-08-03", [], [])
        assert result == ("# 2026-08-03\n\n## Events\n\n## Notes\n")

    def test_events_only_no_notes(self):
        events = [Event(time="08:30", content="wake up")]
        result = show("2026-08-03", events, [])
        assert result == ("# 2026-08-03\n\n## Events\n\n1. `08:30` wake up\n\n## Notes\n")

    def test_notes_only_no_events(self):
        notes = [Note(content="today's thought")]
        result = show("2026-08-03", [], notes)
        assert result == ("# 2026-08-03\n\n## Events\n\n## Notes\n\n1. today's thought\n")

    def test_both_sections(self):
        events = [
            Event(time="08:30", content="wake up"),
            Event(time="09:00", content="meeting"),
        ]
        notes = [
            Note(content="first thought"),
            Note(content="second thought"),
        ]
        result = show("2026-08-03", events, notes)
        assert result == (
            "# 2026-08-03\n\n"
            "## Events\n\n"
            "1. `08:30` wake up\n"
            "2. `09:00` meeting\n\n"
            "## Notes\n\n"
            "1. first thought\n"
            "2. second thought\n"
        )


class TestListDates:
    def test_multiple_dates(self):
        dates = [
            DateSummary("2026-08-03", "Mon", 3, 1),
            DateSummary("2026-08-02", "Sun", 1, 2),
            DateSummary("2026-07-28", "Tue", 5, 0),
        ]
        result = list_dates(dates)
        assert result == (
            "2026-08-03  Mon  3 events, 1 note\n"
            "2026-08-02  Sun  1 event, 2 notes\n"
            "2026-07-28  Tue  5 events, 0 notes\n"
        )

    def test_singular_plural(self):
        dates = [
            DateSummary("2026-08-03", "Mon", 1, 1),
            DateSummary("2026-08-02", "Sun", 0, 0),
        ]
        result = list_dates(dates)
        lines = result.strip().split("\n")
        assert "1 event, 1 note" in lines[0]
        assert "0 events, 0 notes" in lines[1]

    def test_empty_returns_empty_string(self):
        result = list_dates([])
        assert result == ""


class TestAddEvent:
    def test_basic(self):
        event = Event(time="14:30", content="go shopping")
        result = add_event(event, "2026-08-03")
        assert result == ("Added event for 2026-08-03:\n• `14:30` go shopping")


class TestModifyEvent:
    def test_both_changed(self):
        old = Event(time="09:00", content="meeting")
        new = Event(time="10:00", content="team meeting")
        result = modify_event(old, new, "2026-08-03")
        assert result == (
            "Modified event for 2026-08-03:\n- `09:00` meeting\n+ `10:00` team meeting"
        )

    def test_time_only(self):
        old = Event(time="09:00", content="meeting")
        new = Event(time="10:00", content="meeting")
        result = modify_event(old, new, "2026-08-03")
        assert result == ("Modified event for 2026-08-03:\n- `09:00` meeting\n+ `10:00` meeting")

    def test_content_only(self):
        old = Event(time="09:00", content="meeting")
        new = Event(time="09:00", content="team meeting")
        result = modify_event(old, new, "2026-08-03")
        assert result == (
            "Modified event for 2026-08-03:\n- `09:00` meeting\n+ `09:00` team meeting"
        )


class TestDeleteEvent:
    def test_basic(self):
        event = Event(time="09:00", content="meeting")
        result = delete_event(event, "2026-08-03")
        assert result == ("Deleted event for 2026-08-03:\n• `09:00` meeting")


class TestAddNote:
    def test_basic(self):
        note = Note(content="today's thought")
        result = add_note(note, "2026-08-03")
        assert result == ("Added note for 2026-08-03:\n• today's thought")


class TestModifyNote:
    def test_basic(self):
        old = Note(content="old thought")
        new = Note(content="new thought")
        result = modify_note(old, new, "2026-08-03")
        assert result == ("Modified note for 2026-08-03:\n- old thought\n+ new thought")


class TestDeleteNote:
    def test_basic(self):
        note = Note(content="remove me")
        result = delete_note(note, "2026-08-03")
        assert result == ("Deleted note for 2026-08-03:\n• remove me")
