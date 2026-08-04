---
name: use-diary-recorder
description: >
  Use diary-recorder CLI for diary (日记) operations: recording events (事件),
  adding notes (笔记), modifying/deleting entries, viewing a date, listing dates.
---

# Use Diary Recorder

## Domain Terms

- **Event** — a time-bound occurrence. Always has `HH:MM` time and single-line content.
- **Note** — a freeform thought with no time attached. Ordered by insertion order.
- **TimePoint** — a unified point-in-time parameter used across commands. Has an optional
  date part (`YYYY-MM-DD` or `today`) and an optional time part (`HH:MM`, `now`, or a
  negative relative offset like `-15min`).

## TimePoint Syntax

All commands accept a unified `--at` (and `--new-at` for `modify`) that follows
one of these forms:

### Date + time (full datetime)

```bash
--at 2026-08-03T14:00       # explicit date and time
--at todayT09:30            # today at 09:30
```

- No spaces around `T`: `2026-08-03T14:00` ✅ , `2026-08-03 T 14:00` ❌
- `now` cannot replace `HH:MM` after `T`: `todayTnow` ❌ — just use `now`

### Date only

```bash
--at 2026-08-03             # specific date
--at today                  # today's date
```

### Time only (not supported)

Time-only values like `14:00` are **not valid**. Use `todayT14:00` instead.

### Relative offset

```bash
--at -15min                 # 15 minutes ago
--at -5m                    # 5 minutes ago
--at -2h                    # 2 hours ago
--at -1h30m                 # 1 hour 30 minutes ago
--at -1h30min               # same as above
```

- Offset must be > 0 and ≤ 5 hours. For larger offsets use an explicit datetime.
- Zero offset (`-0min`) is not allowed; use `now` instead.

### Now

```bash
--at now                    # current date and time
```

**Required parts by command:**

```
add event     --at: date + time
add note      --at: date only
modify event  --at: date only    --new-at: date + time
modify note   --at: date only    --new-at: date only
delete event  --at: date only
delete note   --at: date only
show          --at: date only
```

## Conventions

### Default to event

When the user asks to record something, default to `add event`.
Only use `add note` when the user explicitly says **笔记**, **note**, or **n**.
Similarly, user may explicitly say **事件**, **event**, or **e** for an event, but
this is optional — event is the default.

### Ask when uncertain

If it is unclear whether the user wants an event or a note, **ask the user**.
Do not guess.

If the user describes an event but gives a vague time ("上午", "下午", "傍晚"),
**ask for a precise time**. Do not infer.

### Show before modify or delete

The `modify` and `delete` commands require `--id N` (1-based). These ids come
from the numbered output of `show`. Always run `show --at <date>` first to get the
current id, then run `modify`/`delete`.

A typical modify flow after an `add`:

1. `add event --at now --content "..."` — user is unhappy with the result
2. `show --at <date>` — get the numbered listing to find the event's `--id`
3. `modify event --at <date> --id N --new-content "..."` — apply the change

### Output format

After running a diary-recorder command, always present the CLI output first
wrapped in a code block, then add your own commentary below:

<your_output>
```text
CLI output.
```
Your commentary.
</your_output>

## Scenarios

### Add an event

```bash
# Just happened (default)
diary-recorder add event --at now --content "<single-line>"

# Happened at a precise time
diary-recorder add event --at HH:MM --content "<single-line>"
diary-recorder add event --at YYYY-MM-DDTHH:MM --content "<single-line>"

# Happened N minutes ago (max 5 hours)
diary-recorder add event --at -15min --content "<single-line>"
diary-recorder add event --at -1h30m --content "<single-line>"
```

- If the user does not specify a time, default to `--at now`.
- If the user gives a precise time (12点, 两点半, 15分钟前, 一个半小时前),
  convert to the appropriate `--at` value.
- If the user gives only a vague time period, ask for clarification.

### Add a note

```bash
diary-recorder add note --at today --content "<single-line>"
diary-recorder add note --at YYYY-MM-DD --content "<single-line>"
```

- Only when the user explicitly says 笔记 / note / n.
- Notes have no time; `--at` takes a date only.

### Show a diary entry

```bash
diary-recorder show --at YYYY-MM-DD
diary-recorder show --at today
```

- If the user asks about a relative day (昨天, 上周三, next Monday), use
  shell `date` to compute the actual `YYYY-MM-DD`, then call `show`.
- Output is numbered; use these numbers as `--id` for `modify`/`delete`.

### List all diary dates

```bash
diary-recorder list
```

- Use when the user wants to browse which dates have diary entries.
- Output shows `YYYY-MM-DD  Weekday  event_count, note_count` per line.

### Modify an event

```bash
diary-recorder show --at YYYY-MM-DD                      # get the --id first
diary-recorder modify event --at YYYY-MM-DD --id N --new-content "<single-line>"
diary-recorder modify event --at YYYY-MM-DD --id N --new-at YYYY-MM-DDTHH:MM
diary-recorder modify event --at YYYY-MM-DD --id N --new-content "..." --new-at HH:MM
```

- `show` first — see [Show before modify or delete](#show-before-modify-or-delete).
- `--at` takes a date only (no time).
- At least one of `--new-content` or `--new-at` is required.
- `--new-at` for an event must include both date and time.

### Modify a note

```bash
diary-recorder show --at YYYY-MM-DD                      # get the --id first
diary-recorder modify note --at YYYY-MM-DD --id N --new-content "<single-line>"
diary-recorder modify note --at YYYY-MM-DD --id N --new-at YYYY-MM-DD
```

- `show` first — see [Show before modify or delete](#show-before-modify-or-delete).
- `--at` takes a date only.
- At least one of `--new-content` or `--new-at` is required.
- `--new-at` for a note must be a date only (no time).

### Delete an event

```bash
diary-recorder show --at YYYY-MM-DD                      # get the --id first
diary-recorder delete event --at YYYY-MM-DD --id N
```

- `show` first — see [Show before modify or delete](#show-before-modify-or-delete).
- `--at` takes a date only.

### Delete a note

```bash
diary-recorder show --at YYYY-MM-DD                      # get the --id first
diary-recorder delete note --at YYYY-MM-DD --id N
```

- `show` first — see [Show before modify or delete](#show-before-modify-or-delete).
- `--at` takes a date only.
