import pytest
from diary_recorder.storage import DiaryStorage
from diary_recorder.models import Event


class TestReadEvents:
    def test_file_not_exists_raises(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        with pytest.raises(FileNotFoundError):
            storage.read_events("2026-08-03")

    def test_empty_file_returns_empty_list(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        date_file = tmp_path / "2026-08-03.md"
        date_file.write_text("# 2026-08-03\n\n## Events\n\n", encoding="utf-8")
        assert storage.read_events("2026-08-03") == []

    def test_parses_events_correctly(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        date_file = tmp_path / "2026-08-03.md"
        date_file.write_text(
            "# 2026-08-03\n\n## Events\n\n"
            "- `08:30` wake up\n"
            "- `09:00` meeting\n"
            "- `18:00` go home\n",
            encoding="utf-8",
        )
        events = storage.read_events("2026-08-03")
        assert events == [
            Event(time="08:30", content="wake up"),
            Event(time="09:00", content="meeting"),
            Event(time="18:00", content="go home"),
        ]


class TestAddEvent:
    def test_creates_file_if_not_exists(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="08:30", content="wake up"))
        date_file = tmp_path / "2026-08-03.md"
        assert date_file.exists()
        content = date_file.read_text(encoding="utf-8")
        assert "# 2026-08-03" in content
        assert "## Events" in content
        assert "`08:30` wake up" in content

    def test_inserts_in_time_order(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="18:00", content="go home"))
        storage.add_event("2026-08-03", Event(time="08:30", content="wake up"))
        storage.add_event("2026-08-03", Event(time="09:00", content="meeting"))
        events = storage.read_events("2026-08-03")
        assert [e.time for e in events] == ["08:30", "09:00", "18:00"]

    def test_same_time_appends_after_existing(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="08:30", content="first"))
        storage.add_event("2026-08-03", Event(time="08:30", content="second"))
        events = storage.read_events("2026-08-03")
        assert events == [
            Event(time="08:30", content="first"),
            Event(time="08:30", content="second"),
        ]


class TestModifyEvent:
    def test_changes_time_and_resorts(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="08:30", content="wake up"))
        storage.add_event("2026-08-03", Event(time="09:00", content="meeting"))
        storage.add_event("2026-08-03", Event(time="18:00", content="go home"))

        old, new = storage.modify_event(
            "2026-08-03", 1, new_time="20:00"  # modify meeting
        )
        assert old == Event(time="09:00", content="meeting")
        assert new == Event(time="20:00", content="meeting")
        events = storage.read_events("2026-08-03")
        assert [e.time for e in events] == ["08:30", "18:00", "20:00"]

    def test_changes_content_only(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="09:00", content="meeting"))

        old, new = storage.modify_event(
            "2026-08-03", 0, new_content="team meeting"
        )
        assert old == Event(time="09:00", content="meeting")
        assert new == Event(time="09:00", content="team meeting")
        events = storage.read_events("2026-08-03")
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
        events = storage.read_events("2026-08-03")
        assert events == [Event(time="09:00", content="meeting")]

    def test_index_out_of_range_raises(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        storage.add_event("2026-08-03", Event(time="09:00", content="meeting"))
        with pytest.raises(IndexError):
            storage.delete_event("2026-08-03", 5)


class TestListDates:
    def test_returns_dates_reverse_chronological(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        (tmp_path / "2026-08-01.md").write_text(
            "# 2026-08-01\n\n## Events\n\n- `08:00` x\n", encoding="utf-8"
        )
        (tmp_path / "2026-08-03.md").write_text(
            "# 2026-08-03\n\n## Events\n\n- `08:00` a\n- `09:00` b\n", encoding="utf-8"
        )
        (tmp_path / "2026-08-02.md").write_text(
            "# 2026-08-02\n\n## Events\n\n", encoding="utf-8"
        )

        dates = storage.list_dates()
        assert len(dates) == 3
        assert dates[0][0] == "2026-08-03"  # newest first
        assert dates[0][2] == 2              # event count
        assert dates[1][0] == "2026-08-02"
        assert dates[1][2] == 0
        assert dates[2][0] == "2026-08-01"
        assert dates[2][2] == 1

    def test_ignores_non_date_files(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        (tmp_path / "2026-08-03.md").write_text(
            "# 2026-08-03\n\n## Events\n\n", encoding="utf-8"
        )
        (tmp_path / "notes.md").write_text("some notes\n", encoding="utf-8")
        (tmp_path / ".gitkeep").write_text("", encoding="utf-8")

        dates = storage.list_dates()
        assert len(dates) == 1
        assert dates[0][0] == "2026-08-03"

    def test_empty_dir_returns_empty(self, tmp_path):
        storage = DiaryStorage(str(tmp_path))
        assert storage.list_dates() == []
