"""Integration tests for the CLI entry point."""

import os

from diary_recorder.cli import main


def _run(*args, diary_dir):
    """Run main() with args and a custom DIARY_DIR, return (stdout, stderr, exit_code)."""
    import io
    import sys

    old_dir = os.environ.get("DIARY_DIR")
    os.environ["DIARY_DIR"] = diary_dir

    stdout = io.StringIO()
    stderr = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout, stderr

    exit_code = 0
    try:
        main(list(args))
    except SystemExit as e:
        exit_code = e.code if isinstance(e.code, int) else 1

    sys.stdout, sys.stderr = old_out, old_err
    if old_dir is not None:
        os.environ["DIARY_DIR"] = old_dir
    else:
        del os.environ["DIARY_DIR"]

    return stdout.getvalue(), stderr.getvalue(), exit_code


class TestAddEvent:
    def test_adds_event_and_confirms(self, tmp_path):
        diary_dir = str(tmp_path)
        out, err, code = _run(
            "add",
            "event",
            "--at",
            "2026-08-03T08:30",
            "--content",
            "wake up",
            diary_dir=diary_dir,
        )
        assert code == 0
        assert out == "Added event for 2026-08-03:\n• `08:30` wake up\n"

        md = tmp_path / "2026-08-03.md"
        assert md.read_text(encoding="utf-8") == (
            "# 2026-08-03\n\n## Events\n\n- `08:30` wake up\n\n## Notes\n"
        )

    def test_adds_event_with_today(self, tmp_path, monkeypatch):
        from datetime import datetime as dt

        fake_dt = dt(2026, 8, 3, 14, 30)

        class FakeDateTime(dt):
            @classmethod
            def now(cls, tz=None):
                return fake_dt

        monkeypatch.setattr("diary_recorder.cli.datetime", FakeDateTime)

        out, err, code = _run(
            "add",
            "event",
            "--at",
            "todayT14:30",
            "--content",
            "test event",
            diary_dir=str(tmp_path),
        )
        assert code == 0
        md = tmp_path / "2026-08-03.md"
        assert md.exists()

    def test_adds_event_with_now(self, tmp_path, monkeypatch):
        from datetime import datetime as dt

        fake_dt = dt(2026, 8, 3, 14, 30)

        class FakeDateTime(dt):
            @classmethod
            def now(cls, tz=None):
                return fake_dt

        monkeypatch.setattr("diary_recorder.cli.datetime", FakeDateTime)

        out, err, code = _run(
            "add", "event", "--at", "now", "--content", "test event", diary_dir=str(tmp_path)
        )
        assert code == 0
        md = tmp_path / "2026-08-03.md"
        content = md.read_text(encoding="utf-8")
        assert "`14:30` test event" in content

    def test_rejects_date_only_for_event(self, tmp_path):
        out, err, code = _run(
            "add", "event", "--at", "today", "--content", "test", diary_dir=str(tmp_path)
        )
        assert code != 0
        assert "event requires a time" in err

    def test_rejects_empty_content(self, tmp_path):
        out, err, code = _run(
            "add", "event", "--at", "todayT12:00", "--content", "   ", diary_dir=str(tmp_path)
        )
        assert code != 0
        assert "content cannot be empty" in err

    def test_rejects_multiline_content(self, tmp_path):
        out, err, code = _run(
            "add",
            "event",
            "--at",
            "todayT12:00",
            "--content",
            "line1\nline2",
            diary_dir=str(tmp_path),
        )
        assert code != 0
        assert "content must be single line" in err


class TestAddNote:
    def test_adds_note_and_confirms(self, tmp_path):
        diary_dir = str(tmp_path)
        out, err, code = _run(
            "add",
            "note",
            "--at",
            "2026-08-03",
            "--content",
            "today's thought",
            diary_dir=diary_dir,
        )
        assert code == 0
        assert out == "Added note for 2026-08-03:\n• today's thought\n"

        md = tmp_path / "2026-08-03.md"
        assert md.read_text(encoding="utf-8") == (
            "# 2026-08-03\n\n## Events\n\n## Notes\n\n- today's thought\n"
        )

    def test_adds_note_with_today(self, tmp_path, monkeypatch):
        from datetime import datetime as dt

        fake_dt = dt(2026, 8, 3, 14, 30)

        class FakeDateTime(dt):
            @classmethod
            def now(cls, tz=None):
                return fake_dt

        monkeypatch.setattr("diary_recorder.cli.datetime", FakeDateTime)

        out, err, code = _run(
            "add", "note", "--at", "today", "--content", "a note", diary_dir=str(tmp_path)
        )
        assert code == 0
        md = tmp_path / "2026-08-03.md"
        assert md.exists()

    def test_rejects_time_for_note(self, tmp_path):
        out, err, code = _run(
            "add", "note", "--at", "todayT14:00", "--content", "test", diary_dir=str(tmp_path)
        )
        assert code != 0
        assert "note must not have a time" in err

    def test_rejects_now_for_note(self, tmp_path):
        out, err, code = _run(
            "add", "note", "--at", "now", "--content", "test", diary_dir=str(tmp_path)
        )
        assert code != 0
        assert "note must not have a time" in err

    def test_rejects_empty_content(self, tmp_path):
        out, err, code = _run(
            "add", "note", "--at", "today", "--content", "   ", diary_dir=str(tmp_path)
        )
        assert code != 0
        assert "content cannot be empty" in err

    def test_rejects_multiline_content(self, tmp_path):
        out, err, code = _run(
            "add", "note", "--at", "today", "--content", "line1\nline2", diary_dir=str(tmp_path)
        )
        assert code != 0
        assert "content must be single line" in err


class TestModifyEvent:
    def test_modifies_time(self, tmp_path):
        diary_dir = str(tmp_path)
        _run(
            "add",
            "event",
            "--at",
            "2026-08-03T08:30",
            "--content",
            "wake up",
            diary_dir=diary_dir,
        )
        _run(
            "add",
            "event",
            "--at",
            "2026-08-03T09:00",
            "--content",
            "meeting",
            diary_dir=diary_dir,
        )

        out, err, code = _run(
            "modify",
            "event",
            "--at",
            "2026-08-03",
            "--id",
            "2",
            "--new-at",
            "2026-08-03T10:00",
            diary_dir=diary_dir,
        )
        assert code == 0
        assert out == ("Modified event for 2026-08-03:\n- `09:00` meeting\n+ `10:00` meeting\n")

    def test_modify_requires_at_least_one_change(self, tmp_path):
        diary_dir = str(tmp_path)
        _run(
            "add",
            "event",
            "--at",
            "2026-08-03T09:00",
            "--content",
            "meeting",
            diary_dir=diary_dir,
        )

        out, err, code = _run(
            "modify", "event", "--at", "2026-08-03", "--id", "1", diary_dir=diary_dir
        )
        assert code != 0
        assert err == "Error: at least one of new_date, new_time, or new_content is required\n"

    def test_id_out_of_range(self, tmp_path):
        diary_dir = str(tmp_path)
        _run(
            "add",
            "event",
            "--at",
            "2026-08-03T09:00",
            "--content",
            "meeting",
            diary_dir=diary_dir,
        )

        out, err, code = _run(
            "modify",
            "event",
            "--at",
            "2026-08-03",
            "--id",
            "5",
            "--new-content",
            "x",
            diary_dir=diary_dir,
        )
        assert code != 0
        assert err == "Error: event #5 not found for 2026-08-03 (has 1 event)\n"

    def test_rejects_time_for_at(self, tmp_path):
        out, err, code = _run(
            "modify",
            "event",
            "--at",
            "2026-08-03T12:00",
            "--id",
            "1",
            "--new-content",
            "x",
            diary_dir=str(tmp_path),
        )
        assert code != 0
        assert "modify requires a date only, not a time" in err

    def test_rejects_date_only_for_new_at(self, tmp_path):
        out, err, code = _run(
            "modify",
            "event",
            "--at",
            "2026-08-03",
            "--id",
            "1",
            "--new-at",
            "2026-08-03",
            diary_dir=str(tmp_path),
        )
        assert code != 0
        assert "new-at requires a time for event" in err


class TestModifyNote:
    def test_modifies_content(self, tmp_path):
        diary_dir = str(tmp_path)
        _run("add", "note", "--at", "2026-08-03", "--content", "original", diary_dir=diary_dir)

        out, err, code = _run(
            "modify",
            "note",
            "--at",
            "2026-08-03",
            "--id",
            "1",
            "--new-content",
            "updated",
            diary_dir=diary_dir,
        )
        assert code == 0
        assert out == ("Modified note for 2026-08-03:\n- original\n+ updated\n")

    def test_id_out_of_range(self, tmp_path):
        diary_dir = str(tmp_path)
        _run("add", "note", "--at", "2026-08-03", "--content", "only", diary_dir=diary_dir)

        out, err, code = _run(
            "modify",
            "note",
            "--at",
            "2026-08-03",
            "--id",
            "5",
            "--new-content",
            "x",
            diary_dir=diary_dir,
        )
        assert code != 0
        assert err == "Error: note #5 not found for 2026-08-03 (has 1 note)\n"

    def test_rejects_time_for_at(self, tmp_path):
        out, err, code = _run(
            "modify",
            "note",
            "--at",
            "2026-08-03T12:00",
            "--id",
            "1",
            "--new-content",
            "x",
            diary_dir=str(tmp_path),
        )
        assert code != 0
        assert "modify requires a date only, not a time" in err

    def test_rejects_time_for_new_at(self, tmp_path):
        out, err, code = _run(
            "modify",
            "note",
            "--at",
            "2026-08-03",
            "--id",
            "1",
            "--new-at",
            "2026-08-03T12:00",
            diary_dir=str(tmp_path),
        )
        assert code != 0
        assert "new-at must not have a time for note" in err


class TestDeleteEvent:
    def test_deletes_event(self, tmp_path):
        diary_dir = str(tmp_path)
        _run(
            "add",
            "event",
            "--at",
            "2026-08-03T08:30",
            "--content",
            "wake up",
            diary_dir=diary_dir,
        )
        _run(
            "add",
            "event",
            "--at",
            "2026-08-03T09:00",
            "--content",
            "meeting",
            diary_dir=diary_dir,
        )

        out, err, code = _run(
            "delete", "event", "--at", "2026-08-03", "--id", "1", diary_dir=diary_dir
        )
        assert code == 0
        assert out == "Deleted event for 2026-08-03:\n• `08:30` wake up\n"

    def test_id_out_of_range(self, tmp_path):
        diary_dir = str(tmp_path)
        _run(
            "add",
            "event",
            "--at",
            "2026-08-03T09:00",
            "--content",
            "meeting",
            diary_dir=diary_dir,
        )

        out, err, code = _run(
            "delete", "event", "--at", "2026-08-03", "--id", "5", diary_dir=diary_dir
        )
        assert code != 0
        assert err == "Error: event #5 not found for 2026-08-03 (has 1 event)\n"

    def test_rejects_time(self, tmp_path):
        out, err, code = _run(
            "delete",
            "event",
            "--at",
            "2026-08-03T12:00",
            "--id",
            "1",
            diary_dir=str(tmp_path),
        )
        assert code != 0
        assert "delete requires a date only, not a time" in err


class TestDeleteNote:
    def test_deletes_note(self, tmp_path):
        diary_dir = str(tmp_path)
        _run("add", "note", "--at", "2026-08-03", "--content", "first", diary_dir=diary_dir)
        _run("add", "note", "--at", "2026-08-03", "--content", "second", diary_dir=diary_dir)

        out, err, code = _run(
            "delete", "note", "--at", "2026-08-03", "--id", "1", diary_dir=diary_dir
        )
        assert code == 0
        assert out == "Deleted note for 2026-08-03:\n• first\n"

    def test_id_out_of_range(self, tmp_path):
        diary_dir = str(tmp_path)
        _run("add", "note", "--at", "2026-08-03", "--content", "only", diary_dir=diary_dir)

        out, err, code = _run(
            "delete", "note", "--at", "2026-08-03", "--id", "5", diary_dir=diary_dir
        )
        assert code != 0
        assert err == "Error: note #5 not found for 2026-08-03 (has 1 note)\n"

    def test_rejects_time(self, tmp_path):
        out, err, code = _run(
            "delete",
            "note",
            "--at",
            "2026-08-03T12:00",
            "--id",
            "1",
            diary_dir=str(tmp_path),
        )
        assert code != 0
        assert "delete requires a date only, not a time" in err


class TestShow:
    def test_shows_full_diary(self, tmp_path):
        diary_dir = str(tmp_path)
        _run(
            "add",
            "event",
            "--at",
            "2026-08-03T08:30",
            "--content",
            "wake up",
            diary_dir=diary_dir,
        )
        _run(
            "add",
            "event",
            "--at",
            "2026-08-03T09:00",
            "--content",
            "meeting",
            diary_dir=diary_dir,
        )
        _run("add", "note", "--at", "2026-08-03", "--content", "a thought", diary_dir=diary_dir)

        out, err, code = _run("show", "--at", "2026-08-03", diary_dir=diary_dir)
        assert code == 0
        assert out == (
            "# 2026-08-03\n\n"
            "## Events\n\n"
            "1. `08:30` wake up\n"
            "2. `09:00` meeting\n\n"
            "## Notes\n\n"
            "1. a thought\n"
        )

    def test_file_not_exists(self, tmp_path):
        out, err, code = _run("show", "--at", "2026-08-03", diary_dir=str(tmp_path))
        assert code != 0
        assert err == "Error: no diary entry for 2026-08-03\n"

    def test_shows_today_diary(self, tmp_path, monkeypatch):
        from datetime import datetime as dt

        fake_dt = dt(2026, 8, 3, 14, 30)

        class FakeDateTime(dt):
            @classmethod
            def now(cls, tz=None):
                return fake_dt

        monkeypatch.setattr("diary_recorder.cli.datetime", FakeDateTime)
        diary_dir = str(tmp_path)
        _run("add", "event", "--at", "todayT14:30", "--content", "test", diary_dir=diary_dir)
        out, err, code = _run("show", "--at", "today", diary_dir=diary_dir)
        assert code == 0
        assert "test" in out

    def test_rejects_time(self, tmp_path):
        out, err, code = _run(
            "show",
            "--at",
            "2026-08-03T12:00",
            diary_dir=str(tmp_path),
        )
        assert code != 0
        assert "show requires a date only, not a time" in err


class TestList:
    def test_lists_dates(self, tmp_path):
        diary_dir = str(tmp_path)
        _run(
            "add",
            "event",
            "--at",
            "2026-08-01T08:00",
            "--content",
            "x",
            diary_dir=diary_dir,
        )
        _run(
            "add",
            "event",
            "--at",
            "2026-08-03T08:00",
            "--content",
            "a",
            diary_dir=diary_dir,
        )
        _run("add", "note", "--at", "2026-08-03", "--content", "n1", diary_dir=diary_dir)

        out, err, code = _run("list", diary_dir=diary_dir)
        assert code == 0
        lines = out.strip().split("\n")
        assert len(lines) == 2
        assert lines[0].startswith("2026-08-03")
        assert "1 event, 1 note" in lines[0]
        assert lines[1].startswith("2026-08-01")
        assert "1 event, 0 notes" in lines[1]

    def test_empty_dir(self, tmp_path):
        out, err, code = _run("list", diary_dir=str(tmp_path))
        assert code == 0
        assert out.strip() == ""
