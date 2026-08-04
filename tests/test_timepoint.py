"""Tests for TimePoint parsing."""

from datetime import datetime

import pytest

from diary_recorder.cli import parse_timepoint
from diary_recorder.models import TimePoint

FIXED_NOW = datetime(2026, 8, 3, 14, 30)


def test_parse_full_datetime():
    tp = parse_timepoint("2026-08-03T12:30")
    assert tp == TimePoint(date_str="2026-08-03", time_str="12:30")


def test_parse_date_only():
    tp = parse_timepoint("2026-08-03")
    assert tp == TimePoint(date_str="2026-08-03", time_str=None)


def test_parse_today():
    tp = parse_timepoint("today", now=FIXED_NOW)
    assert tp == TimePoint(date_str="2026-08-03", time_str=None)


def test_parse_today_with_time():
    tp = parse_timepoint("todayT14:00", now=FIXED_NOW)
    assert tp == TimePoint(date_str="2026-08-03", time_str="14:00")


def test_parse_now():
    tp = parse_timepoint("now", now=FIXED_NOW)
    assert tp == TimePoint(date_str="2026-08-03", time_str="14:30")


def test_parse_relative_minutes():
    tp = parse_timepoint("-15min", now=FIXED_NOW)
    assert tp == TimePoint(date_str="2026-08-03", time_str="14:15")


def test_parse_relative_hours_and_minutes():
    tp = parse_timepoint("-1h20m", now=FIXED_NOW)
    assert tp == TimePoint(date_str="2026-08-03", time_str="13:10")


def test_parse_relative_hours_only():
    tp = parse_timepoint("-5h", now=FIXED_NOW)
    assert tp == TimePoint(date_str="2026-08-03", time_str="09:30")


def test_parse_relative_minutes_short():
    tp = parse_timepoint("-15m", now=FIXED_NOW)
    assert tp == TimePoint(date_str="2026-08-03", time_str="14:15")


def test_parse_relative_cross_midnight():
    now_midnight = datetime(2026, 8, 4, 0, 10)
    tp = parse_timepoint("-15min", now=now_midnight)
    assert tp == TimePoint(date_str="2026-08-03", time_str="23:55")


# --- Error cases ---


def test_reject_zero_offset_hours():
    with pytest.raises(ValueError, match="zero offset"):
        parse_timepoint("-0h")


def test_reject_zero_offset_minutes():
    with pytest.raises(ValueError, match="zero offset"):
        parse_timepoint("-0m")


def test_reject_zero_offset_combined():
    with pytest.raises(ValueError, match="zero offset"):
        parse_timepoint("-0h0m")


def test_reject_offset_exceeds_5h():
    with pytest.raises(ValueError, match="must not exceed 5 hours"):
        parse_timepoint("-6h")


def test_reject_offset_exceeds_5h_combined():
    with pytest.raises(ValueError, match="must not exceed 5 hours"):
        parse_timepoint("-5h1m")


def test_reject_todayt_now():
    with pytest.raises(ValueError, match="'now' cannot be combined"):
        parse_timepoint("todayTnow")


def test_reject_datet_now():
    with pytest.raises(ValueError, match="'now' cannot be combined"):
        parse_timepoint("2026-08-03Tnow")


def test_reject_spaces_around_t():
    with pytest.raises(ValueError, match="no spaces allowed around 'T'"):
        parse_timepoint("today T 14:00")


def test_reject_bare_dash():
    with pytest.raises(ValueError, match="invalid relative time"):
        parse_timepoint("-")


def test_reject_invalid_relative_format():
    with pytest.raises(ValueError, match="invalid relative time"):
        parse_timepoint("-abc")
