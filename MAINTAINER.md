# MAINTAINER

Technical map of the project. Read a directory's README.md for its API, and its MAINTAINER.md for its files.

## layout

- README.md: project goals, concepts, and phases (plain text, edited by hand only).
- .claude/rules/general.md: working rules for agents.
- pyproject.toml / uv.lock: Python 3.12+ project managed with uv (pandas, pyarrow; pytest for dev).
- rulebook/: season-versioned rule constants (`rules_for(season)`).
- scenarios/play/: the play scenario: inputs, event chain, rules, enforcement, stats, validator, narration.
- predictors/baseline/: baseline predictors for every play event (priors from 2026 plays plus hand-set rules).
- nflverse/: downloads and caches nflverse data; turns real plays into play scenario inputs (`real_plays`).
- audit/: runs every real input through the play scenario, validates the results, and compares them with reality.

Dependencies point one way: audit -> predictors, nflverse -> scenarios -> rulebook. The play scenario knows nothing about data or predictors beyond the `Predictors` interface.

## commands

- Tests: `uv run pytest -q`. The nflverse and audit tests skip unless `.cache/nflverse/` has the 2026 files.
- Audit: `uv run python -m audit --season 2026` writes `audit_output/report_2026.md`.
- Rebuild priors: `uv run python -m predictors.baseline.priors 2026`.
- In this environment `UV_INDEX` points at an unauthenticated private registry. Run uv with it unset: `env -u UV_INDEX uv ...` in bash, or `$env:UV_INDEX=$null` first in PowerShell.

## generated files (gitignored)

- .cache/nflverse/: downloaded nflverse files.
- audit_output/: audit reports.
