# Diary Recorder

A CLI tool for managing daily markdown journals. Each day is a file containing
timestamped events and freeform notes.

## Language

**Event**:
A time-bound occurrence on a specific day. Always carries a `HH:MM` time and a
single-line content description.
_Avoid_: entry, appointment, schedule item

**Note**:
A freeform thought, idea, or observation attached to a day. Has no time — Notes
are ordered by insertion (append-only).
_Avoid_: memo, comment, annotation

**Date Summary**:
A lightweight aggregate for the `list` command: a date, its weekday, and separate
counts of its Events and Notes.

**TimePoint**:
A point in time with an optional date part (`YYYY-MM-DD` or `today`) and an
optional time part (`HH:MM`, `now`, or a negative relative offset like `-15min`).
Used as the unified parameter (`--at`, `--new-at`) across all subcommands.
_Avoid_: timestamp, datetime
