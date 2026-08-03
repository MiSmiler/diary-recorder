# Events: unordered list on disk, ordered list on screen

Diary events are stored in markdown files as unordered list items (`-`) but displayed in
the CLI `show` command as ordered list items (`1. 2. 3.`). This deliberate asymmetry
serves two different consumers: git diffs (file) and the human operator who needs
to pick an event number for `modify --id` / `delete --id` (screen).

## Considered Options

### A. Ordered list in both file and CLI

Every event line starts with `1.`. On insert to the middle, every subsequent line's
number changes — producing noisy git diffs that obscure the actual content change.
Since `time` already encodes sort order, the numbers are redundant in the file.

### B. Unordered list in both file and CLI

Clean diffs, but the user has no quick way to identify "the third event" when they need
to pass `--id 3` to `modify` or `delete`. They would have to count manually or rely
on time strings, which is error-prone.

### C. Unordered on disk, ordered on screen *(chosen)*

- **File**: `- `HH:MM` content` — inserting a new event only adds one line in diffs.
  The `time` field already conveys sequence; an ordered list prefix adds no information.
- **CLI `show`**: `1. `HH:MM` content` — the numbers let the user immediately
  identify the target event for `modify --id N` or `delete --id N`. The typical
  workflow is `show` → see the number → `modify --id <that>`.

## Consequences

- A future `show --raw` flag may output the original unordered format for reading
  comfort (no distracting numbers when just browsing).
- Additional sections (e.g. `## Notes`) will follow the same pattern: unordered
  bullets on disk, numbered lines in `show` output.
- Event IDs are ephemeral positional indices, not persisted. This is acceptable
  because the user is expected to `show` immediately before any `modify`/`delete`.
