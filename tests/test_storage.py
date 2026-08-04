import pytest

from diary_recorder.models import DateSummary, Event, Note
from diary_recorder.storage import DiaryStorage

# ---------------------------------------------------------------------------
# Helper to write a minimal valid diary file for tests that need one
# ---------------------------------------------------------------------------

_VALID_FILE = "# 2026-08-03\n\n## Events\n\n## Notes\n"


def _write_file(path, content):
    path.write_text(content, encoding="utf-8")


class TestRead:
    def test_file_not_exists_raises(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        with pytest.raises(FileNotFoundError):
            storage.read("2026-08-03")

    def test_empty_sections_returns_empty_lists(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        _write_file(tmp_path / "2026-08-03.md", _VALID_FILE)
        events, notes = storage.read("2026-08-03")
        assert events == []
        assert notes == []

    def test_parses_events_correctly(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        _write_file(
            tmp_path / "2026-08-03.md",
            "# 2026-08-03\n\n## Events\n\n"
            "- `08:30` wake up\n"
            "- `09:00` meeting\n"
            "- `18:00` go home\n"
            "\n## Notes\n",
        )
        events, notes = storage.read("2026-08-03")
        assert events == [
            Event(time="08:30", content="wake up"),
            Event(time="09:00", content="meeting"),
            Event(time="18:00", content="go home"),
        ]
        assert notes == []

    def test_parses_notes_correctly(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        _write_file(
            tmp_path / "2026-08-03.md",
            "# 2026-08-03\n\n## Events\n\n\n## Notes\n\n- first thought\n- second thought\n",
        )
        events, notes = storage.read("2026-08-03")
        assert events == []
        assert notes == [Note(content="first thought"), Note(content="second thought")]

    def test_parses_both_sections_mixed(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        _write_file(
            tmp_path / "2026-08-03.md",
            "# 2026-08-03\n\n## Events\n\n"
            "- `08:30` wake up\n"
            "- `09:00` meeting\n"
            "\n## Notes\n\n"
            "- today's thought\n"
            "- remember milk\n",
        )
        events, notes = storage.read("2026-08-03")
        assert events == [
            Event(time="08:30", content="wake up"),
            Event(time="09:00", content="meeting"),
        ]
        assert notes == [Note(content="today's thought"), Note(content="remember milk")]

    def test_missing_notes_section_raises(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        _write_file(
            tmp_path / "2026-08-03.md",
            "# 2026-08-03\n\n## Events\n\n- `08:30` wake up\n",
        )
        with pytest.raises(ValueError, match="missing ## Notes section"):
            storage.read("2026-08-03")

    def test_missing_events_section_raises(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        _write_file(
            tmp_path / "2026-08-03.md",
            "# 2026-08-03\n\n## Notes\n\n- a note\n",
        )
        with pytest.raises(ValueError, match="missing ## Events section"):
            storage.read("2026-08-03")


class TestAddEvent:
    def test_creates_file_with_both_sections(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="08:30", content="wake up"))
        date_file = tmp_path / "2026-08-03.md"
        assert date_file.exists()
        content = date_file.read_text(encoding="utf-8")
        assert content == ("# 2026-08-03\n\n## Events\n\n- `08:30` wake up\n\n## Notes\n")

    def test_inserts_in_time_order(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="18:00", content="go home"))
        storage.add_event("2026-08-03", Event(time="08:30", content="wake up"))
        storage.add_event("2026-08-03", Event(time="09:00", content="meeting"))
        events, _ = storage.read("2026-08-03")
        assert [e.time for e in events] == ["08:30", "09:00", "18:00"]

    def test_same_time_appends_after_existing(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="08:30", content="first"))
        storage.add_event("2026-08-03", Event(time="08:30", content="second"))
        events, _ = storage.read("2026-08-03")
        assert events == [
            Event(time="08:30", content="first"),
            Event(time="08:30", content="second"),
        ]

    def test_preserves_existing_notes(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_note("2026-08-03", Note(content="a note"))
        storage.add_event("2026-08-03", Event(time="08:30", content="wake up"))
        _, notes = storage.read("2026-08-03")
        assert notes == [Note(content="a note")]


class TestModifyEvent:
    def test_changes_time_and_resorts(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="08:30", content="wake up"))
        storage.add_event("2026-08-03", Event(time="09:00", content="meeting"))
        storage.add_event("2026-08-03", Event(time="18:00", content="go home"))

        old, new = storage.modify_event(
            "2026-08-03",
            1,
            new_time="20:00",  # modify meeting
        )
        assert old == Event(time="09:00", content="meeting")
        assert new == Event(time="20:00", content="meeting")
        events, _ = storage.read("2026-08-03")
        assert [e.time for e in events] == ["08:30", "18:00", "20:00"]

    def test_changes_content_only(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="09:00", content="meeting"))

        old, new = storage.modify_event("2026-08-03", 0, new_content="team meeting")
        assert old == Event(time="09:00", content="meeting")
        assert new == Event(time="09:00", content="team meeting")
        events, _ = storage.read("2026-08-03")
        assert events == [Event(time="09:00", content="team meeting")]

    def test_index_out_of_range_raises(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="09:00", content="meeting"))
        with pytest.raises(IndexError):
            storage.modify_event("2026-08-03", 5, new_content="x")

    def test_no_changes_specified_raises(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="09:00", content="meeting"))
        with pytest.raises(ValueError, match="at least one of"):
            storage.modify_event("2026-08-03", 0)


class TestDeleteEvent:
    def test_deletes_and_returns_event(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="08:30", content="wake up"))
        storage.add_event("2026-08-03", Event(time="09:00", content="meeting"))

        deleted = storage.delete_event("2026-08-03", 0)
        assert deleted == Event(time="08:30", content="wake up")
        events, _ = storage.read("2026-08-03")
        assert events == [Event(time="09:00", content="meeting")]

    def test_index_out_of_range_raises(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="09:00", content="meeting"))
        with pytest.raises(IndexError):
            storage.delete_event("2026-08-03", 5)


class TestAddNote:
    def test_appends_note(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_note("2026-08-03", Note(content="first"))
        storage.add_note("2026-08-03", Note(content="second"))
        _, notes = storage.read("2026-08-03")
        assert notes == [Note(content="first"), Note(content="second")]

    def test_creates_file_if_not_exists(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_note("2026-08-03", Note(content="a note"))
        date_file = tmp_path / "2026-08-03.md"
        assert date_file.exists()
        content = date_file.read_text(encoding="utf-8")
        assert content == ("# 2026-08-03\n\n## Events\n\n## Notes\n\n- a note\n")

    def test_preserves_existing_events(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="08:30", content="wake up"))
        storage.add_note("2026-08-03", Note(content="a note"))
        events, notes = storage.read("2026-08-03")
        assert events == [Event(time="08:30", content="wake up")]
        assert notes == [Note(content="a note")]


class TestModifyNote:
    def test_changes_content(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_note("2026-08-03", Note(content="original"))

        old, new = storage.modify_note("2026-08-03", 0, new_content="updated")
        assert old == Note(content="original")
        assert new == Note(content="updated")
        _, notes = storage.read("2026-08-03")
        assert notes == [Note(content="updated")]

    def test_index_out_of_range_raises(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_note("2026-08-03", Note(content="only"))
        with pytest.raises(IndexError):
            storage.modify_note("2026-08-03", 5, new_content="x")

    def test_keeps_position_after_modify(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_note("2026-08-03", Note(content="first"))
        storage.add_note("2026-08-03", Note(content="second"))
        storage.add_note("2026-08-03", Note(content="third"))

        storage.modify_note("2026-08-03", 1, new_content="CHANGED")
        _, notes = storage.read("2026-08-03")
        assert notes == [
            Note(content="first"),
            Note(content="CHANGED"),
            Note(content="third"),
        ]


class TestDeleteNote:
    def test_deletes_and_returns_note(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_note("2026-08-03", Note(content="first"))
        storage.add_note("2026-08-03", Note(content="second"))

        deleted = storage.delete_note("2026-08-03", 0)
        assert deleted == Note(content="first")
        _, notes = storage.read("2026-08-03")
        assert notes == [Note(content="second")]

    def test_index_out_of_range_raises(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_note("2026-08-03", Note(content="only"))
        with pytest.raises(IndexError):
            storage.delete_note("2026-08-03", 5)


class TestListDates:
    def test_returns_dates_reverse_chronological(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        _write_file(
            tmp_path / "2026-08-01.md",
            "# 2026-08-01\n\n## Events\n\n- `08:00` x\n\n## Notes\n",
        )
        _write_file(
            tmp_path / "2026-08-03.md",
            "# 2026-08-03\n\n## Events\n\n- `08:00` a\n- `09:00` b\n\n## Notes\n\n- n1\n",
        )
        _write_file(
            tmp_path / "2026-08-02.md",
            "# 2026-08-02\n\n## Events\n\n## Notes\n",
        )

        dates = storage.list_dates()
        assert len(dates) == 3
        assert dates[0] == DateSummary("2026-08-03", "Mon", 2, 1)
        assert dates[1] == DateSummary("2026-08-02", "Sun", 0, 0)
        assert dates[2] == DateSummary("2026-08-01", "Sat", 1, 0)

    def test_ignores_non_date_files(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        _write_file(tmp_path / "2026-08-03.md", _VALID_FILE)
        _write_file(tmp_path / "notes.md", "some notes\n")
        _write_file(tmp_path / ".gitkeep", "")

        dates = storage.list_dates()
        assert len(dates) == 1
        assert dates[0].date_str == "2026-08-03"

    def test_empty_dir_returns_empty(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        assert storage.list_dates() == []
