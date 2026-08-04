# diary-recorder

A CLI tool for managing daily markdown journals. Each day is a file containing
timestamped events and freeform notes.

## Install

Requires Python ≥ 3.10.

```bash
uv tool install .
```

## Quickstart

```bash
# Add a timed event to today's diary
diary-recorder add event --at todayT14:30 --content "Team standup"

# Add an event with a relative time (15 minutes ago)
# Note: relative offsets must use = form (--at=-15min), not space (--at -15min)
diary-recorder add event --at=-15min --content "Bug discovered in auth flow"

# Add a freeform note
diary-recorder add note --at today --content "Interesting idea about project structure"

# Show today's diary
diary-recorder show --at today

# Show the raw markdown file
diary-recorder show --at today --raw

# List all diary dates
diary-recorder list
```

## Example Diary

After adding a few entries, your day might look like this:

```
$ diary-recorder show --at 2026-08-03
# 2026-08-03

## Events

1. `09:00` Team standup
2. `10:30` Pair programming with Alice on auth module
3. `14:00` Sprint planning

## Notes

1. Interesting idea about project structure — revisit tomorrow
2. Need to look into uv's build backend options
```

Under the hood, each day is a plain markdown file at `~/.diary/2026-08-03.md`.
Use `--raw` to see it exactly as stored:

```
$ diary-recorder show --at 2026-08-03 --raw
# 2026-08-03

## Events

- `09:00` Team standup
- `10:30` Pair programming with Alice on auth module
- `14:00` Sprint planning

## Notes

- Interesting idea about project structure — revisit tomorrow
- Need to look into uv's build backend options
```

## Command Overview

Every command supports `--help` — use it to discover available subcommands and
options:

```bash
diary-recorder --help
diary-recorder add --help
diary-recorder modify --help
```

Available commands:

| Command    | Description                      |
| ---------- | -------------------------------- |
| `add`      | Add an event or note             |
| `modify`   | Modify an existing event or note |
| `delete`   | Delete an event or note          |
| `show`     | Show a date's diary              |
| `list`     | List all diary dates             |

### TimePoint format

The `--at` and `--new-at` options accept a unified TimePoint format:

| Form               | Meaning                       |
| ------------------ | ----------------------------- |
| `2026-08-03T14:30` | Specific date and time        |
| `todayT14:30`      | Today at 14:30                |
| `2026-08-03`       | Date only (for notes / show)  |
| `today`            | Today (date only)             |
| `now`              | Current date and time         |
| `-15min`           | 15 minutes ago                |
| `-1h20m`           | 1 hour 20 minutes ago         |

> **Note**: Relative offsets (e.g. `-15min`) start with `-`, which argparse
> misinterprets as an option flag. Use `=` form: `--at=-15min`, not `--at -15min`.

## Configuration

| Variable     | Default      | Description                 |
| ------------ | ------------ | --------------------------- |
| `DIARY_DIR`  | `~/.diary`   | Directory for diary files   |

Diary files are stored as `YYYY-MM-DD.md` under `DIARY_DIR`.
