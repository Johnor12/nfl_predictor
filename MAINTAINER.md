# MAINTAINER

Technical map of the project. Read a directory's README.md for its API, and its MAINTAINER.md for its files.

## layout

The folders follow the architecture in README.md:

- README.md: project goals, concepts, and phases (plain text, edited by hand only).
- .claude/rules/general.md: working rules for agents.
- pyproject.toml / uv.lock: Python 3.12+ project managed with uv (pandas, pyarrow; pytest for dev).
- events/: one package per event: its output type, and under `predictors/` one package per implementation (`baseline/` for all 17 so far). Also `baseline_priors.py`, which rebuilds every baseline's priors.
- scenarios/play/: the play scenario: inputs, event chain, rules, enforcement, stats, validator, narration, and the `Predictors` bundle (`load_predictors`).
- simulators/play/: runs the play scenario over many inputs and summarizes each outcome.
- evaluators/scoring/: the evaluators' shared toolkit: fair CRPS and Brier scores, the reference to beat, sim noise, PIT histograms, reliability (`Scorecard`).
- evaluators/play/: scores the play scenario and each event predictor against real plays (`evaluate`).
- evaluators/lines/: scores betting lines against results, and a simulator's distributions on the same lines (`lines`, `score_lines`).
- evaluators/audit/: checks the play simulator against real plays (validity and reasonableness metrics) and writes a report.
- shared/rulebook/: season-versioned rule constants (`rules_for(season)`).
- shared/priors/: the toolkit behind the count-based baseline predictors (sampling, buckets, player picking, priors files, and building them).
- shared/nflverse/: downloads and caches nflverse data (`load`); turns real plays into play scenario inputs (`real_plays`, `real_samples`).
- shared/lines/: betting lines: game lines from the nflverse schedule (`game_lines`) and DraftKings player props via ESPN (`player_lines`).

Not built yet: the game scenario (`scenarios/game/`, phase 0), its simulator (`simulators/game/`), and its evaluator, which will score simulated games on the betting lines through `evaluators.lines.score_lines`.

## dependencies

They point one way: evaluators -> simulators -> scenarios -> events (output types) -> nothing, with shared/rulebook and shared/priors below everything.

- An event's `__init__.py` holds only its output type, so the play scenario can import it. The play scenario knows nothing about data or about any predictor implementation; `load_predictors` imports them by name.
- Predictor implementations (`events/<event>/predictors/<name>/`) sit above the play scenario: they import its public API (`from scenarios.play import ...`) for inputs and helpers, and `shared.priors`.
- shared/nflverse is the one part of shared/ that isn't at the bottom: it imports `scenarios.play` (it builds `PlayContext`s). shared/lines sits on top of it. Only `events/baseline_priors.py`, the evaluators, and tests import them; the play scenario never does.
- evaluators/scoring imports nothing from the rest of the project; the other evaluators score with it.

## commands

- Tests: `uv run pytest -q`. The nflverse, audit, priors-build, play evaluation, and lines tests skip unless `.cache/` has the 2026 files.
- Evaluate the play scenario and its event predictors: `uv run python -m evaluators.play --season 2026` writes `evaluation_output/play_2026.md` (about 5 minutes on 16 cores; `--weeks 1-2 --sims 20` for a quick look; `--swap carry=other` for another implementation).
- Score the betting lines: `uv run python -m evaluators.lines --season 2026` writes `evaluation_output/lines_2026.md` (downloads each game's props on first use).
- Audit: `uv run python -m evaluators.audit --season 2026` writes `audit_output/report_2026.md`.
- Rebuild the baseline priors: `uv run python -m events.baseline_priors 2026`.
- In this environment `UV_INDEX` points at an unauthenticated private registry. Run uv with it unset: `env -u UV_INDEX uv ...` in bash, or `$env:UV_INDEX=$null` first in PowerShell.

## conventions

- Every play must be reproducible from its seed: a predictor only draws from the `random.Random` it's handed, and never iterates a set (or anything else unordered) on the way to a draw.
- A refactor shouldn't change a single simulated play. Check by hashing a few thousand seeded plays (`describe_play` output and stats) and the audit's metrics before and after.
- A predictor change is measured, not eyeballed: run `evaluators.play` before and after and compare the event's rows (and the play scenario's). The baseline priors are built from 2026, so 2026 scores are in-sample; `--season 2025` is the out-of-sample check.
- Every evaluator scores with `evaluators.scoring` (fair CRPS for numbers, fair Brier for yes/no and categories), so scores mean the same thing at every level.

## generated files (gitignored)

- .cache/nflverse/: downloaded nflverse files.
- .cache/lines/: downloaded player prop lines, one file per played game.
- evaluation_output/: play evaluation and betting lines reports.
- audit_output/: audit reports.
