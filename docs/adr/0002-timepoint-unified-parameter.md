# Adopt TimePoint as unified temporal parameter

The CLI previously used separate `--date` and `--time`/`--new-time` parameters
across subcommands.  To support relative time expressions (`-15min`, `-1h20m`)
and keep the CLI surface consistent, we unified them into a single `--at` /
`--new-at` parameter that accepts a **TimePoint** — an optional date part and
optional time part joined by `T` (e.g. `todayT14:00`, `-15min`, `now`,
`2026-08-03`).  The alternative of bolting relative-time parsing onto the
existing two-parameter design would have produced confusing interactions
(e.g. relative time spanning midnight changing the implicit date) and
inconsistent parameter names across subcommands.

**Considered Options**

- **Add relative-time parsing to existing `--time`/`--new-time`**: simpler code
  change, but leaves `--date` and `--time` as separate concerns.  Cross-midnight
  relative times (`-15min` at 00:10) would produce a time that belongs to a
  different day than `--date`, requiring either silent date adjustment (breaking
  the separation) or an error (surprising the user).  Either outcome is awkward
  in a two-parameter model.

- **TimePoint unification**: treats date and time as two parts of one concept.
  Relative times resolve to a complete date+time at parse time.  Every
  subcommand uses the same `--at` parameter, constrained per subcommand (Event
  requires date+time; Note requires date only).  The trade-off is a breaking CLI
  change and more upfront work.

**Consequences**

- All `--date` and `--time`/`--new-time` parameters are replaced by `--at` /
  `--new-at` across `add`, `modify`, `delete`, and `show` subcommands.
- `--at` has no default value; users must always specify it explicitly.
- `modify` now supports cross-date moves (e.g. move an Event from
  `2026-08-03.md` to `2026-08-04.md`).
- Relative time offsets are capped at 5 hours.  Zero offsets are rejected.
