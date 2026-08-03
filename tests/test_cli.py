"""Integration tests for the CLI entry point."""

import os
import pytest
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


class TestAdd:
    def test_adds_event_and_confirms(self, tmp_path):
        diary_dir = str(tmp_path)
        out, err, code = _run("add", "--date", "2026-08-03",
                              "--time", "08:30", "--content", "wake up",
                              diary_dir=diary_dir)
        assert code == 0
        assert "Added event for 2026-08-03" in out
        assert "`08:30` wake up" in out

        # verify file was written
        md = tmp_path / "2026-08-03.md"
        assert md.read_text(encoding="utf-8") == (
            "# 2026-08-03\n\n## Events\n\n- `08:30` wake up\n"
        )

    def test_defaults_to_today(self, tmp_path, monkeypatch):
        import datetime
        today = "2026-08-03"
        monkeypatch.setattr("diary_recorder.cli._today_str", lambda: today)
        monkeypatch.setattr("diary_recorder.cli._now_time_str", lambda: "14:30")

        out, err, code = _run("add", "--content", "test event",
                              diary_dir=str(tmp_path))
        assert code == 0
        md = tmp_path / f"{today}.md"
        assert md.exists()

    def test_rejects_empty_content(self, tmp_path):
        out, err, code = _run("add", "--content", "   ",
                              diary_dir=str(tmp_path))
        assert code != 0

    def test_rejects_multiline_content(self, tmp_path):
        out, err, code = _run("add", "--content", "line1\nline2",
                              diary_dir=str(tmp_path))
        assert code != 0


class TestModify:
    def test_modifies_time(self, tmp_path):
        diary_dir = str(tmp_path)
        _run("add", "--date", "2026-08-03", "--time", "08:30",
             "--content", "wake up", diary_dir=diary_dir)
        _run("add", "--date", "2026-08-03", "--time", "09:00",
             "--content", "meeting", diary_dir=diary_dir)

        out, err, code = _run("modify", "--date", "2026-08-03", "--id", "1",
                              "--new-time", "10:00", diary_dir=diary_dir)
        assert code == 0
        assert "Modified event for 2026-08-03" in out
        assert "- `09:00` meeting" in out
        assert "+ `10:00` meeting" in out

    def test_modify_requires_at_least_one_change(self, tmp_path):
        diary_dir = str(tmp_path)
        _run("add", "--date", "2026-08-03", "--time", "09:00",
             "--content", "meeting", diary_dir=diary_dir)

        out, err, code = _run("modify", "--date", "2026-08-03", "--id", "0",
                              diary_dir=diary_dir)
        assert code != 0

    def test_id_out_of_range(self, tmp_path):
        diary_dir = str(tmp_path)
        _run("add", "--date", "2026-08-03", "--time", "09:00",
             "--content", "meeting", diary_dir=diary_dir)

        out, err, code = _run("modify", "--date", "2026-08-03", "--id", "5",
                              "--new-content", "x", diary_dir=diary_dir)
        assert code != 0


class TestDelete:
    def test_deletes_event(self, tmp_path):
        diary_dir = str(tmp_path)
        _run("add", "--date", "2026-08-03", "--time", "08:30",
             "--content", "wake up", diary_dir=diary_dir)
        _run("add", "--date", "2026-08-03", "--time", "09:00",
             "--content", "meeting", diary_dir=diary_dir)

        out, err, code = _run("delete", "--date", "2026-08-03", "--id", "0",
                              diary_dir=diary_dir)
        assert code == 0
        assert "Deleted event for 2026-08-03" in out
        assert "`08:30` wake up" in out

    def test_id_out_of_range(self, tmp_path):
        diary_dir = str(tmp_path)
        _run("add", "--date", "2026-08-03", "--time", "09:00",
             "--content", "meeting", diary_dir=diary_dir)

        out, err, code = _run("delete", "--date", "2026-08-03", "--id", "5",
                              diary_dir=diary_dir)
        assert code != 0


class TestShow:
    def test_shows_diary(self, tmp_path):
        diary_dir = str(tmp_path)
        _run("add", "--date", "2026-08-03", "--time", "08:30",
             "--content", "wake up", diary_dir=diary_dir)
        _run("add", "--date", "2026-08-03", "--time", "09:00",
             "--content", "meeting", diary_dir=diary_dir)

        out, err, code = _run("show", "--date", "2026-08-03",
                              diary_dir=diary_dir)
        assert code == 0
        assert "1. `08:30` wake up" in out
        assert "2. `09:00` meeting" in out

    def test_file_not_exists(self, tmp_path):
        out, err, code = _run("show", "--date", "2026-08-03",
                              diary_dir=str(tmp_path))
        assert code != 0

    def test_defaults_to_today(self, tmp_path, monkeypatch):
        import datetime
        monkeypatch.setattr("diary_recorder.cli._today_str", lambda: "2026-08-03")
        diary_dir = str(tmp_path)
        _run("add", "--content", "test", diary_dir=diary_dir)
        out, err, code = _run("show", diary_dir=diary_dir)
        assert code == 0
        assert "`" in out


class TestList:
    def test_lists_dates(self, tmp_path):
        diary_dir = str(tmp_path)
        _run("add", "--date", "2026-08-01", "--time", "08:00", "--content", "x",
             diary_dir=diary_dir)
        _run("add", "--date", "2026-08-03", "--time", "08:00", "--content", "a",
             diary_dir=diary_dir)
        _run("add", "--date", "2026-08-03", "--time", "09:00", "--content", "b",
             diary_dir=diary_dir)

        out, err, code = _run("list", diary_dir=diary_dir)
        assert code == 0
        lines = out.strip().split("\n")
        assert len(lines) == 2
        assert lines[0].startswith("2026-08-03")
        assert "2 events" in lines[0]
        assert lines[1].startswith("2026-08-01")
        assert "1 event" in lines[1]

    def test_empty_dir(self, tmp_path):
        out, err, code = _run("list", diary_dir=str(tmp_path))
        assert code == 0
        assert out.strip() == ""
