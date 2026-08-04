## Project tooling

- **Package manager**: `uv` — use `uv add`, `uv run`, `uv sync`, etc. When adding or removing dependencies, use `uv add` / `uv remove` rather than editing `pyproject.toml` by hand.
- **Linter / formatter**: `ruff` — config in `pyproject.toml` (`[tool.ruff]`). After completing a batch of Python edits, run `uv run ruff check --fix . && uv run ruff format .` to auto-fix lint issues, then format.
- **Test runner**: `pytest` — after lint + format pass, run `uv run pytest -q` to confirm nothing is broken.

## Agent skills

### Issue tracker

Issues are tracked as GitHub issues via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Uses the five canonical triage labels with default names (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
